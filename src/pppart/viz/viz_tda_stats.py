import numpy as np
import altair as alt
import os
import argparse
from typing import Optional

# Import our modular analysis functions and config
from pppart.analysis import (
    get_stalks, get_sheaves, get_basis, calc_coeffs, 
    get_obstructions, chain_del, get_stats, select_zero_rows,
    gen_persistent_homology_data
)
from pppart.utils import get_config

def load_data(filepath: Optional[str] = None) -> np.ndarray:
    """
    Loads partition data as a NumPy array.
    
    Args:
        filepath (str): Path to the CSV file
        
    Returns:
        np.ndarray: Data array with columns [n, p, j, q, k]
    """
    if filepath is None:
        config = get_config()
        filepath = config.default_data_path
    
    # Load CSV and convert to NumPy array
    data = np.loadtxt(filepath, delimiter=',', skiprows=1, dtype=int)
    return data


def analyze_partitions_modular(data: np.ndarray) -> np.ndarray:
    """
    Analyzes partitions using our modular functions.
    Returns n-interval data in a structured format.
    """
    # Get all non-zero partitions (where p != 0)
    non_zero_data = get_stalks(data, 'p', 'gt', 0)
    
    # Get basis (consecutive pairs)
    basis = get_basis(non_zero_data)
    
    # Get coefficients (gap lengths)
    coeffs = calc_coeffs(non_zero_data)
    
    # Create structured array for plotting
    n_points = len(coeffs)
    interval_data = np.empty(n_points, dtype=[('n', 'i8'), ('prime', 'i8'), ('n_interval', 'i8')])
    
    # Fill the structured array
    interval_data['n'] = non_zero_data[1:, 0]  # Skip first point since we need pairs
    interval_data['prime'] = non_zero_data[1:, 1]  # Use p values
    interval_data['n_interval'] = coeffs
    
    return interval_data


def analyze_n_interval_spread_modular(data: np.ndarray, bin_size: int = 1000) -> dict:
    """
    Analyzes n-interval spread using modular functions.
    """
    interval_data = analyze_partitions_modular(data)
    
    # Get n values and their ranges
    n_values = interval_data['n']
    min_n = np.min(n_values)
    max_n = np.max(n_values)
    
    # Create bins
    bins = np.arange(min_n, max_n + bin_size, bin_size)
    bin_labels = [f'{i}-{i+bin_size-1}' for i in bins[:-1]]
    
    # Count distinct intervals per bin
    spread_data = {}
    for i, (start, end) in enumerate(zip(bins[:-1], bins[1:])):
        # Get data in this bin
        bin_data = get_sheaves(interval_data, 'n', start, end)
        if len(bin_data) > 0:
            # Count distinct n_interval values
            distinct_intervals = len(np.unique(bin_data['n_interval']))
            spread_data[bin_labels[i]] = distinct_intervals
    
    return spread_data


def analyze_zero_partitions_modular(data: np.ndarray) -> dict:
    """
    Analyzes zero partitions using modular functions.
    """
    zero_data = select_zero_rows(data)
    return get_stats(zero_data, 'n')


def plot_prime_n_intervals_modular(data: np.ndarray, output_filename: str):
    """Generate prime N intervals plot using modular analysis functions."""
    # Get stats for n column
    n_stats = get_stats(data, 'n')
    
    # Generate interval boundaries based on stats
    n_min = int(n_stats['min'])
    n_max = int(n_stats['max'])
    interval_size = max(1, (n_max - n_min) // 20)  # 20 intervals
    
    intervals = []
    for i in range(n_min, n_max, interval_size):
        intervals.append([i, i + interval_size])
    
    intervals_array = np.array(intervals)
    
    # Get obstructions (data within intervals)
    obstructions = get_obstructions(data, intervals_array)
    
    # Prepare data for Altair
    chart_data = []
    for i, obs in enumerate(obstructions):
        interval_midpoint = (intervals[i][0] + intervals[i][1]) / 2
        chart_data.append({
            'interval_midpoint': interval_midpoint,
            'count': len(obs)
        })
    
    if not chart_data:
        chart = alt.Chart().mark_text(text="No data available").properties(
            title="No Interval Data Available"
        )
    else:
        # Create bar chart
        chart = alt.Chart(chart_data).mark_bar(opacity=0.7).encode(
            x=alt.X('interval_midpoint:Q', title='Prime N Value (Interval Midpoints)'),
            y=alt.Y('count:Q', title='Count of Data Points'),
            tooltip=['interval_midpoint', 'count']
        ).properties(
            title='Distribution of Prime Partitions by N Intervals',
            width=600,
            height=400
        )
    
    # Save chart
    config = get_config()
    output_path = os.path.join(config.output_dir, output_filename) if not os.path.isabs(output_filename) else output_filename
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    chart.save(output_path)
    print(f"Saved prime N intervals plot to {output_path}")


def plot_zero_partition_distribution(data: np.ndarray, output_filename: str):
    """Generate distribution plot of zero partition primes."""
    # Select zero partition rows
    zero_data = select_zero_rows(data)
    
    if len(zero_data) == 0:
        chart = alt.Chart().mark_text(text="No zero partitions found").properties(
            title="No Zero Partitions Available"
        )
    else:
        # Get statistics
        zero_stats = get_stats(zero_data, 'n')
        
        # Prepare data for histogram
        n_values = zero_data[:, 0]  # n column
        
        # Create histogram data
        hist_data = []
        for n in n_values:
            hist_data.append({'n_value': n})
        
        # Create histogram
        chart = alt.Chart(hist_data).mark_bar(opacity=0.7, color='steelblue').encode(
            x=alt.X('n_value:Q', 
                   title='Prime N Values (Zero Partitions)',
                   bin=alt.Bin(maxbins=30)),
            y=alt.Y('count():Q', title='Frequency'),
            tooltip=['count()']
        ).properties(
            title='Distribution of Zero-Partition Primes',
            width=600,
            height=400
        )
        
        # Add statistics text
        stats_text = f"Count: {zero_stats['count']}\nMean: {zero_stats['mean']:.2f}\nStd: {zero_stats['std']:.2f}"
        text_chart = alt.Chart().mark_text(
            text=stats_text,
            align='left',
            baseline='top',
            fontSize=12,
            color='black'
        ).encode(
            x=alt.value(10),
            y=alt.value(10)
        )
        
        chart = chart + text_chart
    
    # Save chart
    config = get_config()
    output_path = os.path.join(config.output_dir, output_filename) if not os.path.isabs(output_filename) else output_filename
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    chart.save(output_path)
    print(f"Saved zero partition distribution plot to {output_path}")


def plot_persistent_homology_barcode(distance_matrix: np.ndarray, output_filename: str):
    """Generate persistent homology barcode (placeholder implementation)."""
    # This is a placeholder - actual PH computation would use giotto-ph
    
    # Mock barcode data for demonstration
    n_bars = min(20, len(distance_matrix))
    birth_times = np.sort(np.random.uniform(0, 1, n_bars))
    death_times = birth_times + np.random.exponential(0.5, n_bars)
    
    # Prepare data for Altair
    barcode_data = []
    for i, (birth, death) in enumerate(zip(birth_times, death_times)):
        barcode_data.append({
            'birth': birth,
            'death': death,
            'index': i
        })
    
    if not barcode_data:
        chart = alt.Chart().mark_text(text="No barcode data available").properties(
            title="No Persistent Homology Data Available"
        )
    else:
        # Create barcode chart
        chart = alt.Chart(barcode_data).mark_rule(strokeWidth=2, color='blue').encode(
            x=alt.X('birth:Q', title='Filtration Parameter'),
            x2=alt.X2('death:Q'),
            y=alt.Y('index:O', title='Barcode Index'),
            tooltip=['birth', 'death', 'index']
        ).properties(
            title='Persistent Homology Barcode (Placeholder)',
            width=600,
            height=400
        )
    
    # Save chart
    config = get_config()
    output_path = os.path.join(config.output_dir, output_filename) if not os.path.isabs(output_filename) else output_filename  
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    chart.save(output_path)
    print(f"Saved persistent homology barcode to {output_path}")


def main():
    """
    Main function with command-line interface.
    """
    parser = argparse.ArgumentParser(
        description='Generate TDA plots using modular analysis functions and Altair.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    config = get_config()
    
    parser.add_argument('--data-file', type=str, default=config.default_data_path,
                        help='Path to partition data CSV file')
    parser.add_argument('--output-dir', type=str, default='output',
                        help='Output directory for plots')
    parser.add_argument('--all', action='store_true',
                        help='Generate all plots')
    parser.add_argument('--n-intervals', action='store_true',
                        help='Generate N-intervals plot')
    parser.add_argument('--zero-partitions', action='store_true',
                        help='Generate zero partition distribution plot')
    parser.add_argument('--persistent-homology', action='store_true',
                        help='Generate persistent homology barcode (placeholder)')
    
    args = parser.parse_args()
    
    # Load data
    try:
        data = load_data(args.data_file)
        print(f"Loaded data with {len(data)} rows")
    except FileNotFoundError:
        print(f"Error: Could not find data file {args.data_file}")
        return
    
    # Create output directory
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    
    # Generate plots based on arguments
    if args.n_intervals or args.all:
        plot_prime_n_intervals_modular(data, f"{args.output_dir}/prime_n_intervals.html")
    
    if args.zero_partitions or args.all:
        plot_zero_partition_distribution(data, f"{args.output_dir}/zero_partition_distribution.html")
    
    if args.persistent_homology or args.all:
        # Generate distance matrix for persistent homology
        distance_matrix, _ = gen_persistent_homology_data(data)
        plot_persistent_homology_barcode(distance_matrix, f"{args.output_dir}/persistent_homology_barcode.html")
    
    # Print some statistics
    print("\n--- Data Statistics ---")
    print(f"Total rows: {len(data)}")
    
    zero_stats = analyze_zero_partitions_modular(data)
    print(f"Zero partitions: {zero_stats['count']} ({zero_stats['count']/len(data)*100:.2f}%)")
    
    if args.all or args.n_intervals:
        spread_data = analyze_n_interval_spread_modular(data)
        print(f"N-interval spread analysis: {len(spread_data)} bins")


if __name__ == "__main__":
    main() 