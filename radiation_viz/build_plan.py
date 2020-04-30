"""
Print a sequence of commands for building files for a visualization
sequence.

Example usage:

Build the planned commands:

$ python -m radiation_viz.build_plan ~/misc/Yan-Fei_Jiang/ ~/tmp/radiation_test \
     --skip 4 --limit 1 --clean --var_substring rho --out ~/tmp/output > plan.sh

Then to execute them:

$ source plan.sh

or 

$ python -m radiation_viz.build_plan \
    /mnt/home/yjiang/ceph/CVDisk/CVIsoB2/Data_finished \
    /mnt/ceph/users/awatters/viz \
    --clean  --var_substring rho \
    --out /mnt/ceph/users/awatters/logs --limit 10 > plan.sh

Then to execute on the cluster in flatiron:

 % module load slurm
 % module load disBatch
 % sbatch -n 5 --ntasks-per-node 5 --wrap "disBatch.py plan.sh"
Submitted batch job 552107

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
        a("--out", help="Directory for output files.", default="")
        self.args = parser.parse_args()
        self.out = None
        out = self.args.out
        if (out):
            self.out = self.fix_path(out)
            if not os.path.isdir(self.out):
                os.makedirs(self.out)

    def fix_path(self, path):
        return os.path.abspath(os.path.expanduser(path))

    def redirect(self, for_path):
        out = self.out
        if not out:
            return ""
        (head, tail) = os.path.split(for_path)
        logpath = os.path.join(out, tail + ".log")
        return "> " + logpath + " 2>&1"

    def build(self):
        prefix = "python -u -m radiation_viz.prepare_viz_data"
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
        # disable truncated output if skip is not specified
        skip_option = "--skip 0"
        if (args.skip):
            skip_option = "--truncated --skip " + repr(args.skip)
        count = 0
        for path in files:
            redir = self.redirect(path)
            print(prefix, path, clean_option, substring_option, skip_option, "--no_config --to_directory", to_directory, "--force", redir)
            clean_option = ""  # after first don't clean
            count += 1
            if (args.limit > 0) and (count >= args.limit):
                break
        # finally build config file
        redir = self.redirect("config.json")
        print (prefix, "dummy_argument.athdf", "--config_only --to_directory", to_directory, "--force", redir)

if __name__ == "__main__":
    plan = BuildPlan()
    plan.build()
