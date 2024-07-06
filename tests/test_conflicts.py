import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from src.pyckage.conflicts import (
    check_conflicts,
    find_conflicts,
    build_dependency_tree,
    add_to_dependency_tree,
    resolve_conflicts,
    find_compatible_version,
    check_and_resolve_conflicts,
)
from src.pyckage.npm_utils import find_max_satisfying


@pytest.fixture
def mock_package_json():
    return {"dependencies": {"package-a": "^1.0.0", "package-b": "^2.0.0"}}


@pytest.fixture
def mock_dependency_tree():
    return {
        "package-a": ["^1.0.0", "^1.2.0"],
        "package-b": ["^2.0.0"],
        "package-c": ["^1.0.0", "^2.0.0"],
    }


def test_check_conflicts(mock_package_json):
    with patch("src.pyckage.conflicts.find_conflicts") as mock_find_conflicts:
        mock_find_conflicts.return_value = ["Conflict 1", "Conflict 2"]
        conflicts = check_conflicts(mock_package_json["dependencies"])
        assert conflicts == ["Conflict 1", "Conflict 2"]
        mock_find_conflicts.assert_called_once_with(mock_package_json["dependencies"])


def test_find_conflicts(mock_dependency_tree):
    with patch("src.pyckage.conflicts.build_dependency_tree") as mock_build_tree:
        mock_build_tree.return_value = mock_dependency_tree
        conflicts = find_conflicts({"package-a": "^1.0.0", "package-b": "^2.0.0"})
        assert len(conflicts) == 2
        assert "package-a" in conflicts[0]
        assert "package-c" in conflicts[1]


def test_build_dependency_tree():
    with patch("src.pyckage.conflicts.add_to_dependency_tree") as mock_add:
        dependencies = {"package-a": "^1.0.0", "package-b": "^2.0.0"}
        build_dependency_tree(dependencies)
        assert mock_add.call_count == 2


@patch("src.pyckage.conflicts.get_package_info")
def test_add_to_dependency_tree(mock_get_package_info):
    mock_get_package_info.return_value = {"dependencies": {"nested-package": "^1.0.0"}}
    tree = {}
    visited = set()
    add_to_dependency_tree(tree, "package-a", "^1.0.0", visited)
    assert tree == {"package-a": ["^1.0.0"], "nested-package": ["^1.0.0"]}
    assert visited == {"package-a", "nested-package"}


def test_resolve_conflicts():
    conflicts = [
        "Package 'package-a' has conflicting version requirements: ^1.0.0, ^1.2.0",
        "Package 'package-b' has conflicting version requirements: ^2.0.0, ^3.0.0",
    ]
    with patch("src.pyckage.conflicts.find_compatible_version") as mock_find:
        mock_find.side_effect = ["1.2.3", None]
        resolved, messages, resolved_deps = resolve_conflicts(conflicts)
        assert not resolved
        assert len(messages) == 2
        assert "Resolved conflict for 'package-a'" in messages[0]
        assert "Package 'package-b' has conflicting version requirements" in messages[1]
        assert resolved_deps == {"package-a": "1.2.3"}


@patch("src.pyckage.conflicts.get_package_info")
@patch("src.pyckage.conflicts.find_max_satisfying")
def test_find_compatible_version(mock_find_max_satisfying, mock_get_package_info):
    mock_get_package_info.return_value = {
        "versions": {"1.0.0": {}, "1.1.0": {}, "1.2.0": {}}
    }

    def mock_find_max(versions, range_, **kwargs):
        satisfying = [v for v in versions if v.startswith(range_[1])]
        return max(satisfying) if satisfying else None

    mock_find_max_satisfying.side_effect = mock_find_max

    result = find_compatible_version("package-a", ["^1.0.0", "^1.1.0"])
    assert result == "1.2.0"

    result = find_compatible_version("package-b", ["^1.0.0", "^2.0.0"])
    assert result is None

    mock_get_package_info.return_value = {
        "versions": {"1.0.0": {}, "1.1.0": {}, "1.2.0": {}}
    }
    result = find_compatible_version("package-c", ["^1.0.0", "^1.1.0"])
    assert result == "1.2.0"

    versions = ["1.2.3", "1.2.4", "1.2.5", "1.2.6", "2.0.1"]
    assert find_max_satisfying(versions, "~1.2.3") == "1.2.6"

    versions = ["1.1.0", "1.2.0", "1.2.1", "1.3.0", "2.0.0", "2.1.0"]
    assert find_max_satisfying(versions, "~2.0.0") == "2.0.0"


def test_check_and_resolve_conflicts_no_conflicts(mock_package_json):
    with patch("src.pyckage.conflicts.check_conflicts") as mock_check:
        mock_check.return_value = []
        resolved, messages, resolved_deps = check_and_resolve_conflicts(
            mock_package_json["dependencies"]
        )
        assert resolved == True
        assert messages == ["No conflicts detected."]
        assert resolved_deps == mock_package_json["dependencies"]


def test_check_and_resolve_conflicts_with_resolvable_conflicts():
    dependencies = {"package-a": "^1.0.0", "package-b": "^2.0.0"}
    conflicts = [
        "Package 'package-a' has conflicting version requirements: ^1.0.0, ^1.2.0"
    ]
    with patch("src.pyckage.conflicts.check_conflicts") as mock_check:
        with patch("src.pyckage.conflicts.resolve_conflicts") as mock_resolve:
            mock_check.return_value = conflicts
            mock_resolve.return_value = (
                True,
                ["Resolved conflict for 'package-a': using version 1.2.3"],
                {"package-a": "1.2.3", "package-b": "^2.0.0"},
            )

            resolved, messages, resolved_deps = check_and_resolve_conflicts(
                dependencies
            )

            assert resolved == True
            assert "Resolved conflict for 'package-a'" in messages[0]
            assert resolved_deps == {"package-a": "1.2.3", "package-b": "^2.0.0"}


def test_check_and_resolve_conflicts_with_unresolvable_conflicts():
    dependencies = {"package-a": "^1.0.0", "package-b": "^2.0.0"}
    conflicts = [
        "Package 'package-a' has conflicting version requirements: ^1.0.0, ^2.0.0",
        "Package 'package-b' has conflicting version requirements: ^2.0.0, ^3.0.0",
    ]
    with patch("src.pyckage.conflicts.check_conflicts") as mock_check:
        with patch("src.pyckage.conflicts.resolve_conflicts") as mock_resolve:
            mock_check.return_value = conflicts
            mock_resolve.return_value = (False, conflicts, {})

            resolved, messages, resolved_deps = check_and_resolve_conflicts(
                dependencies
            )

            assert resolved == False
            assert len(messages) == 2
            assert (
                "Package 'package-a' has conflicting version requirements"
                in messages[0]
            )
            assert (
                "Package 'package-b' has conflicting version requirements"
                in messages[1]
            )
            assert resolved_deps == {}