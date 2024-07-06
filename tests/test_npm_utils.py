import pytest
from unittest.mock import patch, Mock
from src.pyckage.npm_utils import (
    get_package_info,
    parse_version_range,
    find_max_satisfying,
)


@pytest.fixture
def mock_httpx_client():
    with patch("httpx.Client") as mock_client:
        yield mock_client


def test_get_package_info_latest(mock_httpx_client):
    mock_response = Mock()
    mock_response.json.return_value = {
        "dist-tags": {"latest": "1.0.0"},
        "versions": {"1.0.0": {"version": "1.0.0", "name": "test-package"}},
    }
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = (
        mock_response
    )

    result = get_package_info("test-package")
    assert result == {"version": "1.0.0", "name": "test-package"}


def test_get_package_info_specific_version(mock_httpx_client):
    mock_response = Mock()
    mock_response.json.return_value = {
        "versions": {
            "1.0.0": {"version": "1.0.0", "name": "test-package"},
            "1.1.0": {"version": "1.1.0", "name": "test-package"},
        }
    }
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = (
        mock_response
    )

    result = get_package_info("test-package", "1.1.0")
    assert result == {"version": "1.1.0", "name": "test-package"}


def test_get_package_info_version_not_found(mock_httpx_client):
    mock_response = Mock()
    mock_response.json.return_value = {
        "dist-tags": {"latest": "1.1.0"},
        "versions": {
            "1.0.0": {"version": "1.0.0", "name": "test-package"},
            "1.1.0": {"version": "1.1.0", "name": "test-package"},
        },
    }
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = (
        mock_response
    )

    result = get_package_info("test-package", "2.0.0")
    assert result == {"version": "1.1.0", "name": "test-package"}


def test_parse_version_range():
    assert parse_version_range("*") == "latest"
    assert parse_version_range("x") == "latest"
    assert parse_version_range("latest") == "latest"
    assert parse_version_range("1.0.0") == "1.0.0"
    assert parse_version_range("^1.0.0") == "^1.0.0"


def test_find_max_satisfying():
    versions = ["1.0.0", "1.1.0", "1.2.0", "2.0.0"]
    assert find_max_satisfying(versions, "latest") == "2.0.0"
    assert find_max_satisfying(versions, "^1.0.0") == "1.2.0"
    assert find_max_satisfying(versions, "~1.0.0") == "1.0.0"
    assert find_max_satisfying(versions, "1.0.0") == "1.0.0"
