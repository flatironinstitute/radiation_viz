Example data

The file example_small.athdf is an HDF5 file containing only one
dataset.

To view the dataset as a visualization install the preprocessing module
and then run a command line similar to this in this directory

$ python -m radiation_viz.prepare_viz_data example_small.athdf --clean --launch --to_directory delete_me --force

The script will generate the file structure needed to visualize the dataset
at full detail and also in a "skip 4" truncated view which is more performant
(but doesn't look as good).  The "--launch" flag causes the script to run a web server
and attempt to open the visualization in the system browser.

Terminate the web server using CONTROL-C

To clean up when you are done with the test visualization:

$ rm -rf delete_me
