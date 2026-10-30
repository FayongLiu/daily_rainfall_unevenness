#!/bin/bash
#SBATCH --job-name=pre_station       # Job name
#SBATCH --output=log_%x_%j.log  # Standard output log file
#SBATCH --error=log_%x_%j.err   # Standard error log file
#SBATCH --partition=node              # Partition/queue name
#SBATCH --nodes=1
#SBATCH --mem=100G       
#SBATCH --cpus-per-task=64

# Record start time
date
# Load Python module
source /share/home/fyliu0903/anaconda3/etc/profile.d/conda.sh
conda activate rainfall

# Execute the Python script
python -u pre_station_select.py "$@"

# Record end time
date
