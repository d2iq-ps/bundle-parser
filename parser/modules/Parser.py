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
from modules.Template import template
import re
import glob

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
            answer = re.search(field, target).group(2)
            return True, answer, None
    except Exception as e:
        # print(f"Issue with {field} - {str(e)}")
        return False, f"unable to determine", str(e)


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
 
 
    #####  1 and 9 #####                                          
    # Get K8S distro version
    # The "node-diagnostics" dir 
    index = 1
    source = f"{target}cluster-resources/custom-resources/clusters.cluster.x-k8s.io/default.yaml"
    field = "(konvoy\.d2iq\.io\/provider: )(.*)(\n)"
    if pull_value(source, field )[0]:
        # This assumes that if the cluster definition exists, it is Konvoy
        ci["data"][index]["value"] = "Konvoy"
    else:
        # We'll find containerd_config.toml and pull the source client
        node_diagnostics = f"{target}node-diagnostics/"
        for root, _, manifests in os.walk(node_diagnostics):
            for manifest in manifests:
                if manifest == "containerd_config.toml":
                    with open(f"{root}/{manifest}", "r") as config_toml:
                        config_toml = config_toml.read()
                        field = "(Client = \[\")(.*)(\"\])"
                        try:
                            distro = re.search(field, config_toml).group(2)
                            ci["data"][index]["value"] = distro
                        except:
                            ci["data"][index]["value"] = "Konvoy"
                elif manifest == "nvidia_container_runtime_config.toml":
                    with open(f"{root}/{manifest}", "r") as gpu_toml:
                        gpu_toml = gpu_toml.read()
                        if "No such file" in gpu_toml:
                            ci["data"][9]["value"] = 0
                        else:
                            #TODO Need to read this with GPU to parse
                            ci["data"][9]["value"] = "Has GPUs"
                else:
                    ci["data"][9]["value"] = 0  
    if not isinstance(ci["data"][9]["value"], int):
        # We didn't find GPUs so set the value to 0
        ci["data"][9]["value"] = 0
                    
                
    #####  2  #####    
    # Get DKP version
    index = 2
    source = f"{target}cluster-resources/nodes.json"
    field = "(kommander2-licensing-webhook:v)(.*)(\")"
    if "unable" in pull_value(source, field )[1]:
        ci["data"][index]["value"] = "Not Applicable"
    else:
        ci["data"][index]["value"] = pull_value(source, field )[1]
    
    #####  3  #####   
    # Get K8S version
    index = 3
    source = f"{target}/cluster-info/cluster_version.json"
    field = "(\"string\": \")(.*)(\")"
    ci["data"][index]["value"] = pull_value(source, field )[1].split("v")[1]


    #####  4  ##### 
    # Determine Infrastructure
    node_diagnostics = f"{target}node-diagnostics/"
    index = 4
    for root, _, manifests in os.walk(node_diagnostics):
        for manifest in manifests:
            if manifest == "containerd_config.toml":
                with open(f"{root}/{manifest}", "r") as config_toml:
                    config_toml = config_toml.read()
                    field = "(Client = \[\")(.*)(\"\])"
                    try: 
                        distro = re.search(field, config_toml).group(2)
                        ci["data"][index]["value"] = distro.split("/")[0]
                    except AttributeError:
                        ci["data"][index]["value"] = "Unknown"
    
    #####  5  #####  
    # Get OS
    index = 5
    source = f"{target}cluster-resources/nodes.json"
    field = "(osImage\": \")(.*)(\",)"
    ci["data"][index]["value"] = pull_value(source, field )[1].split(" ")[0]
        
    #####  6  #####    
    # Get OS Version
    index = 6
    source = f"{target}cluster-resources/nodes.json"
    field = "(osImage\": \")(.*)(\",)"
    ci["data"][index]["value"] = pull_value(source, field )[1]

    #####  7  #####
    # Get Node Count
    # In the "node-diagnostics" directory, there is a sub-directory for each node. We'll count them
    # to determine the number of nodes
    source = f"{target}node-diagnostics"
    index = 7
    node_count = len([i for i in os.listdir(source)])
    ci["data"][index]["value"] = node_count

    #####  8  ##### 
    # Get CPU Count
    source = f"{target}cluster-resources/nodes.json"
    field = "(cpu\": \")(\d+)(\")"
    index = 8
    with open(source) as target_file:
        target_file = target_file.read()
        cpus = re.findall(field, target_file)
        # count the number of cpus
        cpu_count = 0
        for cpu in cpus:
            cpu_count += int(cpu[1])
    ci["data"][index]["value"] = cpu_count
    
    #####  9  ##### 
    # Combined with index 1

     
    #####  10  #####    
    # Determine if airgapped
    # We'll navigate to configmaps/kommander (if a management cluster) in
    # there there's a cm called dkp-insights-cluster-info[.*].json and a field
    # called "airgapped". If it's a managed cluster, check configmaps/CLUSTER_NAME/
    # /dkp-insights-cluster-info-[.*].json with the same field.
    index = 10
    # Find for management cluster
    source_manager = f"{target}configmaps/kommander"
    if os.path.exists(source_manager):
        for manifest in os.listdir(source_manager):
            if re.match(r'dkp-insights-cluster-info.*', manifest):
                source = os.path.join(source_manager, manifest)
                field = "(airgapped\": \")(.*)(\")"
                if pull_value(source, field)[1] == "true":
                    ci["data"][index]["value"] = "true"
                else:
                    ci["data"][index]["value"] = "false"
    else:
        # Didn't find any manifests in configmaps/kommander. Iterate through all configmaps
        # to find the insights manifest. This is currently the only type of manifest that details
        # the "airgapped" field.
        source_managed = f"{target}configmaps/"
        for manifest in glob.iglob(source_managed + '*/*.json', recursive=True):
                if re.match(r'.*dkp-insights-cluster-info.*', manifest):
                    source = manifest
                    field = "(airgapped\": \")(.*)(\")"
                    if pull_value(source, field)[1] == "true":
                        ci["data"][index]["value"] = "true"
                    else:
                        ci["data"][index]["value"] = "false"
                    # There's a cluster name field in there as well. Let's pull that
                    field = "(clusterName\": \")(.*)(\")"
                    ci["cluster_name"] = pull_value(source, field)[1].lower()

    #####  11  ##### 
    # Determine if FIPS
    index = 11
    source = f"{target}/cluster-info/cluster_version.json"
    field = "(\"string\": \")(.*)(\")"
    fips_check = pull_value(source, field )[1].split("v")[1]
    if "fips" in fips_check:
        ci["data"][index]["value"] = "True"
    else:
        ci["data"][index]["value"] = "False"       

    #####  12  #####
    # Get applications
    try:
        index = 12
        source = f"{target}cluster-resources/custom-resources/helmreleases.helm.toolkit.fluxcd.io/"
        application_list = []
        kommander_apps = []
        for name in os.listdir(source):
            if name == "kommander.yaml":
                kommander_list = []
                field = "(fluxcd\.io\/name: )(.*)(\n)"
                kommander_source = open(f"{target}cluster-resources/custom-resources/helmreleases.helm.toolkit.fluxcd.io/kommander.yaml", "r").read()
                kommander_list = re.findall(field, kommander_source)
                for kommander_app in kommander_list:
                    app = str(kommander_app[1]).replace("-helmrelease", "").replace("-appmanagement", "")
                    if len(app) > 2 and app not in kommander_apps:
                        kommander_apps.append(app)
            elif ci["cluster_name"] not in name:
                application_list.append(name.split(".yaml")[0])
        ci["data"][index]["value"] = application_list, kommander_apps
    except:
        ci["data"][index]["value"] = "None"      


    #####  13  ##### 
    # Determine if Management Cluster
    # Check if this CRD exists, if so, it's managing another cluster
    index = 13
    source = f"{target}cluster-resources/custom-resources/clusters.cluster.x-k8s.io/default.yaml"
    if os.path.isfile(source):
        ci["data"][index]["value"] = "Yes"
    else:
        ci["data"][index]["value"] = "No"


    #####  14  ##### 
    # Determine DKP management cluster version
    # We can map this to dkp version
    index = 14
    dkp_version = ci["data"][2]["value"]
    if dkp_version.startswith("2.0"):
        kommander_version = "Kommander 2.0"
    elif dkp_version.startswith("2.1"):
        kommander_version = "Kommander 2.1"
    elif dkp_version == "Not Applicable":
        kommander_version = dkp_version
    else:
        kommander_version = f"DKP {dkp_version}"
    ci["data"][index]["value"] = kommander_version
    
    
    #####  15  ##### 
    # Count Managed Clusters
    # We'll determine this by counting the number of cluster CRDs minus the default
    index = 15
    source = f"{target}cluster-resources/custom-resources/clusters.cluster.x-k8s.io/"
    try:
        managed_clusters = [name for name in os.listdir(source)]
        #if managed_cluster_count > 0:
        ci["data"][index]["value"] = len(managed_clusters) - 1
        # else:
        #    ci["data"][index]["value"] = 0
    except:
        ci["data"][index]["value"] = 0
    
    return ci
