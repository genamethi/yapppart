import altair as alt
import re
import sys
import os
from datetime import datetime
import numpy as np

def parse_tqdm_log(log_filepath):
    data = []
    # Updated Regex to capture iterations, total, elapsed time, and rate
    # It now accounts for the prefix message and handles the remaining time string between elapsed and rate.
    # Example line: Generating prime partitions: 100%|███████████████████| 16/16 [00:09<00:00, 1.77batch/s]
    regex_pattern = r'.*?(\d+)/(\d+)\s*\[((?:\d{2}:)?\d{2}:\d{2})<(.*?),\s*([\d.]+)([a-zA-Z\/]+)\]'

    try:
        with open(log_filepath, 'r') as f:
            for line in f:
                match = re.search(regex_pattern, line)
                if match:
                    completed_batches = int(match.group(1))
                    total_batches = int(match.group(2))
                    elapsed_time_str = match.group(3)
                    # We don't need match.group(4) (remaining time string) for plotting
                    rate_value = float(match.group(5))
                    rate_unit = match.group(6)

                    # Convert elapsed_time_str to seconds
                    parts = [int(p) for p in elapsed_time_str.split(':')]
                    elapsed_seconds = 0
                    if len(parts) == 3: # HH:MM:SS
                        elapsed_seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
                    elif len(parts) == 2: # MM:SS
                        elapsed_seconds = parts[0] * 60 + parts[1]
                    elif len(parts) == 1: # SS
                        elapsed_seconds = parts[0]

                    data.append({
                        'completed_batches': completed_batches,
                        'total_batches': total_batches,
                        'elapsed_seconds': elapsed_seconds,
                        'rate_value': rate_value,
                        'rate_unit': rate_unit
                    })
    except FileNotFoundError:
        print(f"Error: Log file not found at {log_filepath}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"An error occurred while parsing log file {log_filepath}: {e}", file=sys.stderr)
        return []

    return data

def create_progress_chart(data):
    """
    Create Altair chart showing progress over time.
    """
    if not data:
        return alt.Chart().mark_text(text="No data available").properties(
            title="No Progress Data Available"
        )
    
    # Normalize rate to batch/s
    for row in data:
        if 's/batch' in row['rate_unit']:
            row['rate_batch_per_s'] = 1 / row['rate_value']
        else:
            row['rate_batch_per_s'] = row['rate_value']
    
    # Create DataFrame-like structure for Altair
    chart_data = []
    for row in data:
        chart_data.append({
            'elapsed_seconds': row['elapsed_seconds'],
            'rate_batch_per_s': row['rate_batch_per_s'],
            'completed_batches': row['completed_batches'],
            'metric': 'Rate (batch/s)',
            'value': row['rate_batch_per_s']
        })
        chart_data.append({
            'elapsed_seconds': row['elapsed_seconds'],
            'rate_batch_per_s': row['rate_batch_per_s'],
            'completed_batches': row['completed_batches'],
            'metric': 'Batches Processed',
            'value': row['completed_batches']
        })
    
    # Create the chart
    chart = alt.Chart(chart_data).mark_line(point=True).encode(
        x=alt.X('elapsed_seconds:Q', title='Elapsed Time (seconds)'),
        y=alt.Y('value:Q', title='Value'),
        color=alt.Color('metric:N', 
                       title='Metric',
                       scale=alt.Scale(domain=['Rate (batch/s)', 'Batches Processed'],
                                      range=['blue', 'orange'])),
        tooltip=['elapsed_seconds', 'value', 'metric']
    ).properties(
        title=f'Prime Partition Generation Progress (Total Primes: {data[-1]["total_batches"] * 1000:,})',
        width=600,
        height=400
    )
    
    return chart.configure_axis(
        grid=True,
        gridOpacity=0.3
    )

def main():
    if len(sys.argv) < 3:
        print("Usage: python viz_batch_rate.py <log_file_path> <output_html_path>", file=sys.stderr)
        sys.exit(1)

    log_file = sys.argv[1]
    output_html = sys.argv[2]

    data = parse_tqdm_log(log_file)

    if data:
        chart = create_progress_chart(data)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_html)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # Add timestamp to the filename
        timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(output_html))[0]
        extension = os.path.splitext(output_html)[1]
        timestamped_output_html = os.path.join(output_dir, f"{base_name}{timestamp}{extension}")

        chart.save(timestamped_output_html)
        print(f"Chart saved to {timestamped_output_html}")
    else:
        print(f"No valid tqdm progress data found in {log_file} to plot.", file=sys.stderr)

if __name__ == "__main__":
    main() 