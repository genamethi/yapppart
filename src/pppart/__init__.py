"""
pppart: Prime Partition Analysis Package

A package for analyzing Diophantine equations of the form:
n = p^j + q^k where p, q are primes and j, k >= 1

Configuration flows: setup.py -> pyproject.toml -> utils.py -> modules
"""

import os

# ============================================================================
# DYNAMIC VERSION DETERMINATION
# ============================================================================

def _get_version() -> str:
    """
    Simple version determination: pyproject.toml -> setup.py -> metadata.
    """
    # 1. Try pyproject.toml (source of truth)
    try:
        import tomllib
        from importlib.resources import files
        try:
            # Try package resources first (for installed package)
            project_root = files(__name__).parent.parent
            pyproject_path = project_root / "pyproject.toml"
            with pyproject_path.open("rb") as f:
                data = tomllib.load(f)
            return data["project"]["version"]
        except (FileNotFoundError, AttributeError):
            # Fallback to relative path (for development)
            pyproject_path = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
            if os.path.exists(pyproject_path):
                with open(pyproject_path, "rb") as f:
                    data = tomllib.load(f)
                return data["project"]["version"]
    except (ImportError, FileNotFoundError, KeyError):
        pass
    
    # 2. Try build-time configuration (from setup.py)
    try:
        from ._build_config import BUILD_VERSION, SETUP_PY_CONFIGURED
        if SETUP_PY_CONFIGURED:
            return BUILD_VERSION
    except ImportError:
        pass
    
    # 3. Try installed package metadata
    try:
        import importlib.metadata
        return importlib.metadata.version("pppart")
    except importlib.metadata.PackageNotFoundError:
        pass
    
    # 4. Ultimate fallback
    return "0.5.0+unknown"

# ============================================================================
# BUILD CONFIGURATION ACCESS
# ============================================================================

def _get_build_info() -> dict:
    """Access build-time configuration if available."""
    try:
        from ._build_config import (
            BUILD_VERSION, BUILT_WITH_CYTHON, BUILD_EXTENSIONS, 
            GIT_AVAILABLE, SETUP_PY_CONFIGURED
        )
        return {
            "version": BUILD_VERSION,
            "cython": BUILT_WITH_CYTHON,
            "extensions": BUILD_EXTENSIONS,
            "git_available": GIT_AVAILABLE,
            "setup_py_configured": SETUP_PY_CONFIGURED,
        }
    except ImportError:
        return {
            "version": _get_version(),
            "cython": False,
            "extensions": [],
            "git_available": False,
            "setup_py_configured": False,
        }

# ============================================================================
# VERSION-BASED UTILITIES FOR TESTING
# ============================================================================

def requires_version(min_version: str) -> bool:
    """
    Version checking utility for pytest xfail/xpass markers.
    
    Usage:
        @pytest.mark.xfail(not requires_version("0.6.0"), 
                          reason="Cython optimization not yet implemented")
    """
    try:
        from packaging import version
        current = version.parse(__version__)
        required = version.parse(min_version)
        return current >= required
    except ImportError:
        # Fallback simple comparison if packaging not available
        return __version__ >= min_version

def has_cython_extensions() -> bool:
    """Check if package was built with Cython extensions."""
    return _get_build_info()["cython"]

def get_extension_info() -> dict:
    """Get information about available extensions."""
    build_info = _get_build_info()
    info = {
        "available": build_info["cython"],
        "extensions": build_info["extensions"],
    }
    
    # Try to import and check actual availability
    if build_info["cython"]:
        for ext_name in build_info["extensions"]:
            try:
                __import__(ext_name)
                info[f"{ext_name}_loaded"] = True
            except ImportError:
                info[f"{ext_name}_loaded"] = False
    
    return info

# ============================================================================
# PACKAGE METADATA
# ============================================================================

__version__ = _get_version()
__build_info__ = _get_build_info()

# Export version-based utilities
__all__ = [
    "__version__", 
    "__build_info__",
    "requires_version", 
    "has_cython_extensions", 
    "get_extension_info"
]

# ============================================================================
# CONFIGURATION INTEGRATION MARKER
# ============================================================================

# This marker allows utils.py to detect the configuration hierarchy
_INIT_PY_CONFIGURED = True
