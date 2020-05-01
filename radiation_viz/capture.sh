#!/bin/bash

# request a single gpu node for the run.

#SBATCH -N1 --exclusive --gres=gpu:1 -p gpu bash

# module load slurm
# srun -N1 --exclusive --gres=gpu:1 -p gpu bash capture.sh

source activate nodetest
python -m radiation_viz.capture_images \
     --to_directory /mnt/ceph/users/awatters/images \
     --http_directory /mnt/ceph/users/awatters/viz \
     --node_directory ~/repos/radiation_viz/image_capturer \
     --limit 3000 > /mnt/ceph/users/awatters/logs/capture.log

