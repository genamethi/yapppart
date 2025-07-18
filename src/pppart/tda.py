import numpy as np
from typing import Dict, List, Tuple, Union, Optional
from .spaces import EuclideanSpaces, qSpaceClass


def get_adjacent_mtx(data: Union[List[Tuple], np.ndarray], 
                    depth: int = 0, 
                    norm: str = 'std_norm',
                    max_k: int = None,
                    **kwargs) -> Union[np.ndarray, Dict]:
    """Build adjacency matrix for persistent homology computation.
    
    Args:
        data: List of (n, p, j, q, k) tuples or numpy array
        depth: 0 for full matrix, 1 for q-grouped matrices
        norm: Normalization method ('std_norm', 'mm_norm')
        max_k: Optional stop condition for q-adic chain length
        **kwargs: Additional arguments
    
    Returns:
        Adjacency matrix(ces) satisfying M_ij >= max(M_ii, M_jj)
    """
    # Convert to numpy array if needed
    if isinstance(data, list):
        data = np.array(data)
    
    if depth == 0:
        # For Euclidean/global, drop column p (index 1)
        data_no_p = data[:, [0, 2, 3, 4]]  # (n, j, q, k)
        
        # Use EuclideanSpaces class
        euclidean = EuclideanSpaces()
        norm_data = euclidean.get_euc_norm(data_no_p, norm)
        return euclidean.dist_mtx(norm_data)
    
    elif depth == 1:
        # Separate matrices for each q-group
        q_space = qSpaceClass()
        grouped_data = q_space.groupby_q(data)
        
        # Use dictionary comprehension for vectorized q-adic matrices
        q_matrices = {q: q_space.dist_mtx(q_data, q, max_k) 
                     for q, q_data in grouped_data.items()}
        
        return q_matrices
    
    else:
        raise ValueError(f"Unsupported depth: {depth}")




# Test functions
def test_normalization():
    """Test normalization functions."""
    data = np.array([[1000, 2, 3, 5], [2000, 3, 4, 7], [1500, 1, 2, 11]])
    euclidean = EuclideanSpaces()
    
    print("Original data:")
    print(data)
    print("\nStandard normalized:")
    print(euclidean.get_euc_norm(data, 'std_norm'))
    print("\nMinmax normalized:")
    print(euclidean.get_euc_norm(data, 'mm_norm'))

def test_distance_matrices():
    """Test distance matrix computations."""
    data = np.array([[1000, 2, 3, 5], [2000, 3, 4, 7], [1500, 1, 2, 11]])
    euclidean = EuclideanSpaces()
    norm_data = euclidean.get_euc_norm(data, 'std_norm')
    
    print("Euclidean distance matrix:")
    print(euclidean.dist_mtx(norm_data))
    
    print("\nQ-adic distance matrix (q=2):")
    q_space = qSpaceClass()
    print(q_space.dist_mtx(data, 2))

def test_depth_1():
    """Test depth=1 adjacency matrices."""
    # Create test data with different q values
    data = np.array([
        [1000, 2, 3, 5, 2],  # q=5
        [2000, 2, 4, 5, 3],  # q=5
        [1500, 2, 1, 7, 2],  # q=7
        [2500, 2, 2, 7, 4],  # q=7
        [3000, 2, 3, 11, 1]  # q=11
    ])
    
    print("Test data:")
    print(data)
    print("\nGrouped by q:")
    q_space = qSpaceClass()
    grouped = q_space.groupby_q(data)
    for q, q_data in grouped.items():
        print(f"q={q}: {len(q_data)} partitions")
        print(q_data)
    
    print("\nDepth=1 adjacency matrices:")
    q_matrices = q_space.get_adjacent_mtx(data, depth=1)
    for q, matrix in q_matrices.items():
        print(f"\nq={q} adjacency matrix:")
        print(matrix)

# def test_giotto_ph_integration():
#     """Test integration with giotto-ph for persistent homology."""
#     try:
#         from gph import ripser_parallel
#         from gtda.homology._utils import _postprocess_diagrams
#         
#         # Create test data with more realistic prime partition structure
#         data = np.array([
#             [1000, 2, 3, 5, 2],   # n=1000 = 2^3 + 5^2
#             [2000, 2, 4, 7, 3],   # n=2000 = 2^4 + 7^3  
#             [1500, 2, 1, 11, 2],  # n=1500 = 2^1 + 11^2
#             [2500, 2, 2, 13, 4],  # n=2500 = 2^2 + 13^4
#             [3000, 2, 3, 17, 1]   # n=3000 = 2^3 + 17^1
#         ])
#         
#         print("Test data (n, p, j, q, k):")
#         print(data)
#         
#         # Build adjacency matrix using our function
#         q_space = qSpaceClass()
#         adj_matrix = q_space.get_adjacent_mtx(data, depth=0, norm='std_norm')
#         print(f"\nAdjacency matrix shape: {adj_matrix.shape}")
#         print("Adjacency matrix:")
#         print(adj_matrix)
#         
#         # Check giotto-ph constraint
#         diag_max = np.max(np.diag(adj_matrix))
#         off_diag_min = np.min(adj_matrix[adj_matrix > 0])
#         print(f"\nConstraint check: diag_max={diag_max:.6f}, off_diag_min={off_diag_min:.6f}")
#         print(f"Constraint satisfied: {off_diag_min >= diag_max}")
#         
#         # Use giotto-ph to compute persistent homology
#         print("\nComputing persistent homology with giotto-ph...")
#         dgm = ripser_parallel(adj_matrix, maxdim=2)
#         
#         print(f"Persistence diagram keys: {list(dgm.keys())}")
#         print(f"Number of diagrams: {len(dgm['dgms'])}")
#         
#         # Convert to gtda format for visualization
#         dgm_gtda = _postprocess_diagrams([dgm['dgms']], "ripser", (0, 1, 2), np.inf, True)[0]
#         print(f"GTDA diagram shape: {dgm_gtda.shape}")
#         
#         return True
#         
    except ImportError as e:
        print(f"Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"Error in giotto-ph integration: {e}")
        return False

if __name__ == "__main__":
    test_normalization()
    print("\n" + "="*50 + "\n")
    test_distance_matrices()
    print("\n" + "="*50 + "\n")
    test_depth_1()
    print("\n" + "="*50 + "\n")
    test_giotto_ph_integration() 