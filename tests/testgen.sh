#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Default values
NUM_PRIMES_DEFAULT=5000
BATCH_SIZE_DEFAULT=""
NUM_PROCESSES_DEFAULT=""
OUTPUT_DIR_DEFAULT="pppart_data" # New default for output directory

# Function to display help message
show_help() {
    echo "Usage: $(basename "$0") [-n NUM_PRIMES] [-b BATCH_SIZE] [-c NUM_PROCESSES] [-o OUTPUT_DIR] [-h]"
    echo ""
    echo "Options:"
    echo "  -n NUM_PRIMES      Number of primes to generate test data for (default: ${NUM_PRIMES_DEFAULT})"
    echo "  -b BATCH_SIZE      Optional batch size for multiprocessing (default: 250 in Python script)"
    echo "  -c NUM_PROCESSES   Optional number of threads to use (default: physical cores in Python script)"
    echo "  -o OUTPUT_DIR      Directory to save logs and plots (default: ${OUTPUT_DIR_DEFAULT})"
    echo "  -h, --help         Display this help message"
    echo ""
    echo "Examples:"
    echo "  $(basename "$0") -n 10000"                     # Generates data for 10000 primes with defaults
    echo "  $(basename "$0") -n 20000 -b 500"              # Generates data for 20000 primes, batch size 500
    echo "  $(basename "$0") -n 50000 -c 12"               # Generates data for 50000 primes, default batch size, 12 processes
    echo "  $(basename "$0") -n 100000 -b 1000 -c 16"        # Generates data for 100000 primes, batch size 1000, 16 processes
    echo ""
}

# Parse command line options
while getopts "n:b:c:o:h" opt; do
    case $opt in
        n)
            NUM_PRIMES=$OPTARG
            ;;
        b)
            BATCH_SIZE=$OPTARG
            ;;
        c)
            NUM_PROCESSES=$OPTARG
            ;;
        o)
            OUTPUT_DIR=$OPTARG
            ;;
        h)
            show_help
            exit 0
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            show_help
            exit 1
            ;;
    esac
done
shift $((OPTIND - 1))

# Set defaults if not provided via flags
NUM_PRIMES=${NUM_PRIMES:-${NUM_PRIMES_DEFAULT}}
BATCH_SIZE=${BATCH_SIZE:-${BATCH_SIZE_DEFAULT}}
NUM_PROCESSES=${NUM_PROCESSES:-${NUM_PROCESSES_DEFAULT}}
OUTPUT_DIR=${OUTPUT_DIR:-${OUTPUT_DIR_DEFAULT}}

# Create the main output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# 2. Define log and plot filenames within the output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${OUTPUT_DIR}/generate_log_${NUM_PRIMES}_${TIMESTAMP}.txt"
# This regex extracts the version string from the 'version = "X.Y.Z"' line
VERSION=$(grep -oP 'version = "\K[0-9.]+' pyproject.toml || echo "0.0.0")
if [ -z "$VERSION" ]; then
    echo "Error: Could not determine pppart version from pyproject.toml"
    exit 1
fi

# 4. Construct output PNG filename in the plot subdirectory
PLOT_DIR="${OUTPUT_DIR}/plots"
mkdir -p "${PLOT_DIR}"
OUTPUT_PNG="${PLOT_DIR}/${NUM_PRIMES}primes.${VERSION}.batch_rate_${TIMESTAMP}.png"


echo "Starting test data generation for ${NUM_PRIMES} primes..."
echo "Detailed progress will be logged to ${LOG_FILE}"
echo "Generated plot will be saved to ${OUTPUT_PNG}"

# 5. Run the main pppart module and pipe output to log file using tee
# python -u is crucial for unbuffered output to tee for tqdm progress bar updates.
# 2>&1 redirects stderr (where tqdm writes) to stdout, so tee captures it.
PYTHON_CMD="python -u -m pppart --num-primes $NUM_PRIMES"

if [ -n "$BATCH_SIZE" ]; then
    PYTHON_CMD="$PYTHON_CMD --batch-size $BATCH_SIZE"
fi

if [ -n "$NUM_PROCESSES" ]; then
    PYTHON_CMD="$PYTHON_CMD --num-processes $NUM_PROCESSES"
fi

# The main script handles its own output file, but we direct logs.
DATA_CSV_PATH="${OUTPUT_DIR}/partition_data_${NUM_PRIMES}_${TIMESTAMP}.csv"
PYTHON_CMD="$PYTHON_CMD --output-file $DATA_CSV_PATH"

echo "Running command: $PYTHON_CMD"
$PYTHON_CMD 2>&1 | tee "$LOG_FILE"

echo "Test data generation complete. Log saved to ${LOG_FILE}"
echo "Partition data saved to ${DATA_CSV_PATH}"
echo "Proceeding to plot generation..."

# 6. Call the visualization script with the log file and output PNG path
python -m pppart.viz.viz_batch_rate "$LOG_FILE" "$OUTPUT_PNG"

echo "Plot generation complete. Output saved to ${OUTPUT_PNG}"

# 7. Optional: Clean up the log file.
# Uncomment the line below if you want to remove the log file after plot generation.
# rm "$LOG_FILE" 