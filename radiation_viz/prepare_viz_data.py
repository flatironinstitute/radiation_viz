
"""
Process radiation data files into web viewable formats.
"""

import argparse
import os
import h5py
import numpy as np

SOURCE_SUFFIX = '.athdf'
DEFAULT_DIR = "./radiation_viz"

class Runner:

    def __init__(self):
        parser = self.parser = argparse.ArgumentParser()
        a = parser.add_argument
        a("filenames", help="Source file to convert.  Must end in '.athdf'.", nargs='+', metavar='FILE')
        a("--to_directory", help="Destination directory where to place the visualization and data.", default=DEFAULT_DIR)
        a("--truncated", help="Don't generate full resolution.", action="store_true")
        a("--skip", help="Skip stride for truncated views (0 for none).", type=int, default=4)
        a("--quiet", help="Don't print helpful output.", action="store_true")
        a("--force", help="Overwrite existing files.", action="store_true")
        a("--dry_run", help="List intended actions but don't make permanent changes.", action="store_true")
        a("--launch", help="Start server and attempt to open the visualization in a browser.", action="store_true")
        args = self.args = parser.parse_args()
        self.verbose = (not args.quiet) or args.dry_run
        if self.verbose:
            print()
            print("Arguments parsed.")

    def run(self):
        self.load_file_data()
        self.check_directory()
        self.check_output_files()
        if self.verbose:
            print()
            if self.args.dry_run:
                print ("Dry run complete: not making changes.")
                return
            confirm = input("*** PLEASE CONFIRM: Make changes (Y/N)? ")
            if confirm.upper()[0:1] != "Y":
                print("Aborting.")
                return
        self.copy_directory_if_needed()
        self.write_output_files()
        self.set_up_configuration()

    def load_file_data(self):
        "Load and validate the metadata from data file(s)."
        args = self.args
        self.files = [os.path.abspath(os.path.expanduser(fn)) for fn in args.filenames]
        if self.verbose:
            print("Loading data from file(s).")
        self.file_readers = {}
        for filename in self.files:
            if self.verbose:
                print("   loading metadata for", repr(filename))
                self.file_readers[filename] = FileReader(filename, args.truncated, args.skip, self.verbose)

    def check_directory(self):
        "Determine whether the output directory needs to be created and initialized."
        folder = self.to_directory = self.args.to_directory
        if self.verbose:
            print("Preparing to install or update visualization directory:", repr(self.to_directory))
        if not os.path.exists(folder):
            if self.verbose:
                print ('    folder', repr(folder), 'does not exist: it will be populated.')
            self.make_folder = True
        else:
            if not os.path.isdir(folder):
                raise ValueError("Destination exists and is not a directory: " + repr(folder))
            self.make_folder = False

    def copy_directory_if_needed(self):
        "Set up visualization infrastructure, if it doesn't already exist."
        folder = self.to_directory
        if not self.make_folder:
            if self.verbose:
                print("Assuming existing directory infrastructure is okay. " + repr(folder))
                return
        if self.verbose:
            print("Setting up directory " + repr(folder))

    def check_output_files(self):
        "Check whether any output files are overwrites."
        if self.verbose:
            print("Checking whether output data files exist.")

    def write_output_files(self):
        "Create JSON and binary files from inputs files."
        if self.verbose:
            print("Writing output data files.")

    def set_up_configuration(self):
        "Create the configuration file for the visualization."

class FileReader:

    def __init__(self, filename, truncated, skip, verbose):
        (self.filename, self.truncated, self.skip, self.verbose) = (filename, truncated, skip, verbose)
        assert (not truncated) or skip, "truncated file must have a non-zero skip value " + repr(filename)
        # extract the metadata for quantity locations
        f = h5py.File(filename, 'r')
        def to_str(b_array):
            return [b.decode("utf8") for b in b_array]
        variable_names = to_str(f.attrs["VariableNames"])
        num_variables = f.attrs["NumVariables"]
        dataset_names = to_str(f.attrs["DatasetNames"])
        assert len(num_variables) == len(dataset_names), "num_variables doesn't match datasets: " + repr((filename, num_variables, dataset_names))
        name_to_dataset_and_index = {}
        count = 0
        for (nv, ds) in zip(num_variables, dataset_names):
            for index in range(nv):
                vr = variable_names[count]
                name_to_dataset_and_index[vr] = (ds, index)
                count += 1
        assert count == len(variable_names), "variable names don't match datasets: " + repr((filename, variable_names, count))
        self.name_to_dataset_and_index = name_to_dataset_and_index
        if self.verbose:
            for (name, dsi) in sorted(name_to_dataset_and_index.items()):
                print ("    Found", repr(name), "at", dsi, "in", filename)

def run():
    rnr = Runner()
    rnr.run()
    return rnr

if __name__=="__main__":
    runner = run()
