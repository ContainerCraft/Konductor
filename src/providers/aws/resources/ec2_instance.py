# src/providers/aws/resources/ec2_instance.py

"""AWS EC2 instance resource implementation."""

from typing import Dict, Any

from src.core.interfaces.resource import IResource


class EC2Instance(IResource):
    """AWS EC2 instance resource implementation."""

    def __init__(
        self,
        resource_id: str,
        name: str,
        provider_name: str,
        properties: Dict[str, Any]
    ):
        """Initialize the EC2 instance resource.

        Args:
            resource_id: The unique ID of the resource.
            name: The name of the resource.
            provider_name: The name of the provider that created this resource.
            properties: The resource properties.
        """
        self.resource_id = resource_id
        self.name = name
        self.provider_name = provider_name
        self.resource_type = "aws.ec2.instance"
        self.properties = properties
        self.state = "created"

    def get_id(self) -> str:
        """Get the resource ID.

        Returns:
            The resource ID.
        """
        return self.resource_id

    def get_name(self) -> str:
        """Get the resource name.

        Returns:
            The resource name.
        """
        return self.name

    def get_type(self) -> str:
        """Get the resource type.

        Returns:
            The resource type.
        """
        return self.resource_type

    def get_provider(self) -> str:
        """Get the provider name.

        Returns:
            The provider name.
        """
        return self.provider_name

    def get_properties(self) -> Dict[str, Any]:
        """Get the resource properties.

        Returns:
            The resource properties.
        """
        return self.properties

    def update_properties(self, **properties) -> bool:
        """Update the resource properties.

        Args:
            **properties: The properties to update.

        Returns:
            True if the update was successful, False otherwise.
        """
        # In a real implementation, this would update the resource in the cloud
        self.properties.update(properties)
        return True

    def get_state(self) -> str:
        """Get the resource state.

        Returns:
            The resource state.
        """
        return self.state

    def set_state(self, state: str) -> bool:
        """Set the resource state.

        Args:
            state: The new state.

        Returns:
            True if the state was set successfully, False otherwise.
        """
        # In a real implementation, this would change the resource state in the cloud
        self.state = state
        return True
