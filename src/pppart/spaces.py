"""Space classes for prime partition analysis."""

import numpy as np
from typing import Dict, List, Tuple, Union, Optional

class EuclideanSpaces:
    """Euclidean space operations for prime partition analysis."""

    def __init__(self):
        self.norms = {
            'std_norm': self._std_norm,
            'mm_norm': self._mm_norm
        }

    def _std_norm(self, data: np.ndarray) -> np.ndarray:
        """Standard normalization: (x - mean) / std."""
        # Add a small epsilon to std to avoid division by zero for constant columns
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        return (data - mean) / (std + 1e-8)

    def _mm_norm(self, data: np.ndarray) -> np.ndarray:
        """Min-max normalization: (x - min) / (max - min)."""
        min_vals = np.min(data, axis=0)
        max_vals = np.max(data, axis=0)
        # Add a small epsilon to the denominator to avoid division by zero
        return (data - min_vals) / ((max_vals - min_vals) + 1e-8)

    def get_euc_norm(self, data: np.ndarray, norm: str = 'std_norm') -> np.ndarray:
        """Normalize data using specified method."""
        if norm not in self.norms:
            raise ValueError(f"Unknown normalization method: {norm}")
        return self.norms[norm](data)

    def dist_mtx(self, data: np.ndarray) -> np.ndarray:
        """Compute Euclidean distance matrix using vectorized operations."""
        # This is a memory-intensive way for large N.
        # A more memory-efficient (but potentially slower) method is scipy's pdist
        diff = data[:, np.newaxis, :] - data[np.newaxis, :, :]
        dists = np.sqrt(np.sum(diff**2, axis=2))
        return dists

    # --- NEW METHOD ---

    def get_adj_mtx(self, dist_mtx: np.ndarray, epsilon: float) -> np.ndarray:
        """
        Compute the adjacency matrix from a distance matrix.

        Args:
            dist_mtx: Distance matrix of shape (n_samples, n_samples)
            epsilon: The distance threshold for creating an edge.

        Returns:
            Adjacency matrix of shape (n_samples, n_samples)
        """
        # Create a boolean matrix where True means an edge exists
        adj_mtx = (dist_mtx < epsilon).astype(int)
        # An element should not have an edge to itself
        np.fill_diagonal(adj_mtx, 0)
        return adj_mtx





class qSpaceClass:
    """Finite q^k space operations for prime partition analysis."""
    
    def __init__(self):
        pass
    
    def glob_q_val(self, arr, q, max_k=None):
        """Vectorized q-adic valuation for arbitrary integers.
        
        Args:
            arr: Array of integers
            q: Prime base (must be >= 2)
            max_k: Optional stop condition (k >= max_k). If None, computes full valuation.
        
        Returns:
            Array of q- base valuations
        """
        if not isinstance(q, int) or q < 2:
            raise ValueError("'q' must be a prime integer (>= 2).")

        max_int = np.iinfo(np.int64).max
        valuations = np.full(arr.shape, max_int, dtype=np.int64)

        non_zero_mask = arr != 0
        non_zero_vals = arr[non_zero_mask].copy()
        non_zero_valuations = np.zeros_like(non_zero_vals, dtype=np.int64)
        
        while True:
            divisible_mask = (non_zero_vals % q == 0)
            if not np.any(divisible_mask):
                break
            
            # Check stop condition if max_k is specified
            if max_k is not None and np.any(non_zero_valuations[divisible_mask] >= max_k):
                break
            
            non_zero_vals[divisible_mask] //= q
            non_zero_valuations[divisible_mask] += 1
            
        valuations[non_zero_mask] = non_zero_valuations
        return valuations
    
    def dist_mtx(self, data: np.ndarray, q: int, max_k: int = None) -> np.ndarray:
        """Compute q-adic distance matrix using vectorized operations.
        
        Args:
            data: Array of shape (n_samples, n_features) with n values in first column
            q: Prime base for q-adic valuation
            max_k: Optional stop condition for chain length
        
        Returns:
            Distance matrix based on q-adic valuations
        """
        n_vals = data[:, 0].astype(int)
        
        # Use broadcasting for pairwise differences
        diff_mat = np.abs(n_vals[:, np.newaxis] - n_vals[np.newaxis, :])
        
        # Compute q-adic valuations for all differences
        v_mat = self.glob_q_val(diff_mat, q, max_k)
        
        # Handle inf values (max_int) and compute distances using float arithmetic
        dists = np.where(v_mat == np.iinfo(np.int64).max, 0, float(q)**(-v_mat.astype(float)))
        
        return dists
    
    def groupby_q(self, raw_data: np.ndarray) -> dict[int, np.ndarray]:
        """Groups data by unique q values using vectorized operations.
        
        Args:
            raw_data: The raw data array with columns [n, p, j, q, k]
        
        Returns:
            Dictionary where keys are q values and values are corresponding data arrays
            
        Note:
            For general partitioning by any column, see filters.partition_by()
        """
        q_vals = raw_data[:, 3]  # q is column 3
        unique_qs = np.unique(q_vals)
        
        # Use dictionary comprehension for vectorized grouping
        return {int(q): raw_data[q_vals == q] for q in unique_qs} 