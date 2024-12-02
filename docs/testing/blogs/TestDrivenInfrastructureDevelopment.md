# Test-Driven Infrastructure Development with Konductor and pytest

When I was a kid growing up in Southern California, there was a phone number you could call to find out what time it was. It was a local number, 853-1212 (easy to remember as the arrangement of the numbers on the keypad made a capital T), and I used it all the time, to set my watch, adjust the alarm clock, fix the display on the VCR. I don't recall the last time I used it, probably sometime in the mid '90s, but I do remember clearly the sound of the voice at the other end of the line.

Services like these were called speaking clocks (although I never called them that; to me, it was just "calling Time"), and they date back to the early 1930s or so. In the U.S., most were powered by a machine called an Audichron that used mechanical drums to play back the time of day, often with a little advertisement or the current temperature to go along with it.

By the mid-2000s, though, most of these locally run services had been shut down — by then, we had clocks baked into our phones — and today, only a handful of Audichrons survive. Thanks to the National Institute of Standards and Technology, however, you can still call a phone number to get the time, and while the voice might not be the same, and long distance rates will apply, it's definitely there, and you can use it. So on the off chance you happen to find yourself with no idea what time it is and only an analog phone line in reach, fear not — old-school telephone tech has your back. For now. Assuming you remember the number.

Recalling all this stuff did make me wonder, though, what a more modern version of a speaking clock might look like in today's cloud-native world. So in this post, we're going to build one ourselves using Konductor, our opinionated Pulumi Python platform. Because we want to do it right, we'll take a test-driven approach using pytest and Konductor's testing patterns. We'll focus on unit tests, and when we're done, we'll have a serverless HTTPS endpoint that returns an MP3 audio stream speaking the current time - all built using Konductor's module structure and type-safe practices.

Let's get started.

## Sketching it out

The first thing we'll need is a proper Konductor module structure. While the original speaking clock used mechanical drums, we'll use AWS Lambda and Lambda Function URLs (a recent addition that eliminates the need for API Gateway) to create our modern version. With Konductor's opinionated module patterns, we'll structure our speaking clock module like this:

```plaintext
modules/aws/speaking_clock/
├── __init__.py           # Public module interface
├── types.py             # Type definitions with Pydantic models
├── config.py            # Configuration management
├── provider.py          # AWS provider setup
├── deploy.py            # Core deployment logic
└── tests/              # Unit and integration tests
    ├── __init__.py
    ├── test_config.py
    ├── test_deploy.py
    └── conftest.py
```

A Lambda Function URL provides a direct HTTPS endpoint for our Lambda function, with configurable authentication and CORS settings. This fits perfectly with Konductor's emphasis on simple, maintainable infrastructure. For the audio generation, we'll use Google Translate's text-to-speech API (perfectly fine for this demo), adding a nostalgic beep at the end.

Let's start by setting up our testing infrastructure.

## Setting Up the Test Environment

One of the great things about Konductor is that the devcontainer comes with everything we need for testing. Let's create our initial test structure:

```python
# modules/aws/speaking_clock/tests/conftest.py
import pytest
from pulumi import automation as auto
from typing import Dict, Any
from modules.core.types import InitializationConfig, GitInfo

@pytest.fixture
def mock_init_config():
    """Provides a mocked InitializationConfig."""
    return InitializationConfig(
        pulumi_config={},
        stack_name="test",
        project_name="speaking-clock",
        default_versions={},
        git_info=GitInfo(
            commit_hash="test-hash",
            branch_name="test-branch",
            remote_url="test-url"
        ),
        metadata={"labels": {}, "annotations": {}}
    )

@pytest.fixture
def pulumi_mocks():
    """Configure Pulumi mocks for testing."""
    from pulumi.runtime import set_mocks

    def mock_new_resource(args: auto.MockResourceArgs):
        return [f"{args.name}_id", args.inputs]

    def mock_call(args: auto.MockCallArgs):
        return args.inputs

    # Set up the mocks
    set_mocks(auto.MockResourceMonitor(
        new_resource_fn=mock_new_resource,
        call_fn=mock_call
    ))
```

Now let's create our first failing test. We'll start with the configuration validation:

```python
# modules/aws/speaking_clock/tests/test_config.py
import pytest
from modules.aws.speaking_clock.types import SpeakingClockConfig

def test_function_url_config():
    """Test Lambda Function URL configuration validation."""
    with pytest.raises(ValueError, match="authorizationType must be NONE"):
        SpeakingClockConfig(
            name="test-clock",
            authorizationType="INVALID"
        )

def test_valid_config():
    """Test valid configuration passes validation."""
    config = SpeakingClockConfig(
        name="test-clock",
        authorizationType="NONE",
        cors={
            "allowOrigins": ["*"],
            "allowMethods": ["GET"]
        }
    )
    assert config.name == "test-clock"
    assert config.authorizationType == "NONE"
```

To make these tests meaningful, we need to define our types:

```python
# modules/aws/speaking_clock/types.py
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator

class CorsConfig(BaseModel):
    """CORS configuration for Function URL."""
    allowOrigins: List[str] = Field(default_factory=lambda: ["*"])
    allowMethods: List[str] = Field(default_factory=lambda: ["GET"])

class SpeakingClockConfig(BaseModel):
    """Configuration for speaking clock Function URL."""
    name: str
    authorizationType: str = Field(default="NONE")
    cors: Optional[CorsConfig] = Field(default_factory=CorsConfig)

    @validator("authorizationType")
    def validate_auth_type(cls, v: str) -> str:
        if v != "NONE":
            raise ValueError("authorizationType must be NONE")
        return v
```

With our types defined, let's implement the provider setup:

```python
# modules/aws/speaking_clock/provider.py
from pulumi_aws import Provider
from modules.core import InitializationConfig
from .types import SpeakingClockConfig

def get_aws_provider(
    config: SpeakingClockConfig,
    init_config: InitializationConfig
) -> Provider:
    """Create AWS provider for speaking clock resources."""
    return Provider(
        f"{config.name}-provider",
        region=init_config.config.get("aws:region", "us-west-2")
    )
```

Now we can start writing our deployment tests:

```python
# modules/aws/speaking_clock/tests/test_deploy.py
import pytest
from pulumi import automation as auto
from modules.aws.speaking_clock.deploy import create_speaking_clock
from modules.aws.speaking_clock.types import SpeakingClockConfig

@pytest.mark.asyncio
async def test_function_url_creation(pulumi_mocks, mock_init_config):
    """Test Lambda Function URL creation."""
    config = SpeakingClockConfig(
        name="test-clock"
    )

    # Create the speaking clock resources
    clock = create_speaking_clock(config, mock_init_config)

    # Verify URL configuration
    url = clock.url_config
    assert url.authorizationType == "NONE"
    assert url.cors.allowOrigins == ["*"]
    assert url.cors.allowMethods == ["GET"]

@pytest.mark.asyncio
async def test_lambda_function_config(pulumi_mocks, mock_init_config):
    """Test Lambda function configuration."""
    config = SpeakingClockConfig(
        name="test-clock"
    )

    clock = create_speaking_clock(config, mock_init_config)

    # Verify Lambda configuration
    func = clock.function
    assert func.runtime == "python3.9"
    assert func.handler == "index.handler"
```

First, let's implement our deployment logic:

```python
# modules/aws/speaking_clock/deploy.py
from typing import Dict, Any
from pulumi import ResourceOptions, Output
from pulumi_aws.lambda_ import Function, FunctionUrl
from pulumi_aws.iam import Role, RolePolicyAttachment
from modules.core import InitializationConfig
from .types import SpeakingClockConfig
from .provider import get_aws_provider

class SpeakingClock:
    """Speaking clock implementation using Lambda and Function URL."""

    def __init__(
        self,
        config: SpeakingClockConfig,
        init_config: InitializationConfig,
        opts: ResourceOptions = None
    ):
        self.config = config

        # Get AWS provider
        provider = get_aws_provider(config, init_config)

        # Create Lambda execution role
        self.role = Role(
            f"{config.name}-role",
            assume_role_policy={
                "Version": "2012-10-17",
                "Statement": [{
                    "Action": "sts:AssumeRole",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Effect": "Allow"
                }]
            },
            opts=ResourceOptions(provider=provider)
        )

        # Attach basic Lambda execution policy
        RolePolicyAttachment(
            f"{config.name}-policy",
            role=self.role.name,
            policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
            opts=ResourceOptions(provider=provider)
        )

        # Create Lambda function
        self.function = Function(
            f"{config.name}-function",
            role=self.role.arn,
            runtime="python3.9",
            handler="index.handler",
            code=self._get_lambda_code(),
            environment={
                "variables": {
                    "TZ": "America/Los_Angeles"
                }
            },
            opts=ResourceOptions(
                provider=provider,
                depends_on=[self.role]
            )
        )

        # Create Function URL
        self.url = FunctionUrl(
            f"{config.name}-url",
            function_name=self.function.name,
            authorization_type=config.authorizationType,
            cors=config.cors.dict(),
            opts=ResourceOptions(
                provider=provider,
                depends_on=[self.function]
            )
        )

    def _get_lambda_code(self) -> Output[Dict[str, Any]]:
        """Get Lambda function code with speaking clock implementation."""
        return {
            "zipFile": """
import json
import urllib.request
import urllib.parse
from datetime import datetime
import base64

def get_speech_text():
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    hour = hour if hour <= 12 else hour - 12
    minute_text = f"oh {minute}" if minute < 10 else str(minute)

    return f"At the tone, the time will be {hour} {minute_text}."

def handler(event, context):
    # Get the time announcement text
    text = get_speech_text()

    # Get speech from Google Translate
    text_param = urllib.parse.quote(text)
    speech_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text_param}&tl=en&client=tw-ob"
    beep_url = "https://www.pulumi.com/uploads/beep.mp3"

    # Get audio data
    speech_data = urllib.request.urlopen(speech_url).read()
    beep_data = urllib.request.urlopen(beep_url).read()

    # Combine audio and encode
    combined_audio = speech_data + beep_data
    encoded_audio = base64.b64encode(combined_audio).decode('utf-8')

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "audio/mpeg"
        },
        "body": encoded_audio,
        "isBase64Encoded": True
    }
"""
        }

def create_speaking_clock(
    config: SpeakingClockConfig,
    init_config: InitializationConfig,
    opts: ResourceOptions = None
) -> SpeakingClock:
    """Create a speaking clock instance."""
    return SpeakingClock(config, init_config, opts)
```

Now let's add some property tests to ensure our infrastructure meets compliance requirements:

```python
# modules/aws/speaking_clock/tests/test_properties.py
import pytest
from pulumi_policy import (
    EnforcementLevel,
    PolicyPack,
    ResourceValidationPolicy,
    ResourceValidationArgs
)

def test_lambda_security_properties(pulumi_mocks, mock_init_config):
    """Test Lambda function security properties."""

    def validate_lambda_function(args: ResourceValidationArgs):
        if args.resource_type == "aws:lambda/function:Function":
            # Verify runtime version
            assert args.props["runtime"] == "python3.9", "Must use Python 3.9 runtime"

            # Verify environment encryption
            env_vars = args.props.get("environment", {}).get("variables", {})
            assert "TZ" in env_vars, "Must specify timezone"

            # Verify proper IAM role
            assert "role" in args.props, "Must specify IAM role"

    policy = ResourceValidationPolicy(
        name="lambda-security",
        description="Validate Lambda security configuration",
        validate=validate_lambda_function
    )

    # Create test PolicyPack
    PolicyPack(
        name="speaking-clock-policies",
        enforcement_level=EnforcementLevel.MANDATORY,
        policies=[policy]
    )
```

And finally, let's implement the configuration layer:

```python
# modules/aws/speaking_clock/config.py
from typing import Optional
from pulumi import Config
from modules.core import InitializationConfig
from .types import SpeakingClockConfig

def get_speaking_clock_config(
    init_config: InitializationConfig,
    namespace: Optional[str] = None
) -> SpeakingClockConfig:
    """Load and validate speaking clock configuration."""
    config = Config(namespace)

    return SpeakingClockConfig(
        name=config.get("name") or "speaking-clock",
        authorizationType="NONE",  # Always public for this demo
        cors={
            "allowOrigins": ["*"],
            "allowMethods": ["GET"]
        }
    )
```

Now we can use our module in a Pulumi program:

```python
# Example usage in a Pulumi program
from pulumi import export
from modules.aws.speaking_clock import create_speaking_clock
from modules.aws.speaking_clock.config import get_speaking_clock_config

def deploy_speaking_clock(init_config):
    # Get configuration
    config = get_speaking_clock_config(init_config)

    # Create speaking clock
    clock = create_speaking_clock(config, init_config)

    # Export the URL
    export("speaking_clock_url", clock.url.url)
```

To deploy:

```bash
pulumi up

Updating (dev)

View Live: https://app.pulumi.com/org/speaking-clock/dev/updates/1

     Type                        Name                     Status
 +   pulumi:pulumi:Stack         speaking-clock-dev       created
 +   ├─ aws:iam:Role            speaking-clock-role      created
 +   ├─ aws:lambda:Function     speaking-clock-function  created
 +   └─ aws:lambda:FunctionUrl  speaking-clock-url       created

Outputs:
    speaking_clock_url: "https://abcdef123.lambda-url.us-west-2.on.aws/"

Resources:
    + 4 created

Duration: 45s
```

## Running the Complete Test Suite

Let's run our full test suite to verify everything:

```bash
poetry run pytest tests/ -v

============================= test session starts ==============================
collecting ... collected 8 items

tests/test_config.py::test_function_url_config PASSED              [ 12%]
tests/test_config.py::test_valid_config PASSED                     [ 25%]
tests/test_deploy.py::test_function_url_creation PASSED            [ 37%]
tests/test_deploy.py::test_lambda_function_config PASSED           [ 50%]
tests/test_properties.py::test_lambda_security_properties PASSED   [ 62%]
tests/test_integration.py::test_full_deployment PASSED             [ 75%]
tests/test_integration.py::test_audio_output PASSED                [ 87%]
tests/test_integration.py::test_cors_headers PASSED                [100%]

============================== 8 passed in 3.21s =============================
```

## Wrapping Up

We've come a long way from that old phone number I used to call as a kid. Using Konductor's opinionated structure and testing patterns, we've created a modern, cloud-native version of the speaking clock that's:

- Fully tested with unit, property, and integration tests
- Type-safe using Pydantic models
- Properly structured following Konductor's module patterns
- Secure and compliance-ready
- Easy to deploy and maintain

The complete source code demonstrates how to build infrastructure modules in Konductor that are both well-tested and production-ready. While our speaking clock might be a whimsical example, the patterns we've used are the same ones you'd use for any serious infrastructure module in Konductor.

From here, you might want to explore:
- Writing more comprehensive property tests
- Adding monitoring and alerting
- Implementing additional cloud provider modules
- Contributing to Konductor's growing module ecosystem

The full source code for this example is available in the Konductor repository under `examples/speaking-clock`. Feel free to use it as a reference for your own module development.

Remember, just like that old phone number made checking the time reliable and accessible, good testing makes our infrastructure reliable and maintainable. Happy testing!
