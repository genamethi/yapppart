#!/usr/bin/env python3
"""
Setup script for pppart with dynamic versioning and Cython support.
Centralizes configuration that flows to pyproject.toml -> utils.py -> everything else.
"""

import os
import subprocess
import tomllib
from unittest import result
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import numpy

# ============================================================================
# CENTRALIZED CONFIGURATION
# ============================================================================

class PPPartSetupConfig:
    """Central configuration for setup-time decisions."""
    
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.pyproject_path = os.path.join(self.project_root, "pyproject.toml")
        self.src_path = os.path.join(self.project_root, "src", "pppart")
        
        # Load base config from pyproject.toml
        with open(self.pyproject_path, "rb") as f:
            self.pyproject_data = tomllib.load(f)
        
        # Dynamic version determination
        self.version = self._get_dynamic_version()
        
        # Cython configuration
        self.use_cython = self._should_use_cython()
        self.extensions = self._get_extensions() if self.use_cython else []
    
    def _get_dynamic_version(self) -> str:
        """Dynamic version determination with fallback hierarchy."""
        # 1. Try pyproject.toml
        if version := self.pyproject_data["project"]["version"]:
            return version

        # 2. Try environment variable (for CI overrides)
        if env_version := os.getenv('PPPART_VERSION'):
            return env_version
    
    def _should_use_cython(self) -> bool:
        """Determine if Cython extensions should be built."""
        # Environment override
        if env_cython := os.getenv('PPPART_USE_CYTHON'):
            return env_cython.lower() in ('1', 'true', 'yes')
        
        # Default: use Cython if available and not in minimal install
        try:
            import Cython
            return not os.getenv('PPPART_MINIMAL_INSTALL')
        except ImportError:
            return False
    
    def _get_extensions(self) -> list:
        """Define Cython extensions for vectorized operations."""
        if not self.use_cython:
            return []
        
        extensions = [
            Extension(
                "pppart.core_cython",
                [os.path.join(self.src_path, "core_cython.pyx")],
                include_dirs=[numpy.get_include()],
                define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
                extra_compile_args=["-O3", "-ffast-math"],
                language="c++",
            ),
            Extension(
                "pppart.vectorized_partitions", 
                [os.path.join(self.src_path, "vectorized_partitions.pyx")],
                include_dirs=[numpy.get_include()],
                define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
                extra_compile_args=["-O3", "-ffast-math"],
                language="c++",
            )
        ]
        
        return extensions

# ============================================================================
# CUSTOM BUILD COMMANDS
# ============================================================================

class OptimizedBuildExt(build_ext):
    """Custom build_ext with optimization and configuration injection."""
    
    def run(self):
        # Inject build-time configuration into package
        self._write_build_config()
        super().run()
    
    def _write_build_config(self):
        """Write build configuration to be accessible at runtime."""
        config_content = f'''"""
Build-time configuration for pppart.
Generated automatically by setup.py.
"""

# Build configuration
BUILD_VERSION = "{config.version}"
BUILT_WITH_CYTHON = {config.use_cython}
BUILD_EXTENSIONS = {[ext.name for ext in config.extensions]}
GIT_AVAILABLE = {self._git_available()}

# Configuration hierarchy marker
SETUP_PY_CONFIGURED = True
'''
        
        build_config_path = os.path.join(config.src_path, "_build_config.py")
        with open(build_config_path, 'w') as f:
            f.write(config_content)
    
    def _git_available(self) -> bool:
        try:
            subprocess.run(['git', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

# ============================================================================
# SETUP EXECUTION
# ============================================================================

def main():
    global config
    config = PPPartSetupConfig()
    
    # Cythonize extensions if needed
    ext_modules = []
    if config.use_cython:
        try:
            from Cython.Build import cythonize
            ext_modules = cythonize(
                config.extensions,
                compiler_directives={
                    'language_level': 3,
                    'boundscheck': False,
                    'wraparound': False,
                    'cdivision': True,
                }
            )
            print(f"Building with Cython extensions: {[ext.name for ext in config.extensions]}")
        except ImportError:
            print("Cython not available, building without extensions")
    
    # Setup with dynamic configuration
    setup(
        version=config.version,
        ext_modules=ext_modules,
        cmdclass={'build_ext': OptimizedBuildExt},
        # Let pyproject.toml handle the rest
    )
    
    print(f"Setup completed. Version: {config.version}, Cython: {config.use_cython}")

if __name__ == "__main__":
    main() 