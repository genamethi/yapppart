"""Statistical analysis and random matrix generation for prime partition data."""

import numpy as np
from typing import Literal, Dict
from sage.all import *


def get_stats(data: np.ndarray, col: Literal['n', 'p', 'j', 'q', 'k'] = 'n') -> Dict:
    """Computes basic statistical measures for a specified column.

    Args:
        data (np.ndarray): The data array with columns [n, p, j, q, k].
        col (str): The column to analyze ('n', 'p', 'j', 'q', 'k').

    Returns:
        dict: Dictionary containing mean, std, min, max, and count.
    """
    col_map = {'n': 0, 'p': 1, 'j': 2, 'q': 3, 'k': 4}
    if col not in col_map:
        raise ValueError(f"Invalid column name '{col}'. Must be one of {list(col_map.keys())}")
    col_idx = col_map[col]

    column_data = data[:, col_idx]
    
    stats = {
        'mean': np.mean(column_data),
        'std': np.std(column_data),
        'min': np.min(column_data),
        'max': np.max(column_data),
        'count': len(column_data)
    }
    
    return stats


def gen_gaussian_matrix_sage(size: int, std: float = 1.0):
    """Generate a random matrix using SageMath's Gaussian distribution.
    
    Args:
        size: Matrix size (size x size)
        std: Standard deviation of the Gaussian distribution (mean=0)
        
    Returns:
        SageMath matrix with Gaussian random entries
    """
    
    # Create Gaussian distribution with mean=0, std=std
    gaussian = RealDistribution('gaussian', std)
    
    # Generate random matrix
    random_matrix = matrix([[gaussian.get_random_element() for _ in range(size)] 
                           for _ in range(size)])
    
    return random_matrix


def gen_poisson_matrix_sage(size: int, lambda_param: float = 1.0):
    """Generate a random matrix using SageMath's Poisson distribution.
    
    Args:
        size: Matrix size (size x size)
        lambda_param: Lambda parameter for Poisson distribution
        
    Returns:
        SageMath matrix with Poisson random entries
    """
    from sage.all import matrix, RealDistribution
    
    # Create Poisson distribution
    poisson = RealDistribution('poisson', [lambda_param])
    
    # Generate random matrix
    random_matrix = matrix([[poisson.get_random_element() for _ in range(size)] 
                           for _ in range(size)])
    
    return random_matrix


def gen_mtx_from_stats(size: int, stats: Dict, distribution: str = 'gaussian'):
    """Generate a random matrix based on provided statistics.
    
    Args:
        size: Matrix size (size x size)
        stats: Dictionary with statistical properties (mean, std, etc.)
        distribution: Distribution type ('gaussian', 'poisson')
        
    Returns:
        SageMath matrix with random entries following the specified distribution
    """
    if distribution == 'gaussian':
        std = stats.get('std', 1.0)
        return gen_gaussian_matrix_sage(size, std)
    elif distribution == 'poisson':
        lambda_param = stats.get('mean', 1.0)
        return gen_poisson_matrix_sage(size, lambda_param)
    else:
        raise ValueError(f"Unsupported distribution: {distribution}") 