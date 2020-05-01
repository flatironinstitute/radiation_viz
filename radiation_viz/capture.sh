#!/bin/bash

# request a single gpu node for the run.

#SBATCH -N1 --gres=gpu:1 -p gpu

# module load slurm
# srun -N1 --gres=gpu:1 -p gpu bash capture.sh

# to cancel
# $ squeue | grep awatters
#            554219       gpu capture. awatters  R    2:18:07      1 workergpu05
# $ scancel 554219

source activate nodetest
python -m radiation_viz.capture_images \
     --to_directory /mnt/ceph/users/awatters/images \
     --http_directory /mnt/ceph/users/awatters/viz \
     --node_directory ~/repos/radiation_viz/image_capturer \
     --settings_path ~/repos/radiation_viz/radiation_viz/example_camera_settings.json \
     --limit 3000 > /mnt/ceph/users/awatters/logs/capture.log  2>&1

