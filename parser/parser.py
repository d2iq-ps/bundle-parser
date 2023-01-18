from Parser import Tarball

# my_bundle = "bundle/kaas-1348-cve-prod_20220722T131608.tar.gz"
my_bundle = "bundle/support-bundle-2023-01-11T13_59_54.tar.gz"

tarball = Tarball(my_bundle)

result, target_dir, version = tarball.untar()
if not result:
    print(f"Failed. Reason: {target_dir}")
