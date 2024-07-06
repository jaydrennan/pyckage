import pytest
import json
import os
from unittest.mock import patch, mock_open
from pyckage.add import parse_package_name, get_latest_version, add_package


def test_parse_package_name():
    assert parse_package_name("react") == ("react", None)
    assert parse_package_name("react@17.0.2") == ("react", "17.0.2")
    assert parse_package_name("@angular/core") == ("@angular/core", None)
    assert parse_package_name("@angular/core@12.0.0") == ("@angular/core", "12.0.0")

    with pytest.raises(ValueError):
        parse_package_name("invalid@package@name")


@patch("pyckage.add.get_package_info")
def test_get_latest_version(mock_get_package_info):
    mock_get_package_info.return_value = {"version": "1.2.3"}
    assert get_latest_version("some-package") == "1.2.3"
    mock_get_package_info.assert_called_once_with("some-package")


@patch("pyckage.add.get_latest_version")
@patch("os.path.exists")
def test_add_package(mock_exists, mock_get_latest_version):
    mock_exists.return_value = True
    mock_get_latest_version.return_value = "2.0.0"

    # Test adding a new package
    with patch("builtins.open", mock_open(read_data='{"dependencies": {}}')):
        result = add_package("react")
    assert result == "Adding new package react. Added react@2.0.0 to package.json"

    # Test updating an existing package
    with patch(
        "builtins.open", mock_open(read_data='{"dependencies": {"react": "^1.0.0"}}')
    ):
        result = add_package("react")
    assert (
        result
        == "Package react already exists. Updating version. Added react@2.0.0 to package.json"
    )

    # Test adding a package with a specific version
    with patch("builtins.open", mock_open(read_data='{"dependencies": {}}')):
        result = add_package("react@17.0.2")
    assert result == "Adding new package react. Added react@17.0.2 to package.json"
