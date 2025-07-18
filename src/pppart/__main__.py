import argparse
import psutil
import os
from . import core, utils
from .viz.viz_ppp_counts import plot_partitions_count
from sage.all import *

def main():
    parser = argparse.ArgumentParser(
        description='Find prime factor sums (n = p^j + q^k) for a batch of primes.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('--num-primes', type=int, default=1000, help='Number of primes to process, starting from 2.')
    config = utils.get_config()
    parser.add_argument('--output-file', type=str, help='Path to the output CSV file (overrides default behavior).')
    parser.add_argument('--batch-size', type=int, default=config.default_batch_size, help='Number of primes to process in each batch.')
    parser.add_argument('--num-processes', type=int, default=psutil.cpu_count(logical=False), help='Number of worker processes to use.')
    parser.add_argument('--generate-viz', action='store_true', help='Generate partition count visualization after processing.')
    parser.add_argument('--viz-only', action='store_true', help='Only generate visualization from existing data file, skip data generation.')
    parser.add_argument('--resume', action='store_true', help=f'Append {config.default_data_file} with --num-primes or default more primes')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode - skip actual data generation and file operations.')
    
    args = parser.parse_args()
    
    # Determine output file path based on mode
    if args.output_file:
        # User specified output file - use as is
        output_file = args.output_file
        if not os.path.isabs(output_file):
            output_file = os.path.join(config.output_dir, output_file)
    elif args.resume:
        # Resume mode: use the actual data file
        output_file = config.default_data_path
    else:
        # Default mode: use temp directory with timestamped filename
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"partition_data_{timestamp}.csv"
        output_file = os.path.join(config.temp_dir, temp_filename)

    # --- Visualization Only Mode ---
    if args.viz_only:
        if not os.path.exists(output_file):
            print(f"Error: Data file not found at {output_file}")
            return
        print("Generating partition count visualization from existing data...")
        if not args.test_mode:
            plot_partitions_count(os.path.join(config.data_dir, output_file) if not os.path.isabs(output_file) else output_file)
        return
    
    # --- Input Validation ---
    if args.num_primes % args.batch_size != 0:
        parser.error(
            f"num_primes ({args.num_primes}) must be strictly divisible by "
            f"batch_size ({args.batch_size})."
        )

    if args.resume:
        if args.test_mode:
            master_data_dict = {2: {(2, 1, 0, 0)}}  # Mock data for testing
        else:
            master_data_dict = core.generate_partitions(args.num_primes, args.batch_size, args.num_processes, True, output_file)
    else:
         # --- Data Generation ---
        print(f"Generating partitions for the first {args.num_primes} primes...")
        if args.test_mode:
            print("We need to add a legit test with real data.")
        else:
            master_data_dict = core.generate_partitions(args.num_primes, args.batch_size, args.num_processes, False)

    # --- Data Processing and Output ---
    if not master_data_dict:
        print("No results generated.")
        return

    # Now that all data is correctly aggregated, write it to the outputs
    if not args.test_mode:
        utils.write_csv(master_data_dict, output_file, append_mode=args.resume)
        utils.print_summary(master_data_dict, args.num_primes)
    
    # --- Visualization ---
    if args.generate_viz:
        print("Generating partition count visualization...")
        if not args.test_mode:
            plot_partitions_count(os.path.join(config.data_dir, output_file) if not os.path.isabs(output_file) else output_file)

if __name__ == "__main__":
    main() 