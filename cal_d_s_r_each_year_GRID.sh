#!/bin/bash
#SBATCH --job-name=cal_sdr       # Job name
#SBATCH --output=log_%x_%j.log  # Standard output log file
#SBATCH --error=log_%x_%j.err   # Standard error log file
#SBATCH --partition=node              # Partition/queue name
#SBATCH --nodes=1
#SBATCH --nodelist=node01
#SBATCH --mem=300G     
#SBATCH --cpus-per-task=42               

# Record start time
date
# Load Python module
source /share/home/fyliu0903/anaconda3/etc/profile.d/conda.sh
conda activate rainfall

# Execute the Python script
python -u cal_d_s_r_each_year_GRID.py "$@"

# Record end time
date
