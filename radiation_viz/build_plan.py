"""
Print a sequence of commands for building files for a visualization
sequence.

Example usage:

$ python build_plan.py ~/misc/Yan-Fei_Jiang/ ~/tmp/radiation_test --limit 1 --clean --var_substring rho > plan.sh

Then to execute:

$ source plan.sh

"""

import argparse
import os
import glob

class BuildPlan:

    def __init__(self):
        parser = self.parser = argparse.ArgumentParser()
        a = parser.add_argument
        a("from_directory", help="Directory containing files to convert.")
        a("to_directory", help="Directory where to place support files and visualization files.")
        a("--glob", help="Glob to match filenames (default *.athdf).", default="*.athdf")
        a("--limit", help="Maximum number of files to process (default all).", type=int, default=0)
        a("--clean", help="Delete and replace to_directory if it exists.", action="store_true")
        a("--var_substring", help="Exclude variables with names that do not match this substring (default '').", default='')
        a("--skip", help="Skip stride for truncated views (default to full resolution).", type=int, default=0)
        self.args = parser.parse_args()

    def fix_path(self, path):
        return os.path.abspath(os.path.expanduser(path))

    def build(self):
        prefix = "python -m radiation_viz.prepare_viz_data"
        clean_option = ""
        substring_option = ""
        skip_option = ""
        args = self.args
        from_directory = self.fix_path(args.from_directory)
        to_directory = self.fix_path(args.to_directory)
        glob_path = os.path.join(from_directory, args.glob)
        files = glob.glob(glob_path)
        assert files, "No files found matching: " + repr(glob_path)
        if args.clean:
            clean_option = "--clean"
        if args.var_substring:
            substring_option = "--var_substring " + args.var_substring
        skip_option = "--skip " + repr(args.skip)
        count = 0
        for path in files:
            print(prefix, path, clean_option, substring_option, skip_option, "--no_config --to_directory", to_directory, "--force")
            clean_option = ""  # after first don't clean
            count += 1
            if (args.limit > 0) and (count >= args.limit):
                break
        # finally build config file
        print (prefix, "dummy_argument.athdf", "--config_only --to_directory", to_directory, "--force")

if __name__ == "__main__":
    plan = BuildPlan()
    plan.build()
