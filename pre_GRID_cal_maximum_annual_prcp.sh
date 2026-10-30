#!/bin/bash
#SBATCH --job-name=cal_max_prep       # Job name
#SBATCH --output=log_%x_%j.log  # Standard output log file
#SBATCH --error=log_%x_%j.err   # Standard error log file
#SBATCH --partition=node              # Partition/queue name
#SBATCH --nodes=1
#SBATCH --mem=300G       
#SBATCH --cpus-per-task=42            

# Record start time
date
# Load Python module
source /share/home/fyliu0903/anaconda3/etc/profile.d/conda.sh
conda activate rainfall

# Execute the Python script
python -u pre_GRID_cal_maximum_annual_prcp.py "$@" 

# Record end time
date
