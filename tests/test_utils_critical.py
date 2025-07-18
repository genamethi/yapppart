import pytest
import os
import csv
from sage.all import Integer

from pppart.utils import get_last_prime, create_backup, get_config, PPPartConfig


class TestGetLastPrime:
    """Comprehensive tests for get_last_prime function - critical for resume functionality."""
    
    def test_get_last_prime_basic(self, tmp_path):
        """Test basic get_last_prime functionality."""
        test_file = tmp_path / "test.csv"
        
        # Create a simple CSV file
        with open(test_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["n", "p", "j", "q", "k"])  # Header
            writer.writerow([2, 2, 1, 0, 0])
            writer.writerow([3, 3, 1, 0, 0])
            writer.writerow([5, 4, 2, 1, 0])
            writer.writerow([7, 0, 0, 0, 0])  # Last row
        
        result = get_last_prime(str(test_file))
        assert result == Integer(7)
        assert isinstance(result, Integer)
    
    def test_get_last_prime_single_data_row(self, tmp_path):
        """Test with file containing only header and one data row."""
        test_file = tmp_path / "single.csv"
        
        with open(test_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["n", "p", "j", "q", "k"])
            writer.writerow([11, 11, 1, 0, 0])
        
        result = get_last_prime(str(test_file))
        assert result == Integer(11)
    
    def test_get_last_prime_with_trailing_newline(self, tmp_path):
        """Test file that ends with newline character."""
        test_file = tmp_path / "trailing_newline.csv"
        
        with open(test_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["n", "p", "j", "q", "k"])
            writer.writerow([13, 13, 1, 0, 0])
            writer.writerow([17, 17, 1, 0, 0])
            f.write('\n')  # Extra newline
        
        result = get_last_prime(str(test_file))
        assert result == Integer(17)
    
    def test_get_last_prime_large_numbers(self, tmp_path):
        """Test with large prime numbers."""
        test_file = tmp_path / "large.csv"
        
        with open(test_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["n", "p", "j", "q", "k"])
            writer.writerow([982451653, 982451653, 1, 0, 0])
        
        result = get_last_prime(str(test_file))
        assert result == Integer(982451653)
    
    def test_get_last_prime_file_not_found(self, tmp_path):
        """Test FileNotFoundError for non-existent file."""
        non_existent = tmp_path / "missing.csv"
        
        with pytest.raises(FileNotFoundError, match="Data file not found"):
            get_last_prime(str(non_existent))
    
    def test_get_last_prime_empty_file(self, tmp_path):
        """Test ValueError for completely empty file."""
        empty_file = tmp_path / "empty.csv"
        empty_file.touch()  # Create empty file
        
        with pytest.raises(ValueError, match="Data file is empty"):
            get_last_prime(str(empty_file))
    
    def test_get_last_prime_header_only(self, tmp_path):
        """Test ValueError for file with only header."""
        header_only = tmp_path / "header_only.csv"
        
        with open(header_only, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["n", "p", "j", "q", "k"])
        
        with pytest.raises(ValueError, match="No data rows found"):
            get_last_prime(str(header_only))
    
    def test_get_last_prime_malformed_csv(self, tmp_path):
        """Test ValueError for malformed CSV data."""
        malformed = tmp_path / "malformed.csv"
        
        with open(malformed, 'w') as f:
            f.write("n,p,j,q,k\n")
            f.write("not_a_number,invalid,data,row,here\n")
        
        with pytest.raises(ValueError, match="Could not parse last line"):
            get_last_prime(str(malformed))
    
    def test_get_last_prime_insufficient_columns(self, tmp_path):
        """Test that single column with valid integer works (but may not be ideal CSV format)."""
        insufficient = tmp_path / "insufficient.csv"
        
        with open(insufficient, 'w') as f:
            f.write("n,p,j,q,k\n")
            f.write("13\n")  # Only one column
        
        # This actually works since we only need the first column
        result = get_last_prime(str(insufficient))
        assert result == Integer(13)
    
    def test_get_last_prime_multiple_trailing_newlines(self, tmp_path):
        """Test file with multiple trailing newlines."""
        test_file = tmp_path / "multiple_newlines.csv"
        
        with open(test_file, 'w') as f:
            f.write("n,p,j,q,k\n")
            f.write("19,19,1,0,0\n")
            f.write("23,23,1,0,0\n")
            f.write("\n\n\n")  # Multiple trailing newlines
        
        result = get_last_prime(str(test_file))
        assert result == Integer(23)


class TestCreateBackup:
    """Comprehensive tests for create_backup function."""
    
    def test_create_backup_basic(self, tmp_path, monkeypatch):
        """Test basic backup creation functionality."""
        # Setup test file
        test_file = tmp_path / "data.csv"
        test_file.write_text("n,p,j,q,k\n2,2,1,0,0\n")
        
        # Mock get_config to use tmp_path
        def mock_get_config():
            return PPPartConfig(
                data_dir=str(tmp_path),
                output_dir=str(tmp_path),
                backup_dir=os.path.join(str(tmp_path), "backups"),
                temp_dir=os.path.join(str(tmp_path), "temp")
            )
        
        monkeypatch.setattr("pppart.utils.get_config", mock_get_config)
        
        # Create backup
        create_backup(str(test_file))
        
        # Verify backup directory was created
        backup_dir = os.path.join(str(tmp_path), "backups")
        assert os.path.exists(backup_dir)
        assert os.path.isdir(backup_dir)
        
        # Verify backup file was created
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".csv.bak")]
        assert len(backup_files) == 1
        
        # Verify backup content matches original
        backup_file_path = os.path.join(backup_dir, backup_files[0])
        with open(backup_file_path, 'r') as f:
            backup_content = f.read()
        original_content = test_file.read_text()
        assert backup_content == original_content
    
    def test_create_backup_nonexistent_file(self, tmp_path, monkeypatch):
        """Test that create_backup does nothing for non-existent files."""
        def mock_get_config():
            return PPPartConfig(
                data_dir=str(tmp_path),
                output_dir=str(tmp_path),
                backup_dir=os.path.join(str(tmp_path), "backups"),
                temp_dir=os.path.join(str(tmp_path), "temp")
            )
        
        monkeypatch.setattr("pppart.utils.get_config", mock_get_config)
        
        non_existent = tmp_path / "missing.csv"
        
        # Should not raise exception
        create_backup(str(non_existent))
        
        # Backup directory should not be created for non-existent files
        backup_dir = os.path.join(str(tmp_path), "backups")
        assert not os.path.exists(backup_dir)
    
    def test_create_backup_preserves_permissions(self, tmp_path, monkeypatch):
        """Test that backup preserves file permissions and metadata."""
        test_file = tmp_path / "restricted.csv"
        test_file.write_text("test data")
        test_file.chmod(0o644)
        
        def mock_get_config():
            return PPPartConfig(
                data_dir=str(tmp_path),
                output_dir=str(tmp_path),
                backup_dir=os.path.join(str(tmp_path), "backups"),
                temp_dir=os.path.join(str(tmp_path), "temp")
            )
        
        monkeypatch.setattr("pppart.utils.get_config", mock_get_config)
        
        create_backup(str(test_file))
        
        backup_dir = os.path.join(str(tmp_path), "backups")
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".csv.bak")]
        assert len(backup_files) == 1
        
        # Verify permissions are preserved (shutil.copy2 preserves metadata)
        backup_file_path = os.path.join(backup_dir, backup_files[0])
        backup_stat = os.stat(backup_file_path)
        original_stat = test_file.stat()
        assert backup_stat.st_mode == original_stat.st_mode
    
    def test_create_backup_filename_format(self, tmp_path, monkeypatch):
        """Test backup filename format includes timestamp."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("data")
        
        def mock_get_config():
            return PPPartConfig(
                data_dir=str(tmp_path),
                output_dir=str(tmp_path),
                backup_dir=os.path.join(str(tmp_path), "backups"),
                temp_dir=os.path.join(str(tmp_path), "temp")
            )
        
        monkeypatch.setattr("pppart.utils.get_config", mock_get_config)
        
        create_backup(str(test_file))
        
        backup_dir = os.path.join(str(tmp_path), "backups")
        backup_files = [f for f in os.listdir(backup_dir) if f.endswith(".csv.bak")]
        assert len(backup_files) == 1
        
        # Verify filename format: YYYY-MM-DD_HHMM.csv.bak
        backup_name = backup_files[0]
        assert backup_name.endswith(".csv.bak")
        
        # Extract timestamp part (before .csv.bak)
        timestamp_part = backup_name[:-8]  # Remove .csv.bak
        assert len(timestamp_part) == 15  # YYYY-MM-DD_HHMM format
        assert timestamp_part[4] == '-'
        assert timestamp_part[7] == '-'
        assert timestamp_part[10] == '_'


class TestPPPartConfig:
    """Test PPPartConfig dataclass edge cases."""
    
    def test_config_properties(self, tmp_path):
        """Test PPPartConfig property methods work correctly."""
        config = PPPartConfig(
            data_dir=os.path.join(str(tmp_path), "data"),
            output_dir=os.path.join(str(tmp_path), "output"), 
            backup_dir=os.path.join(str(tmp_path), "backup"),
            temp_dir=os.path.join(str(tmp_path), "temp")
        )
        
        # Test that properties combine paths correctly
        assert os.path.basename(config.default_data_path) == "partition_data.csv"
        assert os.path.basename(config.default_output_path) == "partition_data.csv"
        assert config.data_dir.endswith("data")
        assert config.output_dir.endswith("output")
        assert config.default_batch_size == 250
    
    def test_config_custom_filename(self, tmp_path):
        """Test PPPartConfig with custom filename."""
        config = PPPartConfig(
            data_dir=os.path.join(str(tmp_path), "data"),
            output_dir=os.path.join(str(tmp_path), "output"),
            backup_dir=os.path.join(str(tmp_path), "backup"),
            temp_dir=os.path.join(str(tmp_path), "temp"),
            default_data_file="custom_partitions.csv"
        )
        
        # Test custom filename is used correctly
        assert os.path.basename(config.default_data_path) == "custom_partitions.csv"
        assert os.path.basename(config.default_output_path) == "custom_partitions.csv"


class TestGetConfigEdgeCases:
    """Test edge cases for get_config function."""
    
    def test_get_config_environment_variables(self, monkeypatch, tmp_path):
        """Test get_config with environment variables set."""
        data_dir = tmp_path / "env_data"
        output_dir = tmp_path / "env_output" 
        backup_dir = tmp_path / "env_backup"
        
        monkeypatch.setenv("PPPART_DATA_DIR", str(data_dir))
        monkeypatch.setenv("PPPART_OUTPUT_DIR", str(output_dir))
        monkeypatch.setenv("PPPART_BACKUP_DIR", str(backup_dir))
        
        config = get_config()
        
        assert str(config.data_dir) == str(data_dir)
        assert str(config.output_dir) == str(output_dir)
        assert str(config.backup_dir) == str(backup_dir)
    
    def test_get_config_partial_env_vars(self, monkeypatch, tmp_path):
        """Test get_config with only some environment variables set."""
        data_dir = tmp_path / "partial_data"
        
        monkeypatch.setenv("PPPART_DATA_DIR", str(data_dir))
        # Don't set other env vars - should use defaults
        
        config = get_config()
        
        assert str(config.data_dir) == str(data_dir)
        assert str(config.output_dir) == 'src/pppart/data/tmp'  # Default
        assert str(config.backup_dir) == 'src/pppart/data/backups'  # Default 