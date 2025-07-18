import pytest
from pppart.core import generate_partitions, PartitionDict
from pppart.utils import print_summary
from sage.all import Integer
import re

# Mock data for testing print_summary formatting without expensive computation
def _create_mock_partition_data() -> PartitionDict:
    """Create lightweight mock data for testing print_summary formatting."""
    mock_data = {
        Integer(2): {(2, 1, 0, 0)},
        Integer(3): {(3, 1, 0, 0)}, 
        Integer(5): {(4, 2, 1, 0), (5, 1, 0, 0)},
        Integer(7): {(0, 0, 0, 0)},  # Zero partition case
        Integer(11): {(9, 3, 2, 0), (8, 3, 3, 0), (11, 1, 0, 0)},
        Integer(13): {(0, 0, 0, 0)},  # Another zero partition
    }
    return mock_data

def _parse_summary_output(output: str) -> dict:
    """Parse print_summary output into structured data for testing."""
    lines = output.strip().split('\n')
    stats = {}
    
    # Parse summary statistics section
    for line in lines:
        if "Primes processed:" in line:
            stats['primes_processed'] = int(re.search(r'Primes processed: (\d+)', line).group(1))
        elif "Total partitions found:" in line:
            stats['total_partitions'] = int(re.search(r'Total partitions found: (\d+)', line).group(1))
        elif "Zero-partition primes:" in line:
            match = re.search(r'Zero-partition primes: (\d+) \((\d+\.?\d*)%\)', line)
            if match:
                stats['zero_partition_count'] = int(match.group(1))
                stats['zero_partition_percentage'] = float(match.group(2))
        elif "Average partitions per prime:" in line:
            stats['avg_partitions'] = float(re.search(r'Average partitions per prime: (\d+\.?\d*)', line).group(1))
    
    # Parse distribution section
    stats['has_distribution_section'] = "=== Partition Count Distribution ===" in output
    stats['has_bin_counts'] = "partitions:" in output and "primes" in output
    
    return stats

def test_print_summary_content(capsys):
    """Test print_summary content and logic with structured assertions."""
    mock_data = _create_mock_partition_data()
    num_primes = len(mock_data)
    
    print_summary(mock_data, num_primes)
    captured = capsys.readouterr()
    
    stats = _parse_summary_output(captured.out)
    
    # Test basic statistics
    assert stats['primes_processed'] == 6
    assert stats['total_partitions'] == 9  # 1+1+2+1+3+1
    assert stats['zero_partition_count'] == 2  # primes 7 and 13
    assert stats['zero_partition_percentage'] == 33.3  # 2/6 * 100
    assert abs(stats['avg_partitions'] - 1.5) < 0.01  # 9/6 = 1.5
    
    # Test section structure
    assert stats['has_distribution_section']
    assert stats['has_bin_counts']

def test_print_summary_structure(capsys):
    """Test that print_summary produces well-structured output."""
    mock_data = _create_mock_partition_data()
    
    print_summary(mock_data, len(mock_data))
    captured = capsys.readouterr()
    output = captured.out
    
    # Test section headers exist
    assert "=== Summary Statistics ===" in output
    assert "=== Partition Count Distribution ===" in output
    
    # Test required fields present
    required_fields = [
        "Primes processed:",
        "Total partitions found:",
        "Zero-partition primes:",
        "Average partitions per prime:"
    ]
    for field in required_fields:
        assert field in output, f"Missing required field: {field}"
    
    # Test reasonable line count (should have multiple sections)
    lines = output.strip().split('\n')
    assert len(lines) >= 8, "Output should have multiple informative lines"

def test_print_summary_edge_cases(capsys):
    """Test print_summary with edge case data."""
    # Test all zero partitions
    all_zeros = {Integer(7): {(0, 0, 0, 0)}, Integer(11): {(0, 0, 0, 0)}}
    print_summary(all_zeros, 2)
    captured = capsys.readouterr()
    stats = _parse_summary_output(captured.out)
    
    assert stats['zero_partition_count'] == 2
    assert stats['zero_partition_percentage'] == 100.0
    assert stats['total_partitions'] == 2
    
    # Test no zero partitions
    capsys.readouterr()  # Clear
    no_zeros = {Integer(2): {(2, 1, 0, 0)}, Integer(3): {(3, 1, 0, 0)}}
    print_summary(no_zeros, 2)
    captured = capsys.readouterr()
    stats = _parse_summary_output(captured.out)
    
    assert stats['zero_partition_count'] == 0
    assert stats['zero_partition_percentage'] == 0.0

@pytest.mark.slow
def test_generate_partitions_functional():
    """Separate functional test for generate_partitions core logic."""
    num_primes = 50  # Smaller for faster testing
    batch_size = 25
    
    result = generate_partitions(
        num_primes=num_primes,
        batch_size=batch_size, 
        num_processes=1,
        resume=False
    )
    
    # Test core functionality
    assert isinstance(result, dict)
    assert len(result) == num_primes
    assert all(isinstance(k, Integer) for k in result.keys())
    assert all(isinstance(v, set) for v in result.values()) 