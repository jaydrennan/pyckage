import json
from typing import Dict, List, Tuple, Set
from .npm_utils import get_package_info, find_max_satisfying


def check_conflicts(dependencies: Dict[str, str]) -> List[str]:
    """Check for conflicts in the given dependencies."""
    return find_conflicts(dependencies)


def find_conflicts(dependencies: Dict[str, str]) -> List[str]:
    """Find conflicts in the given dependencies."""
    conflicts = []
    dependency_tree = build_dependency_tree(dependencies)

    for package, versions in dependency_tree.items():
        if len(versions) > 1:
            conflict = f"Package '{package}' has conflicting version requirements: {', '.join(versions)}"
            conflicts.append(conflict)

    return conflicts


def build_dependency_tree(dependencies: Dict[str, str]) -> Dict[str, List[str]]:
    """Build a dependency tree including nested dependencies."""
    dependency_tree = {}
    visited = set()

    for package, version_range in dependencies.items():
        add_to_dependency_tree(dependency_tree, package, version_range, visited)

    return dependency_tree


def add_to_dependency_tree(
    tree: Dict[str, List[str]],
    package: str,
    version_range: str,
    visited: Set[str] = None,
):
    """Recursively add a package and its dependencies to the dependency tree."""
    if visited is None:
        visited = set()

    if package in visited:
        return

    visited.add(package)

    if package not in tree:
        tree[package] = []

    if version_range not in tree[package]:
        tree[package].append(version_range)

    package_info = get_package_info(package, version_range)
    nested_dependencies = package_info.get("dependencies", {})

    for nested_package, nested_version_range in nested_dependencies.items():
        add_to_dependency_tree(tree, nested_package, nested_version_range, visited)


def resolve_conflicts(conflicts: List[str]) -> Tuple[bool, List[str], Dict[str, str]]:
    """Attempt to resolve conflicts by finding compatible versions."""
    resolved = []
    unresolved = []
    resolved_dependencies = {}

    for conflict in conflicts:
        package = conflict.split("'")[1]
        versions = [v.strip() for v in conflict.split(":")[1].split(",")]

        compatible_version = find_compatible_version(package, versions)
        if compatible_version:
            resolved.append(
                f"Resolved conflict for '{package}': using version {compatible_version}"
            )
            resolved_dependencies[package] = compatible_version
        else:
            unresolved.append(conflict)

    return len(unresolved) == 0, resolved + unresolved, resolved_dependencies


def find_compatible_version(package: str, version_ranges: List[str]) -> str:
    """Find a compatible version that satisfies all given version ranges."""
    package_info = get_package_info(package)
    all_versions = list(package_info["versions"].keys())

    compatible_versions = []
    for version in all_versions:
        if all(find_max_satisfying([version], range_) for range_ in version_ranges):
            compatible_versions.append(version)

    if compatible_versions:
        return find_max_satisfying(
            compatible_versions, "^" + min(version_ranges).lstrip("^")
        )

    return None


def check_and_resolve_conflicts(
    dependencies: Dict[str, str],
) -> Tuple[bool, List[str], Dict[str, str]]:
    """Check for conflicts and attempt to resolve them."""
    conflicts = check_conflicts(dependencies)
    if conflicts:
        return resolve_conflicts(conflicts)
    return True, ["No conflicts detected."], dependencies
