import json
import os
import httpx
import asyncio
from typing import Dict, List, Set, Optional
from nodesemver import max_satisfying
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

NPM_REGISTRY_URL = "https://registry.npmjs.org"


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


def get_package_info(package_name: str, version: str) -> Dict:
    """Fetch package information from npm registry."""
    try:
        with httpx.Client() as client:
            response = client.get(f"{NPM_REGISTRY_URL}/{package_name}")
            response.raise_for_status()
            package_data = response.json()

        if not isinstance(package_data, dict):
            raise ValueError(f"Invalid package data for {package_name}: Expected a dictionary, got {type(package_data)}")

        if "versions" not in package_data:
            raise ValueError(f"Invalid package data for {package_name}: 'versions' key not found. Keys present: {', '.join(package_data.keys())}")

        available_versions = list(package_data["versions"].keys())

        if version == "latest" or version in ["*", "x"]:
            matching_version = package_data.get("dist-tags", {}).get("latest")
            if not matching_version:
                raise ValueError(f"Latest version not found for {package_name}")
        else:
            matching_version = find_max_satisfying(available_versions, version)

        if not matching_version:
            matching_version = (
                version.lstrip("^~")
                if version.startswith("^") or version.startswith("~")
                else version
            )
            if matching_version not in available_versions:
                print(
                    f"Exact version {matching_version} not found. Using latest version."
                )
                matching_version = package_data.get("dist-tags", {}).get("latest")
                if not matching_version:
                    raise ValueError(f"No suitable version found for {package_name}@{version}")

        print(
            f"Found matching version for {package_name}@{version}: {matching_version}"
        )

        return package_data["versions"][matching_version]
    except Exception as e:
        print(f"Error in get_package_info for {package_name}@{version}: {str(e)}")
        print(f"Package data: {package_data}")
        raise


async def download_package_async(
    package_name: str,
    version: str,
    target_dir: str,
    package_info: Dict,
    progress: Progress,
    task_id: int,
) -> None:
    """Download package asynchronously."""
    tarball_url = package_info["dist"]["tarball"]

    async with httpx.AsyncClient() as client:
        response = await client.get(tarball_url)
        response.raise_for_status()

        package_dir = os.path.join(target_dir, package_name)
        os.makedirs(package_dir, exist_ok=True)

        file_path = os.path.join(package_dir, f"{package_name}-{version}.tgz")
        with open(file_path, "wb") as f:
            f.write(response.content)

        progress.update(task_id, advance=1)

    # Note: In a real implementation, you would extract the tarball here


def install_package(
    package_name: str,
    version: str,
    node_modules_dir: str,
    installed: Set[str],
    download_queue: List,
) -> None:
    """Prepare a package and its dependencies for installation."""
    package_key = f"{package_name}@{version}"

    if package_key in installed:
        return

    try:
        package_info = get_package_info(package_name, version)
        actual_version = package_info["version"]
        actual_package_key = f"{package_name}@{actual_version}"

        if actual_package_key in installed:
            return

        download_queue.append(
            (package_name, actual_version, node_modules_dir, package_info)
        )
        installed.add(actual_package_key)

        dependencies = package_info.get("dependencies", {})

        for dep_name, dep_version in dependencies.items():
            install_package(
                dep_name, dep_version, node_modules_dir, installed, download_queue
            )
    except Exception as e:
        print(
            f"Warning: Could not prepare {package_name}@{version} for installation. Error: {str(e)}"
        )


def install_packages(resolved_dependencies=None) -> List[str]:
    """Install packages from package.json or resolved dependencies."""
    try:
        if resolved_dependencies is None:
            if not os.path.exists("package.json"):
                raise FileNotFoundError(
                    "package.json not found. Initialize your project first."
                )

            with open("package.json", "r") as f:
                package_data = json.load(f)

            dependencies = package_data.get("dependencies", {})
        else:
            dependencies = resolved_dependencies

        if not dependencies:
            return ["No dependencies found to install"]

        node_modules_dir = "node_modules"
        os.makedirs(node_modules_dir, exist_ok=True)

        installed = set()
        download_queue = []
        messages = []

        for package_name, version in dependencies.items():
            try:
                print(f"Preparing to install {package_name}@{version}")
                install_package(
                    package_name, version, node_modules_dir, installed, download_queue
                )
            except Exception as e:
                print(f"Error installing {package_name}@{version}: {str(e)}")
                print(f"Full error for {package_name}: {repr(e)}")
                raise

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task = progress.add_task("Downloading packages", total=len(download_queue))

            async def download_all():
                await asyncio.gather(
                    *[
                        download_package_async(
                            package_name, version, target_dir, package_info, progress, task
                        )
                        for package_name, version, target_dir, package_info in download_queue
                    ]
                )

            asyncio.run(download_all())

        messages.append(f"Installed {len(installed)} packages")
        return messages
    except Exception as e:
        print(f"Error in install_packages: {str(e)}")
        print(f"Full error: {repr(e)}")
        raise
