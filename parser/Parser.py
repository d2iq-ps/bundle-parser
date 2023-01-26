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
from datetime import datetime
from Template import template
import re

class Tarball:
    def __init__(self, file_path):
        self.file_path = file_path
        self.cluster_name = self.file_path.rsplit("/", 1)[1].split("_")[0]

    def untar(self):
        """Takes a tarball, un-tars to the extracted dir"""
        print(f"Extracting Diagnostic bundle {self.cluster_name}")
        try:
            tar = tarfile.open(self.file_path)
            cluster_dir = f"extracted/{self.cluster_name}/"
            shutil.rmtree(cluster_dir, ignore_errors=True)
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
                print(f"This diagnostic bundle is a 2.x cluster")
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

def pull_value(source, field):
    """This function is a simple read key value which returns success and value. It's used
    for most of the parsing except where counts are needed"""
    try:
        with open(source) as target:
            target = target.read()
            answer = re.search(field, target).group(2).capitalize()
            return True, answer
    except Exception as e:
        return False, e


def parse_ver_1(target):
    """Pull the metrics for ver 1.x bundle"""
    date_time = open(f"extracted/timedatectl.txt")
    return None


def parse_ver_2(target):
    """Pull the metrics for ver 2.x bundle""" 
    ci = template
    
    # Set the target cluster name and current timestamp
    ci["parse_time"] = str(datetime.now())
    ci["bundle_name"] = target.split("/")[1]
    
    # Get cluster name
    source = f"{target}cluster-resources/nodes.json"
    field = "(cluster-name\": \")(.*)(\",)"
    ci["cluster_name"] = pull_value(source, field )[1].lower()
    
    
    # Get K8S distro version
    """     index = 1
        source = f"{target}cluster-resources/custom-resources/clusters.cluster.x-k8s.io/default.yaml"
        field = "(konvoy\.d2iq\.io\/provider: )(.*)(\n)"
        ci["data"][index]["value"] = distro_version = pull_value(source, field )[1] """
    
    # Get DKP version
    index = 2
    source = f"{target}cluster-resources/nodes.json"
    field = "(docker\.io\/mesosphere\/capimate:)(.*)(\")"
    ci["data"][index]["value"] = pull_value(source, field )[1].split("V")[1]
    
    # Get K8S version
    index = 3
    source = f"{target}/cluster-info/cluster_version.json"
    field = "(\"string\": \")(.*)(\")"
    ci["data"][index]["value"] = pull_value(source, field )[1].split("V")[1]
    
   
    # Get Infrastructure
    index = 5
    source = f"{target}cluster-resources/nodes.json"
    field = "(system-os_release\.ID\": \")(.*)(\",)"
    ci["data"][index]["value"] = pull_value(source, field )[1]
    
    # Get OS Version
    index = 6
    source = f"{target}cluster-resources/nodes.json"
    field = "(osImage\": \")(.*)(\",)"
    ci["data"][index]["value"] = pull_value(source, field )[1]
    
    # Get CPU and Node Count
    source = f"{target}cluster-resources/nodes.json"
    field = "(cpu\": \")(\d)(\")"
    node_count_index = 7
    cpu_count_index = 8
    with open(source) as target:
        target = target.read()
        cpus = re.findall(field, target)
        # count the number of nodes
        node_count = len(cpus)
        # count the number of cpus
        cpu_count = 0
        for cpu in cpus:
            cpu_count += int(cpu[1])
    ci["data"][node_count_index]["value"] = node_count
    ci["data"][cpu_count_index]["value"] = cpu_count
    
    # Determine if Management Cluster
    # Check if this CRD exists, if so, it's managing another cluster
    index = 13
    source = f"{target}cluster-resources/custom-resources/clusters.cluster.x-k8s.io/default.yaml"
    if os.path.isfile(source):
        ci["data"][index]["value"] = "Yes"
    else:
        ci["data"][index]["value"] = "No"


    # Count Managed Clusters
    # We'll determine this by counting the number of cluster CRDs minus the default
    index = 15
    source = f"{target}cluster-resources/custom-resources/clusters.cluster.x-k8s.io/"
    managed_cluster_count = len([name for name in os.listdir('.') if os.path.isfile(name)]) - 1
    ci["data"][index]["value"] = managed_cluster_count
    
    return ci
