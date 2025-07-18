import altair as alt
from sympy import prime, primerange, isprime
from factorsums.archive.find_sum_bases import find_sum_bases
from factorsums.archive.number_partition import FactorSumPartition
import numpy as np
import pandas as pd

def is_twin_prime(n):
    """
    Check if n is part of a twin prime pair.
    Returns: (is_twin, is_lower) where is_lower is True if n is the lower of the pair
    """
    if not isprime(n):
        return False, False
    
    if isprime(n + 2):
        return True, True
    if isprime(n - 2):
        return True, False
    return False, False

def plot_base_pairs(n):
    """
    Plot valid base pairs (p,q) for a given n, with color indicating the sum of powers.
    Returns Altair chart.
    """
    # Get valid base pairs
    valid_pairs = find_sum_bases(n)
    
    # Create a partition object to get power information
    partition = FactorSumPartition(n)
    
    # Prepare data for plotting
    data = []
    
    for p, q in valid_pairs:
        # Get the partition for this base pair
        parts = partition.get_partitions(p, q)
        if parts:
            # Use the first valid partition's powers
            j, k, l, m = parts[0].powers
            power_sum = j + k + l + m
            data.append({
                'p': p,
                'q': q,
                'power_sum': power_sum,
                'powers': f'({j},{k},{l},{m})'
            })
    
    if not data:
        return alt.Chart(pd.DataFrame()).mark_text(text="No valid base pairs found").properties(
            title=f'No Valid Base Pairs for n={n}'
        )
    
    df = pd.DataFrame(data)
    
    # Create scatter plot
    chart = alt.Chart(df).mark_circle(size=100, opacity=0.7).encode(
        x=alt.X('p:Q', title='Base p'),
        y=alt.Y('q:Q', title='Base q'),
        color=alt.Color('power_sum:Q', 
                       title='Sum of Powers (j+k+l+m)',
                       scale=alt.Scale(scheme='viridis')),
        tooltip=['p', 'q', 'power_sum', 'powers']
    ).properties(
        title=f'Valid Base Pairs (p,q) for n={n}',
        width=400,
        height=400
    )
    
    # Add text labels
    text = alt.Chart(df).mark_text(
        align='left',
        baseline='middle',
        dx=5,
        fontSize=10
    ).encode(
        x='p:Q',
        y='q:Q',
        text='powers:N'
    )
    
    return (chart + text).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

def plot_base_pair_matrix(max_n=50):
    """
    Create a heatmap showing which prime pairs are valid bases for each n.
    Returns Altair chart.
    """
    # Get all primes up to max_n
    primes = list(primerange(2, max_n + 1))
    
    # Create a matrix to store results
    matrix_data = []
    
    # For each prime n, find valid base pairs
    for n in primes:
        valid_pairs = find_sum_bases(n)
        for p, q in valid_pairs:
            matrix_data.append({
                'p': p,
                'q': q,
                'valid': 1
            })
            matrix_data.append({
                'p': q,
                'q': p,
                'valid': 1
            })
    
    if not matrix_data:
        return alt.Chart(pd.DataFrame()).mark_text(text="No valid pairs found").properties(
            title='No Valid Base Pairs Found'
        )
    
    df = pd.DataFrame(matrix_data)
    
    # Create heatmap
    chart = alt.Chart(df).mark_rect().encode(
        x=alt.X('p:O', title='Prime q'),
        y=alt.Y('q:O', title='Prime p'),
        color=alt.Color('valid:Q', 
                       title='Valid Pair',
                       scale=alt.Scale(scheme='blues'))
    ).properties(
        title='Valid Base Pairs (p,q) for Prime Numbers',
        width=400,
        height=400
    )
    
    return chart

def plot_power_pairs(n, max_power=10):
    """
    Plot base pairs (p,q) with colors indicating their power pairs (j,k,l,m).
    The color intensity represents the sum of powers (j+k+l+m).
    Returns Altair chart.
    """
    # Get valid base pairs
    valid_pairs = find_sum_bases(n)
    
    # Create a partition object to get power information
    partition = FactorSumPartition(n)
    
    # Prepare data for plotting
    data = []
    
    for p, q in valid_pairs:
        # Get the partition for this base pair
        parts = partition.get_partitions(p, q)
        if parts:
            # Use the first valid partition's powers
            j, k, l, m = parts[0].powers
            power_sum = j + k + l + m
            data.append({
                'p': p,
                'q': q,
                'power_sum': power_sum,
                'powers': f'({j},{k},{l},{m})'
            })
    
    if not data:
        return alt.Chart(pd.DataFrame()).mark_text(text="No valid power pairs found").properties(
            title=f'No Valid Power Pairs for n={n}'
        )
    
    df = pd.DataFrame(data)
    
    # Create scatter plot
    chart = alt.Chart(df).mark_circle(size=100, opacity=0.7).encode(
        x=alt.X('p:Q', title='Base p'),
        y=alt.Y('q:Q', title='Base q'),
        color=alt.Color('power_sum:Q', 
                       title='Sum of Powers (j+k+l+m)',
                       scale=alt.Scale(scheme='viridis')),
        tooltip=['p', 'q', 'power_sum', 'powers']
    ).properties(
        title=f'Base Pairs and Their Powers for n={n}',
        width=500,
        height=400
    )
    
    # Add text labels
    text = alt.Chart(df).mark_text(
        align='left',
        baseline='middle',
        dx=5,
        fontSize=10
    ).encode(
        x='p:Q',
        y='q:Q',
        text='powers:N'
    )
    
    return (chart + text).configure_axis(
        grid=True,
        gridOpacity=0.3
    )

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Plot results of find_sum_bases for prime numbers using Altair',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--n', type=int, required=True,
                       help='Number to find base pairs for')
    parser.add_argument('--matrix-only', action='store_true',
                       help='Only generate the matrix plot')
    parser.add_argument('--scatter-only', action='store_true',
                       help='Only generate the scatter plot')
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Output directory for HTML files')
    
    args = parser.parse_args()
    
    # Create output directory
    import os
    os.makedirs(args.output_dir, exist_ok=True)
    
    if not args.matrix_only:
        print(f"Generating base pair plot for n={args.n}...")
        chart = plot_base_pairs(args.n)
        output_file = os.path.join(args.output_dir, f'sum_bases_plot_n{args.n}.html')
        chart.save(output_file)
        print(f"Base pair plot saved as '{output_file}'")
    
    if not args.scatter_only:
        print("Generating matrix plot...")
        chart = plot_base_pair_matrix(min(args.n, 50))  # Limit matrix size for readability
        output_file = os.path.join(args.output_dir, 'sum_bases_matrix.html')
        chart.save(output_file)
        print(f"Matrix plot saved as '{output_file}'")

if __name__ == "__main__":
    main() 