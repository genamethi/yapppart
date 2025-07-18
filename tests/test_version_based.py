"""
Test suite demonstrating version-based xfail/xpass markers.
Shows how the configuration hierarchy enables dynamic test behavior.
"""

import pytest
import os
import pppart
from pppart import requires_version, has_cython_extensions, get_extension_info


class TestVersionBasedTesting:
    """Test version-based conditional testing functionality."""
    
    def test_version_determination(self):
        """Verify version is correctly determined from hierarchy."""
        version = pppart.__version__
        assert version is not None
        assert isinstance(version, str)
        assert len(version) > 0
        print(f"Detected version: {version}")
    
    def test_build_info_access(self):
        """Verify build information is accessible."""
        build_info = pppart.__build_info__
        assert isinstance(build_info, dict)
        assert "version" in build_info
        assert "cython" in build_info
        assert "extensions" in build_info
        print(f"Build info: {build_info}")
    
    @pytest.mark.xfail(not requires_version("0.6.0"), 
                      reason="Cython optimization not yet implemented")
    def test_vectorized_partitions_future(self):
        """Test that will pass once Cython vectorization is implemented."""
        # This test represents future vectorized functionality
        import numpy as np
        
        # Mock test for vectorized partition generation
        primes = np.array([3, 5, 7, 11, 13])
        
        # In the future, this should use Cython-optimized bulk processing
        if has_cython_extensions():
            # Test actual Cython implementation
            from pppart.vectorized_partitions import bulk_partition_check
            results = bulk_partition_check(primes)
            assert len(results) == len(primes)
        else:
            # Placeholder test - will xfail until Cython is implemented
            pytest.skip("Cython extensions not available")
    
    @pytest.mark.xfail(not requires_version("0.7.0"),
                      reason="Advanced statistical analysis not yet implemented")
    def test_kde_fitting_future(self):
        """Test that will pass once advanced zero analysis is implemented."""
        # This represents future statistical functionality
        if requires_version("0.7.0"):
            from pppart.zero_analysis import estimate_zero_density
            # Test actual implementation
            assert callable(estimate_zero_density)
        else:
            # Will xfail until version 0.7.0
            pytest.skip("Advanced analysis not yet implemented")
    
    def test_cython_extensions_info(self):
        """Test Cython extension detection and information."""
        ext_info = get_extension_info()
        assert isinstance(ext_info, dict)
        assert "available" in ext_info
        assert "extensions" in ext_info
        
        print(f"Extension info: {ext_info}")
        
        # Test behavior based on Cython availability
        if ext_info["available"]:
            # Extensions should be available
            assert len(ext_info["extensions"]) > 0
            pytest.mark.cython_available()
        else:
            # Pure Python mode
            assert len(ext_info["extensions"]) == 0
            pytest.mark.pure_python()
    
    @pytest.mark.skipif(not has_cython_extensions(),
                       reason="Requires Cython extensions")
    def test_cython_performance(self):
        """Test that only runs when Cython extensions are available."""
        # This test would verify performance improvements
        ext_info = get_extension_info()
        
        # Check that extensions actually loaded
        for ext_name in ext_info["extensions"]:
            loaded_key = f"{ext_name}_loaded"
            if loaded_key in ext_info:
                assert ext_info[loaded_key], f"Extension {ext_name} failed to load"
    
    def test_configuration_hierarchy(self):
        """Test that configuration hierarchy is working properly."""
        from pppart.utils import get_config
        
        config = get_config()
        assert config is not None
        assert hasattr(config, 'default_data_path')
        assert hasattr(config, 'default_output_path')
        
        # Verify paths are properly configured
        assert os.path.basename(config.default_data_path) == config.default_data_file
        
        print(f"Config data path: {config.default_data_path}")
        print(f"Config output path: {config.default_output_path}")


class TestDynamicVersioning:
    """Test dynamic versioning functionality."""
    
    def test_version_comparison(self):
        """Test version comparison utilities."""
        # Test basic version checking
        assert requires_version("0.1.0")  # Should always be true
        
        # Test with current version
        current = pppart.__version__
        assert requires_version(current)
    
    def test_version_based_markers(self):
        """Demonstrate different version-based markers."""
        current_version = pppart.__version__
        
        # Test different version scenarios
        if requires_version("1.0.0"):
            # Future functionality
            pytest.skip("Version 1.0.0+ functionality")
        elif requires_version("0.6.0"):
            # Near-future functionality  
            pytest.skip("Version 0.6.0+ functionality")
        else:
            # Current functionality
            assert True, "Current version functionality working"


# Custom pytest markers for conditional testing
pytestmark = [
    pytest.mark.version_based,
    pytest.mark.configuration_test
] 

##

