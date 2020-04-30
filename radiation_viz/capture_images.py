"""
Top level control for capturing an image sequence from the
visualization.

- Launch a node based http server serving the visualization in a subprocess.
- Launch a node/puppeteer headless browser scraper script to scrape the images from the http server.
- Wait for the scraper script to terminate.
- Terminate the http server.

Example:

python -m radiation_viz.capture_images \
     --to_directory ~/tmp/viz \
     --http_directory ~/misc/Yan-Fei_Jiang/eg_small \
     --node_directory ~/repos/radiation_viz/image_capturer \
     --limit 5
"""

import os
import argparse
import subprocess

SERVER_EXECUTABLE = "http-server"
SCRAPER_NODE_SCRIPT = "scrape_images.js"

class Runner:

    def __init__(self):
        parser = self.parser = argparse.ArgumentParser()
        a = parser.add_argument
        a("--to_directory", help="Destination directory where to place the images.", required=True)
        a("--http_directory", help="Directory containing the index.html file for the visualization.", required=True)
        a("--node_directory", help="Directory containing the node scripts.", required=True)
        a("--url_parameters", help="URL or URL arguments containing initial image and/or camera settings.", default='')
        a("--limit", help="Maximum number of images to capture (default all).", type=int, default=0)
        a("--port", help="Port where to run the server (default 9393).", type=int, default=9393)
        #a("--mac", help="Use Mac chrome configuration.", action="store_true")
        a("--quiet", help="Don't print helpful output.", action="store_true")
        args = self.args = parser.parse_args()
        self.verbose = (not args.quiet)
        if self.verbose:
            print()
            print("Arguments parsed.")
        # validate parameters
        self.http_directory = self.fix_path(args.http_directory)
        assert os.path.isdir(self.http_directory), repr(self.http_directory) + " must be a directory."
        self.node_directory = self.fix_path(args.node_directory)
        assert os.path.isdir(self.node_directory), repr(self.node_directory) + " must be a directory."
        index = os.path.join(self.http_directory, "index.html")
        assert os.path.isfile(index), repr(index) + " must be an existing file."
        self.to_directory = self.fix_path(args.to_directory)
        params = args.url_parameters
        if "?" in params:
            try:
                [params] = params.split("?")[1:]
            except:
                raise ValueError(repr(params) + " invalid url parameters.")
        self.params = params

    def fix_path(self, path):
        return os.path.abspath(os.path.expanduser(path))

    def run(self):
        if not os.path.isdir(self.to_directory):
            if self.verbose:
                print("creating output directory", repr(self.to_directory))
            os.makedirs(self.to_directory)
        if self.verbose:
            print("running subprocesses in", repr(self.node_directory))
        os.chdir(self.node_directory)
        try:
            self.launch_web_server()
            self.run_scraper()
        finally:
            self.stop_web_server()

    def launch_web_server(self):
        args = self.args
        cmd_args = [SERVER_EXECUTABLE, self.http_directory, "-p", repr(args.port)]
        if self.verbose:
            print("starting web server", cmd_args)
        self.web_server = subprocess.Popen(cmd_args)

    def run_scraper(self):
        args = self.args
        initial_url = "http://127.0.0.1:%s/index.html" % (args.port)
        if args.url_parameters:
            initial_url = "%s?%s" % (initial_url, args.url_parameters)
        #mac_option = "linux"
        #if args.mac:
        #    mac_option = "mac"
        cmd_args = ["node", SCRAPER_NODE_SCRIPT, initial_url, self.to_directory, repr(args.limit)]
        if self.verbose:
            print("running scraper", cmd_args)
        self.scraper_info = subprocess.run(cmd_args)
        if self.verbose:
            print("scraper finished.")

    def stop_web_server(self):
        if self.verbose:
            print("stopping web server.")
        self.web_server.terminate()

if __name__=="__main__":
    rnr = Runner()
    rnr.run()
