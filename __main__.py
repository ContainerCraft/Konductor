# __main__.py

"""
Main entry point for the Pulumi program.

This entrypoint is an entrypoint for the core module. There is no logic or module
specific code here. Do not enhance this file unless absolutely necessary.

All enhancements should be made to the core module, to provider modules, or to provider
submodule resource and component modules.

Usage:
    poetry install
    poetry shell
    pulumi login
    pulumi stack init <stack_name>
    pulumi stack select <stack_name>
    pulumi config set --path <config_namespace>.<config_key> <config_value>
    pulumi config set --path <config_namespace>.<config_key> <config_value> --secret
    pulumi install
    pulumi preview
    pulumi up
    pulumi destroy
    pulumi stack rm <stack_name>
    pulumi logout
"""

# Import the core module
from src.core import CoreModule


def main():
    """Main entry point for the Pulumi program."""
    # Initialize the core module
    core = CoreModule()

    # Run the core module
    core.run()


# Execute the main function
main()
