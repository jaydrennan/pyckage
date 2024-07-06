import json
import os
import re
from typing import Tuple, Optional
from .npm_utils import get_package_info


def parse_package_name(package_arg: str) -> Tuple[str, Optional[str]]:
    """Parse package name and version from input argument."""
    match = re.match(
        r"^(@?[a-zA-Z0-9-]+(?:/[a-zA-Z0-9-]+)?)(?:@([^@]+))?$", package_arg
    )
    if not match:
        raise ValueError(f"Invalid package name: {package_arg}")
    return match.group(1), match.group(2)


def get_latest_version(package_name: str) -> str:
    """Fetch the latest version of the package from npm registry."""
    package_info = get_package_info(package_name)
    return package_info["version"]


def add_package(package_arg: str) -> str:
    """Add a package to package.json."""
    package_name, version = parse_package_name(package_arg)

    if not os.path.exists("package.json"):
        with open("package.json", "w") as f:
            json.dump({"dependencies": {}}, f, indent=2)

    with open("package.json", "r") as f:
        package_data = json.load(f)

    dependencies = package_data.get("dependencies", {})

    if version is None:
        version = get_latest_version(package_name)

    if package_name in dependencies:
        message = f"Package {package_name} already exists. Updating version."
    else:
        message = f"Adding new package {package_name}."

    dependencies[package_name] = f"^{version}"
    package_data["dependencies"] = dependencies

    with open("package.json", "w") as f:
        json.dump(package_data, f, indent=2)

    return f"{message} Added {package_name}@{version} to package.json"
