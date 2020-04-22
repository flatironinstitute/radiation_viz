
"""
Process radiation data files into web viewable formats.
"""

import argparse
import os
import h5py
import numpy as np
import shutil
import json
from . import dump_json_and_binary

SOURCE_SUFFIX = '.athdf'
DEFAULT_DIR = "./radiation_viz"
DATA_SUBDIRECTORY = "processed_data"
CONFIG_FILENAME = "config.json"

MY_DIR = os.path.dirname(__file__)

def module_path(relative_path):
    return os.path.join(MY_DIR, relative_path)

class Runner:

    def __init__(self):
        parser = self.parser = argparse.ArgumentParser()
        a = parser.add_argument
        a("filenames", help="Source file to convert.  Must end in '.athdf'.", nargs='+', metavar='FILE')
        a("--to_directory", help="Destination directory where to place the visualization and data.", default=DEFAULT_DIR)
        a("--truncated", help="Don't generate full resolution.", action="store_true")
        a("--skip", help="Skip stride for truncated views (0 for none).", type=int, default=4)
        a("--quiet", help="Don't print helpful output.", action="store_true")
        a("--force", help="Don't prompt for verification and overwrite existing files.", action="store_true")
        a("--clean", help="Delete existing visualization folder if it exists.", action="store_true")
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
        if not self.args.force:
            confirm = input("*** PLEASE CONFIRM: Make changes (Y/N)? ")
            if confirm.upper()[0:1] != "Y":
                print("Aborting.")
                return
        self.copy_directory_if_needed()
        self.write_output_files()
        self.set_up_configuration()

    def fix_path(self, path):
        return os.path.abspath(os.path.expanduser(path))

    def load_file_data(self):
        "Load and validate the metadata from data file(s)."
        args = self.args
        self.files = sorted([self.fix_path(fn) for fn in args.filenames])
        if self.verbose:
            print("Loading data from file(s).")
        self.file_readers = {}
        force_files = args.force or args.clean
        for filename in self.files:
            if self.verbose:
                print("   loading metadata for", repr(filename))
            self.file_readers[filename] = FileReader(filename, args.truncated, args.skip, force_files, self.verbose)

    def check_directory(self):
        "Determine whether the output directory needs to be created and initialized."
        folder = self.to_directory = self.fix_path(self.args.to_directory)
        if self.verbose:
            print("Preparing to install or update visualization directory:", repr(self.to_directory))
        if not os.path.exists(folder):
            if self.verbose:
                print ('    folder', repr(folder), 'does not exist: it will be populated.')
            self.make_folder = True
        else:
            if not os.path.isdir(folder):
                raise ValueError("Destination exists and is not a directory: " + repr(folder))
            if self.args.clean:
                if self.verbose:
                    print("   existing directory will be deleted.")
                self.make_folder = True
            else:
                if self.verbose:
                    print("   existing directory will be preserved.")
                self.make_folder = False
        if self.make_folder:
            self.template_folder = module_path("viz_template")
            assert os.path.isdir(self.template_folder)
            if self.verbose:
                print("    Folder data will be cloned from: " + repr(self.template_folder))

    def copy_directory_if_needed(self):
        "Set up visualization infrastructure, if it doesn't already exist."
        folder = self.to_directory
        if not self.make_folder:
            if self.verbose:
                print("Assuming existing directory infrastructure is okay. " + repr(folder))
                return
        if os.path.exists(folder):
            if self.verbose:
                print("deleting exiting folder " + repr(folder))
            shutil.rmtree(folder)
        if self.verbose:
            print("Setting up directory " + repr(folder))
        shutil.copytree(self.template_folder, folder)

    def check_output_files(self):
        "Check whether any output files are overwrites."
        self.data_directory = os.path.join(self.to_directory, DATA_SUBDIRECTORY)
        if self.verbose:
            print("Checking whether output data files exist.")
        for filename in self.files:
            self.file_readers[filename].check_output_files(self.data_directory)

    def write_output_files(self):
        "Create JSON and binary files from inputs files."
        if self.verbose:
            print("Writing output data files.")
        for filename in self.files:
            self.file_readers[filename].write_output_files(self.data_directory)

    def set_up_configuration(self):
        "Create the configuration file for the visualization."
        datadir = self.data_directory
        todir = self.to_directory
        config_path = os.path.join(todir, CONFIG_FILENAME)
        files = set(os.listdir(datadir))
        files_info = []
        for bin_fn in sorted(files):
            if bin_fn.endswith(".bin"):
                prefix = bin_fn[:-4]
                json_fn = prefix + ".json"
                if json_fn in files:
                    files_info.append({"prefix": prefix, "bin": bin_fn, "json": json_fn})
        config_value = {
            "files": files_info,
        }
        with open(config_path, "w") as out:
            json.dump(config_value, out, indent=4)
        if self.verbose:
            print("Configured %s files in %s." % (len(files_info), config_path))

class FileReader:

    def __init__(self, filename, truncated, skip, force, verbose):
        (self.filename, self.truncated, self.skip, self.force, self.verbose) = (filename, truncated, skip, force, verbose)
        assert filename.endswith(SOURCE_SUFFIX), "Filename has incorrect extension: " + repr((filename, SOURCE_SUFFIX))
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

    def check_output_files(self, to_directory):
        self.to_directory = to_directory
        [self.source_dir, self.file_tail] = os.path.split(self.filename)
        self.file_prefix = self.file_tail[:-len(SOURCE_SUFFIX)]
        self.out_prefix = self.file_prefix.replace(".", "_")
        self.variable_and_skip_to_file_prefix = {}
        for vr in sorted(self.name_to_dataset_and_index):
            if not self.truncated:
                self.variable_and_skip_to_file_prefix[(vr, 0)] = "%s_%s_full"  % (self.file_prefix, vr)
            if self.skip:
                self.variable_and_skip_to_file_prefix[(vr, self.skip)] = "%s_%s_skip_%s"  % (self.file_prefix, vr, self.skip)
        existing_files = 0
        for prefix in sorted(self.variable_and_skip_to_file_prefix.values()):
            for ext in (".json", ".bin"):
                path = os.path.join(self.to_directory, prefix + ext)
                if os.path.exists(path):
                    existing_files += 1
                    assert os.path.isfile(path), "Cannot overwrite non-file: " + repr(path)
                    if self.verbose:
                        print("    Existing file to overwrite " + repr(path))
                elif self.verbose:
                    print("    File will be created " + repr(path))
        if existing_files > 0 and not self.force:
            assert self.force, "Cannot overwrite existing %s files without --force flag." % existing_files

    def write_output_files(self, to_directory):
        assert to_directory == self.to_directory
        source_filename = self.filename
        for vr_skip in sorted(self.variable_and_skip_to_file_prefix):
            (vr, skip) = vr_skip
            to_prefix = self.variable_and_skip_to_file_prefix[vr_skip]
            if self.verbose:
                print("    writing expanded data", vr_skip, to_prefix)
            (ds, index) = self.name_to_dataset_and_index[vr]
            blocks = dump_json_and_binary.get_values_and_geometry(source_filename, ds, index, self.verbose)
            if skip:
                blocks = blocks.truncate_r_phi(skip, self.verbose)
            # xxxx always expand?  no verbose option
            expanded = blocks.expand(verbose=False)
            expanded.dump_files(to_directory, to_prefix, verbose=self.verbose)
            
def run():
    rnr = Runner()
    rnr.run()
    return rnr

if __name__=="__main__":
    runner = run()
