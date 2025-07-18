"""Filtering and partitioning functions for prime partition data."""

import numpy as np
from typing import List, Tuple, Optional, Any


def get_stalks(data: np.ndarray, col_idx: int) -> List[np.ndarray]:
    """Group data by unique values in specified column.
    
    Args:
        data: Input array
        col_idx: Column index to group by
        
    Returns:
        List of arrays, each containing rows with same value in col_idx
    """
    unique_vals = np.unique(data[:, col_idx])
    return [data[data[:, col_idx] == val] for val in unique_vals]


def get_sheaves(data: np.ndarray, col_idx: int) -> Tuple[np.ndarray, List[np.ndarray]]:
    """Group data by unique values and return both unique values and groups.
    
    Args:
        data: Input array
        col_idx: Column index to group by
        
    Returns:
        Tuple of (unique_values, list_of_groups)
    """
    unique_vals = np.unique(data[:, col_idx])
    sheaves = [data[data[:, col_idx] == val] for val in unique_vals]
    return unique_vals, sheaves


def partition_by(data: np.ndarray, col_idx: int, sort_within_groups: bool = False, 
                sort_col: Optional[int] = None) -> List[np.ndarray]:
    """Efficiently partition data by column values using sorted+split approach.
    
    Args:
        data: Input array
        col_idx: Column index to partition by
        sort_within_groups: Whether to sort within each group
        sort_col: Column to sort by within groups (defaults to col_idx)
        
    Returns:
        List of arrays, each containing rows with same value in col_idx
    """
    if sort_col is None:
        sort_col = col_idx
    
    # Sort by partition column first, then by sort column
    sort_keys = (data[:, col_idx], data[:, sort_col])
    sorted_indices = np.lexsort(sort_keys)
    sorted_data = data[sorted_indices]
    
    # Find split points where column values change
    partition_col = sorted_data[:, col_idx]
    split_points = np.where(partition_col[1:] != partition_col[:-1])[0] + 1
    
    # Split into groups using np.split
    groups = np.split(sorted_data, split_points)
    
    if sort_within_groups and sort_col != col_idx:
        groups = [group[np.argsort(group[:, sort_col])] for group in groups]
    
    return groups


def sort_groups_by(groups: List[np.ndarray], col_idx: int) -> List[np.ndarray]:
    """Sort each group by specified column.
    
    Args:
        groups: List of arrays to sort
        col_idx: Column index to sort by
        
    Returns:
        List of sorted arrays
    """
    return [group[np.argsort(group[:, col_idx])] for group in groups]


def sel_zero_rows(data: np.ndarray, col_idx: int) -> np.ndarray:
    """Select rows where specified column equals zero.
    
    Args:
        data: Input array
        col_idx: Column index to check for zero
        
    Returns:
        Array containing only rows where col_idx equals zero
    """
    return data[data[:, col_idx] == 0]


# Legacy alias for backward compatibility
def pullby_val(data: np.ndarray, col_idx: int, sort_within_groups: bool = False) -> List[np.ndarray]:
    """Alias for partition_by for backward compatibility."""
    return partition_by(data, col_idx, sort_within_groups) 