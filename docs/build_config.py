"""
Look for binary files with matching json files and list their prefixes in config.json.
"""

import os, json

data_dir = "./processed_data"
config_fn = "./config.json"

def build_it():
    files = os.listdir(data_dir)
    prefixes = []
    for fn in sorted(files):
        if fn.endswith(".bin"):
            print ("examining binary filename", fn)
            prefix = fn[:-4]
            json_fn = prefix+".json"
            if os.path.exists(os.path.join(data_dir, json_fn)):
                prefixes.append({"prefix": prefix, "bin": fn, "json": json_fn})
                print("matching json found", prefixes[-1])
    fout = open(config_fn, "w")
    json_data = {
        "files": prefixes,
    }
    json.dump(json_data, fout, indent=4)
    fout.close()
    print ("wrote config file", config_fn)

if __name__=="__main__":
    build_it()
