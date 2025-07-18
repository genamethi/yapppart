import csv
import os
import numpy as np
from dataclasses import dataclass
from typing import Dict, Set, Tuple, Optional
from sage.rings.integer import Integer

@dataclass
class PPPartConfig:
    """Central configuration for all pppart paths and settings."""
    data_dir: str
    output_dir: str
    backup_dir: str
    temp_dir: str
    default_data_file: str = "partition_data.csv"
    default_batch_size: int = 250
    
    @property
    def default_data_path(self) -> str:
        return os.path.join(self.data_dir, self.default_data_file)
    
    @property
    def default_output_path(self) -> str:
        return os.path.join(self.output_dir, self.default_data_file)

def get_config() -> PPPartConfig:
    """Get configuration following env vars -> pyproject.toml -> setup.py -> importlib.resources -> fallback hierarchy."""
    
    # 1. Try environment variables (highest priority for overrides)
    if data_dir := os.getenv('PPPART_DATA_DIR'):
        return PPPartConfig(
            data_dir=data_dir,
            output_dir=os.getenv('PPPART_OUTPUT_DIR', 'src/pppart/data/tmp'),
            backup_dir=os.getenv('PPPART_BACKUP_DIR', 'src/pppart/data/backups'),
            temp_dir=os.getenv('PPPART_TEMP_DIR', 'src/pppart/data/tmp')
        )
    
    # 2. Try pyproject.toml (source of truth)
    try:
        import tomllib
        from importlib.resources import files
        try:
            # Try package resources first (for installed package)
            project_root = files(__name__.split('.')[0])
            pyproject_path = project_root.parent / "pyproject.toml"
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            
            # Extract directory configuration
            dirs = data.get("tool", {}).get("pppart", {}).get("directories", {})
            return PPPartConfig(
                data_dir=dirs.get("data_dir", "src/pppart/data"),
                output_dir=dirs.get("output_dir", "src/pppart/data/tmp"),
                backup_dir=dirs.get("backup_dir", "src/pppart/data/backups"),
                temp_dir=dirs.get("temp_dir", "src/pppart/data/tmp")
            )
        except (FileNotFoundError, AttributeError):
            # Fallback to relative path (for development)
            pyproject_path = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
            if os.path.exists(pyproject_path):
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                
                dirs = data.get("tool", {}).get("pppart", {}).get("directories", {})
                return PPPartConfig(
                    data_dir=dirs.get("data_dir", "src/pppart/data"),
                    output_dir=dirs.get("output_dir", "src/pppart/data/tmp"),
                    backup_dir=dirs.get("backup_dir", "src/pppart/data/backups"),
                    temp_dir=dirs.get("temp_dir", "src/pppart/data/tmp")
                )
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    # 3. Try build-time configuration (from setup.py)
    try:
        from ._build_config import BUILD_VERSION, SETUP_PY_CONFIGURED
        if SETUP_PY_CONFIGURED:
            # Use version-specific data directories for different builds
            version_suffix = BUILD_VERSION.replace('.', '_').replace('+', '_')
            base_data_dir = 'data'
            
            return PPPartConfig(
                data_dir=os.path.join(base_data_dir, f"v{version_suffix}"),
                output_dir=os.path.join(base_data_dir, 'tmp'),
                backup_dir=os.path.join(base_data_dir, 'backups'),
                temp_dir=os.path.join(base_data_dir, 'temp')
            )
    except ImportError:
        pass
    
    # 4. Try importlib.resources for package data

    try:
        from importlib.resources import files
        data_files = files('pppart.data')
        return PPPartConfig(
            data_dir=str(data_files),
            output_dir='src/pppart/data/tmp',  # Local output
            backup_dir='src/pppart/data/backups',
            temp_dir='src/pppart/data/tmp'
        )
    except (ImportError, ModuleNotFoundError):
        pass
    
    # 5. Ultimate fallback
    return PPPartConfig(
        data_dir='src/pppart/data',
        output_dir='src/pppart/data/tmp', 
        backup_dir='src/pppart/data/backups',
        temp_dir='src/pppart/data/tmp'
    )

# Type Aliases
PartitionTuple = Tuple[Integer, int, Integer, int]
PartitionDict = Dict[int, Set[PartitionTuple]]

def write_csv(master_data_dict: PartitionDict, fname: str, append_mode: bool = False):
    """Writes the results dictionary to a flat CSV file with one partition per row."""
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    
    mode = 'a' if append_mode else 'w'
    with open(fname, mode, newline='') as f:
        writer = csv.writer(f)
        # Only write header if not appending
        if not append_mode:
            writer.writerow(["n", "p", "j", "q", "k"])
        
        # Sort by n for deterministic output
        for n, partitions_set in sorted(master_data_dict.items()):
            # Sort the partitions themselves for deterministic representation
            sorted_partitions = sorted(list(partitions_set))
            
            for p, j, q, k in sorted_partitions:
                writer.writerow([n, int(p), int(j), int(q), int(k)])
            
    print(f"Output successfully saved to {fname}")

def get_last_prime(fname: str) -> Integer:
    """Read the last line of CSV and return the highest prime n value."""
    if not os.path.exists(fname):
        raise FileNotFoundError(f"Data file not found at {fname}")
    
    with open(fname, 'rb') as f:
        # Seek to end and read backwards to find last line efficiently
        f.seek(0, 2)  # Go to end
        file_size = f.tell()
        
        if file_size == 0:
            raise ValueError("Data file is empty")
            
        # Read backwards to find last non-empty line
        f.seek(-1, 2)
        
        # Skip trailing whitespace/newlines by reading backwards
        while f.tell() > 0:
            char = f.read(1)
            if char != b'\n' and char != b'\r':
                # Found non-whitespace, this is end of last data line
                break
            f.seek(-2, 1)  # Go back 2 positions (1 for the char we read, 1 more to go backwards)
        
        # Now read backwards to find the start of this line
        while f.tell() > 0:
            f.seek(-1, 1)
            char = f.read(1)
            if char == b'\n':
                break
            f.seek(-1, 1)
        
        # Read the last non-empty line
        last_line = f.readline().decode('utf-8').strip()
        
        if not last_line or last_line.startswith('n,'):  # Header or empty
            raise ValueError("No data rows found in CSV file")
        
        # Parse the first column (n value)
        try:
            n_value = Integer(last_line.split(',')[0])
            return n_value
        except (ValueError, IndexError, TypeError) as e:
            raise ValueError(f"Could not parse last line of CSV: {last_line}") from e

def print_summary(master_data_dict: PartitionDict, num_primes: int):
    """Print comprehensive summary statistics for the generated partition data.
    
    TODO: Add CLI flags for different summary options (--brief, --detailed, --counts-only)
    but for now we provide all the data at once.
    """
    # Basic summary statistics
    total_partitions = sum(len(partitions_set) for partitions_set in master_data_dict.values())
    zero_partition_count = sum(1 for partitions_set in master_data_dict.values() 
                              if len(partitions_set) == 1 and (0, 0, 0, 0) in partitions_set)
    
    print(f"\n=== Summary Statistics ===")
    print(f"Primes processed: {len(master_data_dict)}")
    print(f"Total partitions found: {total_partitions}")
    print(f"Zero-partition primes: {zero_partition_count} ({zero_partition_count/len(master_data_dict)*100:.1f}%)")
    print(f"Average partitions per prime: {total_partitions/len(master_data_dict):.2f}")
    
    # Detailed partition count distribution
    # Get the count of partitions for each prime n
    counts_per_n = []
    for partitions_set in master_data_dict.values():
        if len(partitions_set) == 1 and (0, 0, 0, 0) in partitions_set:
            # Zero partition case
            counts_per_n.append(0)
        else:
            # Regular partitions
            counts_per_n.append(len(partitions_set))
    
    # Use numpy.bincount to efficiently count frequencies of each partition count
    partition_counts = np.bincount(counts_per_n)
    
    print(f"\n=== Partition Count Distribution ===")
    print(f"Partition count distribution for {len(master_data_dict)} primes:")
    for count, freq in enumerate(partition_counts):
        if freq > 0:
            print(f"  {count} partitions: {freq} primes")
    print()

def create_backup(fname: str) -> None:
    """Create timestamped backup of existing file."""
    if not os.path.exists(fname):
        return
        
    from datetime import datetime
    import shutil
    
    config = get_config()
    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M')
    backup_name = f"{timestamp}.csv.bak"
    backup_path = os.path.join(config.backup_dir, backup_name)
    
    # Ensure backup directory exists
    os.makedirs(config.backup_dir, exist_ok=True)
    
    shutil.copy2(fname, backup_path)
    print(f"Backup created: {backup_path}")

# load_partition_data removed - use numpy-based approaches instead 

