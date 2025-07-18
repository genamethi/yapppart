"""Chain complex analysis for prime partition data."""

import numpy as np
from typing import List


def get_obstructions(raw_data: np.ndarray, gap_boundaries: np.ndarray) -> List[np.ndarray]:
    """Probes the data within specified intervals. Computes the preimage
    of each interval under the projection to the n-coordinate.

    Args:
        raw_data (np.ndarray): The full, original dataset.
        gap_boundaries (np.ndarray): A 2D array where each row is a
                                     [start_n, end_n] pair defining an interval.

    Returns:
        List[np.ndarray]: A list of numpy arrays. Each array contains
                          the data points within the corresponding interval.
    """
    if gap_boundaries.ndim != 2 or gap_boundaries.shape[1] != 2:
        raise ValueError("gap_boundaries must be a 2D array with shape (num_gaps, 2).")

    # Extract the 'n' column from the raw data
    n_values = raw_data[:, 0]

    # Use broadcasting to create a boolean mask.
    # The mask will be of shape (len(n_values), len(gap_boundaries)).
    # mask[i, j] is True if n_values[i] is within the j-th interval.
    in_gap_mask = (n_values[:, np.newaxis] > gap_boundaries[:, 0]) & \
                  (n_values[:, np.newaxis] < gap_boundaries[:, 1])

    # Find the index of the interval each data point belongs to.
    # `np.argmax` along axis 1 will find the first 'True' for each row.
    # We add 1 to make it 1-based, 0 means it belongs to no interval.
    gap_indices = np.argmax(in_gap_mask, axis=1) * np.any(in_gap_mask, axis=1)

    # Filter for data points that are within any interval
    data_in_any_gap = raw_data[gap_indices > 0]
    gap_indices_in_any_gap = gap_indices[gap_indices > 0]

    # A more efficient, vectorized way to split the array without a Python loop.
    # Find the unique gap indices and where they start.
    unique_gaps, split_indices = np.unique(gap_indices_in_any_gap, return_index=True)

    # `np.split` will create the list of arrays for us.
    # We sort the split_indices to ensure the output list is ordered by gap.
    result_list = np.split(data_in_any_gap, split_indices[1:])

    return result_list


def get_basis(filtered_data: np.ndarray) -> np.ndarray:
    """Computes the boundary operator on ordered n-values. Extracts
    consecutive pairs to define intervals.

    Args:
        filtered_data (np.ndarray): A subset of the raw data, sorted by 'n'.

    Returns:
        np.ndarray: A 2D array of shape (N-1, 2) where each row is a
                    [gap_start_n, gap_end_n] pair. Returns an empty
                    array if there are not enough data points to form a gap.
    """
    if filtered_data.shape[0] < 2:
        return np.array([], dtype=int).reshape(0, 2)

    # Ensure data is sorted by 'n' to calculate gaps correctly
    sorted_data = filtered_data[filtered_data[:, 0].argsort()]
    
    # Select the 'n' column (index 0)
    n_values = sorted_data[:, 0]
    
    # Create pairs of consecutive n-values to define the gap boundaries
    gap_boundaries = np.lib.stride_tricks.as_strided(
        n_values,
        shape=(n_values.shape[0] - 1, 2),
        strides=(n_values.strides[0], n_values.strides[0])
    )

    return gap_boundaries


def calc_coeffs(filtered_data: np.ndarray) -> np.ndarray:
    """Computes the lengths of gaps between consecutive n-values.
    The differential operator on the ordered sequence.

    Args:
        filtered_data (np.ndarray): A subset of the raw data, sorted by 'n'.

    Returns:
        np.ndarray: A 1D array of gap sizes (differences between consecutive n-values).
    """
    if filtered_data.shape[0] < 2:
        return np.array([], dtype=int)

    # Ensure data is sorted by 'n' to calculate gaps correctly
    sorted_data = filtered_data[filtered_data[:, 0].argsort()]
    
    # Select the 'n' column (index 0)
    n_values = sorted_data[:, 0]
    
    # Calculate the difference between consecutive n values
    gaps = np.diff(n_values)
    
    return gaps


def chain_del(basis: np.ndarray, coeffs: np.ndarray) -> np.ndarray:
    """Computes the boundary map ∂: C₁ → C₀.
    ∂(Σcᵢ[aᵢ,bᵢ)) = Σcᵢ(bᵢ - aᵢ)

    Args:
        basis (np.ndarray): 2D array of interval pairs [aᵢ, bᵢ]
        coeffs (np.ndarray): 1D array of coefficients cᵢ

    Returns:
        np.ndarray: The boundary values (bᵢ - aᵢ) weighted by coefficients
    """
    if basis.shape[0] != coeffs.shape[0]:
        raise ValueError("Basis and coefficients must have same length")
    
    # Compute the differences (bᵢ - aᵢ) for each interval
    interval_lengths = basis[:, 1] - basis[:, 0]
    
    # Weight by coefficients
    weighted_lengths = interval_lengths * coeffs
    
    return weighted_lengths 