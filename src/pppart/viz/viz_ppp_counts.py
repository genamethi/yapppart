import numpy as np
import altair as alt
import os
from typing import Optional


def plot_partitions_count(data_filename: Optional[str] = None, output_filename="sample/viz/prime_partitions_count_plot.html"):
    """
    Generates a scatter plot of prime numbers vs. their partition counts.
    Primes with zero partitions are highlighted.
    """
    # Default to bundled resource if no data_filename is provided
    if data_filename is None:
        from .. import utils
        config = utils.get_config()
        data_filename = config.default_data_path

    if not os.path.exists(data_filename):
        print(f"Error: Data file not found at {data_filename}")
        return

    # Load data as numpy array
    data = np.loadtxt(data_filename, delimiter=',', skiprows=1, dtype=int)
    
    # Calculate the number of partitions for each unique prime 'n'
    # Group by n and count non-zero partitions (where p != 0)
    unique_ns = np.unique(data[:, 0])  # Column 0 is 'n'
    partition_counts = []
    
    for n in unique_ns:
        n_rows = data[data[:, 0] == n]
        # Count rows where p != 0 (column 1 is 'p')
        count = np.sum(n_rows[:, 1] != 0)
        partition_counts.append(count)
    
    partition_counts = np.array(partition_counts)
    
    # Print frequency table of partition counts
    print("\nFrequency Table of Partition Counts:")
    unique_counts, count_freqs = np.unique(partition_counts, return_counts=True)
    for count, freq in zip(unique_counts, count_freqs):
        print(f"{count}: {freq}")
    print("\n")

    # Generate and print frequency table of zero partitions by n grouping
    print("Frequency Table of Zero Partitions by Number of Digits:")
    zero_partition_ns = unique_ns[partition_counts == 0]
    
    if len(zero_partition_ns) > 0:
        # Define bins based on number of digits
        bins = [0, 10, 100, 1000, 10000, 100000, 1000000]
        labels = ['1-digit', '2-digits', '3-digits', '4-digits', '5-digits', '6-digits']
        
        # Categorize zero partition primes into digit-based bins
        binned_counts = np.zeros(len(labels), dtype=int)
        for i, (start, end) in enumerate(zip(bins[:-1], bins[1:])):
            binned_counts[i] = np.sum((zero_partition_ns >= start) & (zero_partition_ns < end))
        
        for label, count in zip(labels, binned_counts):
            if count > 0:
                print(f"{label}: {count}")
        print("\n")

        # Save frequency table to CSV
        freq_table_output = "sample/viz/zero_partitions_frequency_by_digits.csv"
        os.makedirs(os.path.dirname(freq_table_output), exist_ok=True)
        with open(freq_table_output, 'w') as f:
            f.write("digit_range,count\n")
            for label, count in zip(labels, binned_counts):
                if count > 0:
                    f.write(f"{label},{count}\n")
        print(f"Frequency table saved to {freq_table_output}\n")

    else:
        print("No primes found with zero partitions.")
        print("\n")

    # Create Altair chart
    chart_data = {
        'n': unique_ns,
        'num_partitions': partition_counts
    }
    
    chart = alt.Chart(alt.InlineData(values=[
        {'n': int(n), 'num_partitions': int(count)} 
        for n, count in zip(unique_ns, partition_counts)
    ])).mark_circle(
        size=30,
        color='black'
    ).encode(
        x=alt.X('n:Q', title='Prime Number (n)'),
        y=alt.Y('num_partitions:Q', title='Number of Partitions')
    ).properties(
        title='Number of Partitions for Primes',
        width=600,
        height=400
    )

    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Save chart
    chart.save(output_filename)
    print(f"Plot saved to {output_filename}")

if __name__ == "__main__":
    plot_partitions_count() 