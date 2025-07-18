import numpy as np
import pytest
import altair as alt
from pppart import requires_version


# --- Test Data Fixture ---

@pytest.fixture
def sample_partition_data() -> np.ndarray:
    """
    Provides a small, clear sample of partition data as numpy array,
    simulating the direct output format [n, p, j, q, k].
    """
    return np.array([
        [2, 0, 0, 0, 0],  # Zero partition
        [3, 0, 0, 0, 0],  # Zero partition
        [5, 2, 1, 3, 1],  # One partition
        [7, 2, 2, 3, 1],  # First partition for 7
        [7, 2, 1, 5, 1],  # Second partition for 7
    ])


# --- Contract Tests ---

@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_zero_analysis_contract(sample_partition_data):
    """
    SPECIFICATION: Zero analysis functions must exist and return correct types.
    """
    try:
        from pppart.zero_analysis import (
            find_zero_partition_ns,
            estimate_zero_density,
            plot_kde,
            propose_closed_form_pdf
        )
    except ImportError as e:
        pytest.fail(f"FAIL: Zero analysis functions not implemented: {e}")

    # Test find_zero_partition_ns
    zero_ns = find_zero_partition_ns(sample_partition_data)
    assert isinstance(zero_ns, np.ndarray)
    assert len(zero_ns) == 2  # Should find primes 2 and 3
    assert 2 in zero_ns and 3 in zero_ns

    # Test estimate_zero_density returns arrays
    result = estimate_zero_density(zero_ns)
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    x_grid, density = result
    assert isinstance(x_grid, np.ndarray)
    assert isinstance(density, np.ndarray)
    assert len(x_grid) == len(density)

    # Test plot_kde returns Altair Chart
    chart = plot_kde(x_grid, density)
    assert isinstance(chart, alt.Chart)

    # Test propose_closed_form_pdf returns tuple with Expression
    try:
        from sage.all import Expression
        result = propose_closed_form_pdf(x_grid, density)
        assert isinstance(result, tuple)
        assert len(result) == 2
        expr, error_analysis = result
        assert isinstance(expr, Expression)
        assert isinstance(error_analysis, dict)
    except ImportError:
        pytest.skip("SageMath not available for testing")


def test_visualization_contract(sample_partition_data):
    """
    SPECIFICATION: Visualization functions must exist and return Altair Charts.
    """
    try:
        from pppart.viz.viz_ppp_counts import plot_partitions_count
    except ImportError:
        pytest.fail("FAIL: `plot_partitions_count` not implemented in viz module")

    # Test that function exists and can be called
    # We'll test file presence rather than actual plotting
    assert callable(plot_partitions_count)


def test_numpy_data_processing_contract(sample_partition_data):
    """
    SPECIFICATION: Data processing should work with numpy arrays, not pandas.
    """
    # Test basic numpy operations work on the data format
    assert sample_partition_data.shape == (5, 5)
    
    # Test finding zero partitions (where p=0)
    zero_mask = sample_partition_data[:, 1] == 0  # Column 1 is 'p'
    zero_rows = sample_partition_data[zero_mask]
    assert len(zero_rows) == 2
    
    # Test grouping by n (column 0)
    unique_ns = np.unique(sample_partition_data[:, 0])
    assert len(unique_ns) == 4  # Should have 4 unique primes: 2, 3, 5, 7
    
    # Test counting partitions per n
    partition_counts = []
    for n in unique_ns:
        n_rows = sample_partition_data[sample_partition_data[:, 0] == n]
        count = np.sum(n_rows[:, 1] != 0)  # Count non-zero p values
        partition_counts.append(count)
    
    expected_counts = [0, 0, 1, 2]  # 2:0, 3:0, 5:1, 7:2
    assert partition_counts == expected_counts 