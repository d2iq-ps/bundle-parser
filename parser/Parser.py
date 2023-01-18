"""
Title:      Diagnostic Bundle Parser
Author:     Dave Whitehouse - EMEA Solutions Architect
Contact:    @dwhitehouse
Date:       17 Jan 2023
Scope:      A simple parser to extract key data points from a DKP diagnostic bundle
"""

import tarfile
import os
import shutil

class Tarball:
    def __init__(self, file_path):
        self.file_path = file_path
        self.cluster_name = self.file_path.rsplit("/", 1)[1].split("_")[0]
        self.cluster_info = {}

    def untar(self):
        """Takes a tarball, un-tars to the extracted dir"""
        print(f"Extracting Diagnostic bundle {self.cluster_name}")
        try:
            tar = tarfile.open(self.file_path)
            cluster_dir = f"extracted/{self.cluster_name}/"
            os.makedirs(cluster_dir, exist_ok=True)
            tar.extractall(cluster_dir)
            tar.close
            if os.path.exists(f"{cluster_dir}/bundles"):
                self.version = 1
                cluster_dir_full = f"{cluster_dir}/bundles"
                print(f"This diagnostic bundle is a 1.x cluster")
            else:
                for suffix in os.listdir(cluster_dir):
                    suffix = suffix
                cluster_dir_full = f"{cluster_dir}{suffix}"
                self.version = 2
                print(f"This diagnostic bundle is a 1.x cluster")
            if self.version == 1:
                for file in os.listdir(cluster_dir_full ):
                    print(f"Extracting {file}")
                    target_file = f"{cluster_dir_full}/{file}"
                    tar = tarfile.open(target_file)
                    node = file.split(".tar")[0]
                    os.makedirs(f"{cluster_dir}/{node}/", exist_ok=True)
                    tar.extractall(f"{cluster_dir}/{node}/")
                    tar.close
                shutil.rmtree(f"{cluster_dir}/bundles")
            else:
                for dir in os.listdir(f"{cluster_dir}{suffix}"):
                    origin = f"{cluster_dir}{suffix}/{dir}"
                    destination = f"{cluster_dir}{dir}"
                    shutil.move(origin, destination)
                shutil.rmtree(f"{cluster_dir}{suffix}")  
            return True, cluster_dir, self.version
        except Exception as e:
            return False, e, None

    def parse1(self, target):
        """Pull the metrics"""
        date_time = open(f"extracted/timedatectl.txt")
        return None
