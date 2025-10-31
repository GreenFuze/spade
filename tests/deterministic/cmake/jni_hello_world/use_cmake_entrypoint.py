from pathlib import Path

from core.rig import RIG
from deterministic import CMakePlugin
from tests.test_utils import test_repos_root


def main() -> None:
    repo_root = test_repos_root / "jni_hello_world"

    # use CMake entrypoint to generate RIG for repo_root
    cmakeplugin = CMakePlugin(repo_root)
    plugin_rig = cmakeplugin.rig

    # compare generated RIG to ground truth
    ground_truth_rig = RIG.load(Path(__file__).parent / "jni_hello_world_ground_truth.sqlite3")

    results = plugin_rig.compare(ground_truth_rig)
    if results is not None:
        print(results)
        exit(1)

if __name__ == "__main__":
    main()
