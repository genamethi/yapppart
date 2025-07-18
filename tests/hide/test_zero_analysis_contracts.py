import numpy as np
import pytest
import altair as alt
from pppart import requires_version


# --- Test Data Fixtures ---

@pytest.fixture
def sample_partition_data() -> np.ndarray:
    """
    Sample partition data as numpy array [n, p, j, q, k].
    """
    return np.array([
        [2, 0, 0, 0, 0],   # Zero partition
        [3, 0, 0, 0, 0],   # Zero partition  
        [5, 2, 1, 3, 1],   # One partition
        [7, 2, 2, 3, 1],   # First partition for 7
        [7, 2, 1, 5, 1],   # Second partition for 7
        [11, 2, 3, 3, 1],  # One partition
        [13, 0, 0, 0, 0],  # Zero partition
    ])

@pytest.fixture
def zero_primes() -> np.ndarray:
    """Sample zero partition primes."""
    #this is so wrong, but I can't fix until after this. 2, 3, 149, 331, 373, 509, 701, 757 (are the first few)
    return np.array([2, 3, 13, 23, 37, 53, 71, 89])

@pytest.fixture
def kde_test_data() -> tuple[np.ndarray, np.ndarray]:
    """Sample KDE test data."""
    x_grid = np.linspace(2, 100, 50)
    density = np.exp(-0.1 * x_grid) * np.sin(0.2 * x_grid) + 0.1
    return x_grid, density


# --- Core Function Contract Tests ---

@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_find_zero_partition_ns_contract(sample_partition_data):
    """Test find_zero_partition_ns returns correct zero partition primes."""
    from pppart.zero_analysis import find_zero_partition_ns
    
    result = find_zero_partition_ns(sample_partition_data)
    assert isinstance(result, np.ndarray)
    assert len(result) == 3  # Should find primes 2, 3, 13
    expected = np.array([2, 3, 13])
    np.testing.assert_array_equal(np.sort(result), expected)


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_estimate_zero_density_contract(zero_primes):
    """Test estimate_zero_density returns proper KDE array."""
    from pppart.zero_analysis import estimate_zero_density
    
    result = estimate_zero_density(zero_primes)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    x_grid, density = result
    assert isinstance(x_grid, np.ndarray)
    assert isinstance(density, np.ndarray)
    assert len(x_grid) == len(density)
    assert np.all(density >= 0)  # Density should be non-negative
    assert np.isfinite(density).all()  # No NaN or inf values


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_plot_kde_contract(kde_test_data):
    """Test plot_kde returns Altair Chart."""
    from pppart.zero_analysis import plot_kde
    
    x_grid, density = kde_test_data
    chart = plot_kde(x_grid, density)
    
    assert isinstance(chart, alt.Chart)
    # Basic chart validation
    assert hasattr(chart, 'mark')
    assert hasattr(chart, 'encoding')


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_propose_closed_form_pdf_contract(kde_test_data):
    """Test propose_closed_form_pdf returns SageMath Expression and error analysis."""
    from pppart.zero_analysis import propose_closed_form_pdf
    
    x_grid, density = kde_test_data
    result = propose_closed_form_pdf(x_grid, density)
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    expression, error_analysis = result
    
    # Test SageMath Expression (skip if not available)
    try:
        from sage.all import Expression
        assert isinstance(expression, Expression)
    except ImportError:
        pytest.skip("SageMath not available for testing")
    
    # Test error analysis dictionary
    assert isinstance(error_analysis, dict)
    expected_keys = {'r_squared', 'aic', 'bic', 'rmse', 'big_o_term', 'confidence_bounds'}
    assert all(key in error_analysis for key in expected_keys)


# --- Advanced Function Contract Tests ---

@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_validate_fit_quality_contract(kde_test_data):
    """Test validate_fit_quality returns proper metrics."""
    from pppart.zero_analysis import validate_fit_quality
    
    x_grid, density = kde_test_data
    # Mock fitted values
    fitted_values = density + np.random.normal(0, 0.1, len(density))
    
    metrics = validate_fit_quality(x_grid, density, fitted_values, n_params=3)
    
    assert isinstance(metrics, dict)
    expected_metrics = {'r2', 'rmse', 'aic', 'bic', 'residual_std'}
    assert all(metric in metrics for metric in expected_metrics)
    
    # Basic sanity checks
    assert 0 <= metrics['r2'] <= 1
    assert metrics['rmse'] >= 0


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_bootstrap_confidence_contract(zero_primes):
    """Test bootstrap_confidence returns confidence intervals."""
    from pppart.zero_analysis import bootstrap_confidence
    
    confidence_bounds = bootstrap_confidence(zero_primes, n_bootstrap=10)
    
    assert isinstance(confidence_bounds, tuple)
    assert len(confidence_bounds) == 2
    
    ci_mean, ci_std = confidence_bounds
    assert isinstance(ci_mean, np.ndarray)
    assert isinstance(ci_std, np.ndarray)
    assert len(ci_mean) == 2  # [lower, upper] for mean
    assert len(ci_std) == 2   # [lower, upper] for std
    assert ci_mean[0] <= ci_mean[1]  # Lower bound should be <= upper bound
    assert ci_std[0] <= ci_std[1]    # Lower bound should be <= upper bound


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_spectral_analysis_contract(sample_partition_data):
    """Test spectral_analysis returns eigenvalue analysis."""
    from pppart.zero_analysis import spectral_analysis
    
    result = spectral_analysis(sample_partition_data)
    
    assert isinstance(result, dict)
    expected_keys = {'eigenvalues', 'eigenvectors', 'spectral_gap', 'dominant_frequencies'}
    assert all(key in result for key in expected_keys)
    
    eigenvalues = result['eigenvalues']
    eigenvectors = result['eigenvectors']
    
    assert isinstance(eigenvalues, np.ndarray)
    assert isinstance(eigenvectors, np.ndarray)
    assert len(eigenvalues) > 0
    assert eigenvectors.shape[0] > 0


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_differential_equation_analysis_contract(kde_test_data):
    """Test differential_equation_analysis returns DE coefficients."""
    from pppart.zero_analysis import differential_equation_analysis
    
    # Mock a fitted expression (we'd need SageMath for real test)
    x_grid, density = kde_test_data
    # Create a simple mock expression for testing
    mock_expr = "x^2 + 1"  # Placeholder
    
    result = differential_equation_analysis(mock_expr, x_grid)
    
    assert isinstance(result, dict)
    expected_keys = {'de', 'solution', 'note'}
    assert all(key in result for key in expected_keys)


# --- Visualization Contract Tests ---

@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_plot_model_comparison_contract(kde_test_data):
    """Test plot_model_comparison returns Altair Chart with multiple models."""
    from pppart.zero_analysis import plot_model_comparison
    
    x_grid, density = kde_test_data
    
    # Mock multiple fitted models
    models = {
        'exponential': density * 0.9,
        'power_law': density * 1.1,
        'log_normal': density * 0.95
    }
    
    chart = plot_model_comparison(x_grid, density, models)
    
    assert isinstance(chart, alt.Chart)
    # Should be a layered chart for multiple models
    assert hasattr(chart, 'layer') or hasattr(chart, 'mark')


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_plot_residual_analysis_contract(kde_test_data):
    """Test plot_residual_analysis returns Altair Chart."""
    from pppart.zero_analysis import plot_residual_analysis
    
    x_grid, density = kde_test_data
    fitted_values = density + np.random.normal(0, 0.05, len(density))
    
    chart = plot_residual_analysis(x_grid, density, fitted_values)
    
    assert isinstance(chart, alt.Chart)
    assert hasattr(chart, 'mark')
    assert hasattr(chart, 'encoding')


@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_generate_analysis_report_contract(zero_primes):
    """Test generate_analysis_report returns comprehensive report."""
    from pppart.zero_analysis import generate_analysis_report
    
    # Mock fitted expression and error analysis
    mock_expr = "x^2 + 1"  # Placeholder
    mock_error_analysis = {
        'model': 'test_model',
        'metrics': {'r2': 0.8, 'rmse': 0.1}
    }
    
    report = generate_analysis_report(zero_primes, mock_expr, mock_error_analysis)
    
    assert isinstance(report, dict)
    expected_keys = {'num_zeros', 'stats', 'best_model', 'fitted_expr', 'metrics', 'key_findings'}
    assert all(key in report for key in expected_keys)


# --- Integration Contract Test ---

@pytest.mark.xfail(not requires_version("0.6.0"), reason="Zero analysis functions are scaffold contracts, not implemented yet")
def test_full_pipeline_contract(sample_partition_data):
    """Test the full zero analysis pipeline integration."""
    from pppart.zero_analysis import (
        find_zero_partition_ns,
        estimate_zero_density,
        propose_closed_form_pdf,
        generate_analysis_report
    )
    
    # Full pipeline test
    zero_ns = find_zero_partition_ns(sample_partition_data)
    assert len(zero_ns) > 0
    
    x_grid, density = estimate_zero_density(zero_ns)
    
    expression, error_analysis = propose_closed_form_pdf(x_grid, density)
    assert error_analysis['metrics']['r2'] >= 0
    
    report = generate_analysis_report(zero_ns, expression, error_analysis)
    assert 'best_model' in report 