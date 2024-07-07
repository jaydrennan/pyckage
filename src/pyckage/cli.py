#!/usr/bin/env python3
import json
import click
from .add import add_package
from .install import install_packages
from .conflicts import check_and_resolve_conflicts, write_package_lock


@click.group()
def main():
    """pyckage: A basic NodeJS package manager"""
    pass


@main.command()
@click.argument("package_name")
def add(package_name):
    """Add a package to package.json"""
    try:
        message = add_package(package_name)
        click.echo(message)
        click.echo("Package added to package.json. Run 'pyckage install' to install the package.")
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)


@main.command()
def install():
    """Install packages from package.json"""
    try:
        with open("package.json", "r") as f:
            package_json = json.load(f)
        dependencies = package_json.get("dependencies", {})

        resolved, messages, resolved_dependencies = check_and_resolve_conflicts(
            dependencies
        )
        for message in messages:
            click.echo(f"  - {message}")

        if resolved:
            # Update package.json with resolved dependencies
            package_json["dependencies"] = resolved_dependencies
            with open("package.json", "w") as f:
                json.dump(package_json, f, indent=2)
            click.echo("Dependencies updated in package.json")

            # Generate package-lock.json
            write_package_lock(resolved_dependencies)
            click.echo("Generated package-lock.json")

            # Install resolved dependencies
            install_messages = install_packages(resolved_dependencies)
            for message in install_messages:
                click.echo(message)
        else:
            click.echo(
                "Some conflicts could not be automatically resolved. Please review your dependencies."
            )
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        click.echo(f"Full error details: {repr(e)}", err=True)
        import traceback
        click.echo(f"Traceback: {traceback.format_exc()}", err=True)


if __name__ == "__main__":
    main()
