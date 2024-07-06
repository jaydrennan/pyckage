import httpx
from typing import Dict, List, Optional
from nodesemver import max_satisfying

NPM_REGISTRY_URL = "https://registry.npmjs.org"


def get_package_info(package_name: str, version: str = "latest") -> Dict:
    """Fetch package information from npm registry."""
    with httpx.Client() as client:
        response = client.get(f"{NPM_REGISTRY_URL}/{package_name}")
        response.raise_for_status()
        package_data = response.json()

        if version == "latest":
            version = package_data["dist-tags"]["latest"]

        matching_version = find_max_satisfying(
            list(package_data["versions"].keys()), version
        )

        if not matching_version:
            matching_version = (
                version.lstrip("^~")
                if version.startswith("^") or version.startswith("~")
                else version
            )
            if matching_version not in package_data["versions"]:
                print(
                    f"Exact version {matching_version} not found. Using latest version."
                )
                matching_version = package_data["dist-tags"]["latest"]

        return package_data["versions"][matching_version]


def parse_version_range(range_: str) -> str:
    """Parse version range to handle special cases."""
    if range_ in ["*", "x", "latest"]:
        return "latest"
    return range_


def find_max_satisfying(versions: List[str], range_: str) -> Optional[str]:
    """Find the maximum version that satisfies the given range."""
    parsed_range = parse_version_range(range_)
    if parsed_range == "latest":
        return max(versions)

    try:
        return max_satisfying(versions, parsed_range, loose=False)
    except ValueError:
        return None
