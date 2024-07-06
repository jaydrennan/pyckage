import json
import pytest
from click.testing import CliRunner
from pyckage.cli import main, add, install


@pytest.fixture
def runner():
    return CliRunner()


def test_add_command(runner, mocker):
    mocker.patch("pyckage.cli.add_package", return_value="Package added successfully")

    with runner.isolated_filesystem():
        # Create a mock package.json file
        with open("package.json", "w") as f:
            json.dump({"dependencies": {}}, f)

        result = runner.invoke(add, ["new-package"])

    assert result.exit_code == 0
    assert "Package added successfully" in result.output
    assert "Package added to package.json. Run 'pyckage install' to install the package." in result.output


def test_add_command_with_error(runner, mocker):
    mocker.patch("pyckage.cli.add_package", side_effect=Exception("Test error"))

    result = runner.invoke(add, ["error-package"])

    assert result.exit_code == 0
    assert "Error: Test error" in result.output


def test_install_command(runner, mocker):
    mocker.patch(
        "pyckage.cli.check_and_resolve_conflicts",
        return_value=(True, ["Conflict resolved"], {"package": "1.0.0"}),
    )
    mocker.patch("pyckage.cli.install_packages", return_value=["Package installed"])

    with runner.isolated_filesystem():
        # Create a mock package.json file
        with open("package.json", "w") as f:
            json.dump({"dependencies": {"package": "1.0.0"}}, f)

        result = runner.invoke(install)

    assert result.exit_code == 0
    assert "Conflict resolved" in result.output
    assert "Dependencies updated in package.json" in result.output
    assert "Package installed" in result.output


def test_install_command_with_conflict(runner, mocker):
    mocker.patch(
        "pyckage.cli.check_and_resolve_conflicts",
        return_value=(False, ["Conflict detected"], {}),
    )

    with runner.isolated_filesystem():
        # Create a mock package.json file
        with open("package.json", "w") as f:
            json.dump({"dependencies": {}}, f)

        result = runner.invoke(install)

    assert result.exit_code == 0
    assert "Conflict detected" in result.output
    assert "Some conflicts could not be automatically resolved" in result.output


def test_main_command(runner):
    result = runner.invoke(main)
    assert result.exit_code == 0
    assert "pyckage: A basic NodeJS package manager" in result.output
