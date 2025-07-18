import pytest
from pppart.core import generate_partitions, PartitionDict
from pppart.utils import write_csv
from sage.all import Integer
import csv

def _create_mock_csv_data() -> PartitionDict:
    """Create lightweight mock data for testing CSV formatting."""
    return {
        Integer(2): {(2, 1, 0, 0)},
        Integer(3): {(3, 1, 0, 0)}, 
        Integer(5): {(4, 2, 1, 0), (5, 1, 0, 0)},
        Integer(7): {(0, 0, 0, 0)},
    }

def _parse_csv_content(file_path) -> dict:
    """Parse CSV content into structured data for testing."""
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    
    stats = {
        'header': header,
        'row_count': len(rows),
        'rows': rows,
        'zero_partitions': [row for row in rows if row[1] == '0'],
        'non_zero_partitions': [row for row in rows if row[1] != '0'],
        'unique_primes': set(row[0] for row in rows),
    }
    return stats

def test_csv_formatting(tmp_path):
    """Test CSV output formatting with structured assertions."""
    mock_data = _create_mock_csv_data()
    test_file = tmp_path / "test_output.csv"
    
    write_csv(mock_data, str(test_file))
    
    # Verify file was created
    assert test_file.exists()
    
    # Parse and validate structure
    csv_data = _parse_csv_content(test_file)
    
    # Test header format
    assert csv_data['header'] == ['n', 'p', 'j', 'q', 'k']
    
    # Test expected row count (2,3,5,5,7 = 5 data rows)
    assert csv_data['row_count'] == 5
    
    # Test data integrity
    assert len(csv_data['zero_partitions']) == 1  # Only prime 7
    assert len(csv_data['non_zero_partitions']) == 4  # 2,3,5,5
    assert len(csv_data['unique_primes']) == 4  # 2,3,5,7
    
    # Test specific content
    zero_row = csv_data['zero_partitions'][0]
    assert zero_row == ['7', '0', '0', '0', '0']
    
    # Test that all rows have 5 columns
    for row in csv_data['rows']:
        assert len(row) == 5, f"Row has wrong column count: {row}"
    
    # Test that all values are valid integers
    for row in csv_data['rows']:
        for val in row:
            assert val.isdigit(), f"Non-integer value found: {val}"

def test_csv_data_consistency(tmp_path):
    """Test that CSV data matches the input partition data structure."""
    mock_data = _create_mock_csv_data()
    test_file = tmp_path / "test_output.csv"
    
    write_csv(mock_data, str(test_file))
    csv_data = _parse_csv_content(test_file)
    
    # Reconstruct partition data from CSV to verify consistency
    reconstructed = {}
    for row in csv_data['rows']:
        n, p, j, q, k = map(int, row)
        if n not in reconstructed:
            reconstructed[n] = set()
        reconstructed[n].add((p, j, q, k))
    
    # Compare with original (convert Integer keys to int for comparison)
    original_int_keys = {int(k): v for k, v in mock_data.items()}
    
    assert reconstructed == original_int_keys

@pytest.mark.slow 
def test_csv_functional_generation(tmp_path):
    """Functional test: generate real data and validate CSV output structure."""
    num_primes = 50  # Small but real dataset
    batch_size = 25
    
    # Generate real partition data
    partition_data = generate_partitions(
        num_primes=num_primes,
        batch_size=batch_size,
        num_processes=1,
        resume=False
    )
    
    test_file = tmp_path / "functional_test.csv"
    write_csv(partition_data, str(test_file))
    
    csv_data = _parse_csv_content(test_file)
    
    # Test that we have data for all requested primes
    assert len(csv_data['unique_primes']) == num_primes
    
    # Test reasonable data characteristics
    assert csv_data['row_count'] >= num_primes  # At least one partition per prime
    assert len(csv_data['zero_partitions']) >= 0  # Some primes might have zero partitions
    
    # Test that first few primes are present (2, 3, 5, 7, 11)
    primes_found = sorted([int(p) for p in csv_data['unique_primes']])
    assert primes_found[:5] == [2, 3, 5, 7, 11]