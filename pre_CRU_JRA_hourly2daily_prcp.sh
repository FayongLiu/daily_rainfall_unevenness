#!/bin/bash
#SBATCH --job-name=climate_processing  # Job name
#SBATCH --output=%x_%j_%N.log          # Standard output log (dynamic)
#SBATCH --error=%x_%j_%N.err           # Error log (dynamic)
#SBATCH --ntasks=1                     # Run a single task
#SBATCH --cpus-per-task=4              # Number of CPU cores per task
#SBATCH --mem=150G                     # Memory pool for all cores
#SBATCH --time=24:00:00                # Time limit hrs:min:sec
#SBATCH --partition=gpu                # Partition to submit to
#SBATCH --nodes=1                      # Number of nodes

# Load necessary modules
module load cdo

# Directories and variables
first_year=1901
last_year=2020
input_dir='/data4/share/CRUJRA/v2.2/'  # Directory for climate data
output_dir_base="/data1/yyzhao/data/CRU-JRA/"

# Method for precipitation variable
declare -A variables_methods=( 
    ["pre"]="sum"  # Only process "pre" (precipitation) using sum method
)

# Function to process precipitation data
process_variable() {
    variable=$1
    method=${variables_methods[$variable]}

    # Use the same directory for precipitation data
    input_dir=$input_dir

    echo "Processing variable: $variable with method: $method"
    start_time=$(date +%s)

    output_dir="${output_dir_base}/${variable}"
    mkdir -p $output_dir  # Create output directory if it doesn't exist

    for (( year=$first_year; year<=$last_year; year++ )); do
        echo "Processing year: $year for variable: $variable"

        input_file="${input_dir}/crujra.v2.2.5d.${variable}.${year}.365d.noc.nc"

        if [[ ! -f $input_file ]]; then
            echo "Input file not found: $input_file"
            continue
        fi

        output_daily="${output_dir}/${variable}_${year}_daily.nc"
        cdo -r day${method} $input_file $output_daily

        echo "Completed processing for year: $year, variable: $variable. Output saved to: $output_daily"
    done

    end_time=$(date +%s)
    duration=$((end_time - start_time))
    echo "Completed processing for variable: $variable in $duration seconds"
}

# Start processing for precipitation variable
echo "Starting processing for variable: pre"
process_variable "pre"
echo "Finished processing for variable: pre"

total_end_time=$(date +%s)
echo "Process completed at $(date)"
