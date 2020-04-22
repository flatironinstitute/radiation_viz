# radiation_viz
Visualizations for astrophysical radiation simulation data.

View the example visualization here:
<a href="https://flatironinstitute.github.io/radiation_viz/">https://flatironinstitute.github.io/radiation_viz/</a>.

This is an experimental project which uses Python 3 for preprocessing of data files and HTML5/Javascript in a
modern browser like Chrome for presentation. Please install it in development mode to make it easy to update.

To install the Python3 `radiation_viz` pre-processing module locally in development mode:

```bash
    % git clone https://github.com/flatironinstitute/radiation_viz.git
    % cd radiation_viz
    % pip3 install -e .
```

The `radiation_viz.prepare_viz_data` module preprocesses an HDF5 file with the `.athdf` suffix
to produce a directory tree containing web code and data files for viewing the data in the file.

Here is the help output from the script:

```
% python -m radiation_viz.prepare_viz_data -h
usage: prepare_viz_data.py [-h] [--to_directory TO_DIRECTORY] [--truncated]
                           [--skip SKIP] [--quiet] [--force] [--clean]
                           [--dry_run] [--launch] [--view_only]
                           FILE [FILE ...]

positional arguments:
  FILE                  Source file to convert. Must end in '.athdf'.

optional arguments:
  -h, --help            show this help message and exit
  --to_directory TO_DIRECTORY
                        Destination directory where to place the visualization
                        and data.
  --truncated           Don't generate full resolution.
  --skip SKIP           Skip stride for truncated views (0 for none).
  --quiet               Don't print helpful output.
  --force               Don't prompt for verification and overwrite existing
                        files.
  --clean               Delete existing visualization folder if it exists.
  --dry_run             List intended actions but don't make permanent
                        changes.
  --launch              Start server and attempt to open the visualization in
                        a browser.
  --view_only           Only start server and attempt to open the
                        visualization in a browser.
```

