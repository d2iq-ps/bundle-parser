from modules.Parser import Tarball, parse_ver_1, parse_ver_2
import json
import os

bundle_dir = "bundle"
bundles = [bundle for bundle in os.listdir(bundle_dir) if bundle != "README.md" ]

if __name__ == "__main__":
    for bundle in bundles:
        # Untar the bundle
        my_bundle = f"bundle/{bundle}"
        tarball = Tarball(my_bundle)
        result, target_dir, version = tarball.untar()
        if result:
            # The untar operation worked and returned a directory
            if version == 2:
                # The bundle is version 2.x
                cluster = parse_ver_2(target_dir)
                # print(cluster)
                print(json.dumps(cluster, indent=4))
            else:
                # The bundle version is 1.x
                parse_ver_1()
        else:
            # Extraction failed. Exit with Error Code
            print(f"Failed. Reason: {target_dir}")
