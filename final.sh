#!/bin/bash
#SBATCH --job-name=python
#SBATCH --output=slurm-%j.log
#SBATCH --error=slurm-%j.err
#SBATCH --partition=node
#SBATCH --nodelist=node04
#SBATCH --nodes=1

date
module load python
# conda activate python3.10
# Your Python script

python /data1/yyzhao/code/finally_upload_code/plot_v6_figS8_cmip6_muti_map.py

echo "~~~~~~~~~~~~~~~~~~~~ok~~~~~~~~~~~~~~~~~~~~~~~"

#python /data1/yyzhao/code/finally_upload_code/plot_v6_figS9_cmip6_muti_slope.py
echo "~~~~~~~~~~~~~~~~~~~~ok~~~~~~~~~~~~~~~~~~~~~~~"
#python /data1/yyzhao/code/finally_upload_code/plot_v6_fig4_regional_daily_grids.py
date


#查看node的可用内存和可用核：sinfo -N -o "%N %C %e"