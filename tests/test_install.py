import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from pyckage.install import (
    parse_version_range,
    find_max_satisfying,
    get_package_info,
    install_package,
    install_packages,
)


@pytest.fixture
def mock_httpx_client():
    with patch("pyckage.install.httpx.Client") as mock_client:
        yield mock_client


@pytest.fixture
def mock_package_json():
    package_json = {"dependencies": {"package1": "^1.0.0", "package2": "2.0.0"}}
    with patch("builtins.open", new_callable=MagicMock()) as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
            package_json
        )
        yield package_json


def test_parse_version_range():
    assert parse_version_range("*") == "latest"
    assert parse_version_range("x") == "latest"
    assert parse_version_range("latest") == "latest"
    assert parse_version_range("^1.0.0") == "^1.0.0"


def test_find_max_satisfying():
    versions = ["1.0.0", "1.1.0", "2.0.0", "2.1.0"]
    assert find_max_satisfying(versions, "^1.0.0") == "1.1.0"
    assert find_max_satisfying(versions, "~2.0.0") == "2.0.0"
    assert find_max_satisfying(versions, "latest") == "2.1.0"
    assert find_max_satisfying(versions, "3.0.0") is None


def test_get_package_info(mock_httpx_client):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "versions": {
            "1.0.0": {"version": "1.0.0"},
            "1.1.0": {"version": "1.1.0"},
        },
        "dist-tags": {"latest": "1.1.0"},
    }
    mock_httpx_client.return_value.__enter__.return_value.get.return_value = (
        mock_response
    )

    result = get_package_info("test-package", "1.0.0")
    assert result == {"version": "1.0.0"}

    result = get_package_info("test-package", "latest")
    assert result == {"version": "1.1.0"}


@patch("pyckage.install.get_package_info")
def test_install_package(mock_get_package_info):
    mock_get_package_info.return_value = {
        "version": "1.0.0",
        "dependencies": {"dep1": "2.0.0"},
    }
    installed = set()
    download_queue = []
    install_package("test-package", "1.0.0", "node_modules", installed, download_queue)

    assert "test-package@1.0.0" in installed
    assert len(download_queue) == 2  # test-package and its dependency


@patch("pyckage.install.asyncio.run")
@patch("pyckage.install.Progress")
@patch("pyckage.install.install_package")
@patch("pyckage.install.os.makedirs")
@patch("pyckage.install.os.path.exists")
def test_install_packages(
    mock_exists,
    mock_makedirs,
    mock_install_package,
    mock_progress,
    mock_asyncio_run,
    mock_package_json,
):
    mock_exists.return_value = True
    mock_progress.return_value.__enter__.return_value.add_task.return_value = 1

    # Simulate install_package adding to the installed set
    def side_effect(package_name, version, node_modules_dir, installed, download_queue):
        installed.add(f"{package_name}@{version}")
        download_queue.append((package_name, version, node_modules_dir, {}))

    mock_install_package.side_effect = side_effect

    # Mock the asyncio.run to actually run the coroutine
    async def mock_download_all():
        pass

    mock_asyncio_run.side_effect = (
        lambda x: asyncio.get_event_loop().run_until_complete(mock_download_all())
    )

    result = install_packages()

    assert mock_install_package.call_count == 2  # Called for each dependency
    assert mock_makedirs.called
    assert "Installed 2 packages" in result[0]
    assert mock_asyncio_run.called


@patch("pyckage.install.os.path.exists")
def test_install_packages_no_package_json(mock_exists):
    mock_exists.return_value = False
    with pytest.raises(FileNotFoundError):
        install_packages()


# Add more tests as needed for edge cases and error handling
