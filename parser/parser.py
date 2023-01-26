from Parser import Tarball, parse_ver_1, parse_ver_2
import json

# my_bundle = "bundle/kaas-1348-cve-prod_20220722T131608.tar.gz" # ver 1 - ebrc
my_bundle = "bundle/support-bundle-2023-01-11T13_59_54.tar.gz" # ver 2 EITCO mgt
# my_bundle = "bundle/support-bundle-2023-01-11T14_08_44.tar.gz" # ver 2 EITCO worker

if __name__ == "__main__":
    # Untar the bundle
    tarball = Tarball(my_bundle)
    result, target_dir, version = tarball.untar()
    if result:
        # The untar operation worked and returned a directory
        if version == 2:
            # The bundle is version 2.x
            cluster = parse_ver_2(target_dir)
            print(cluster)
            print(json.dumps(cluster, indent=4))
        else:
            # The bundle version is 1.x
            parse_ver_1()
    else:
        # Extraction failed. Exit with Error Code
        print(f"Failed. Reason: {target_dir}")
