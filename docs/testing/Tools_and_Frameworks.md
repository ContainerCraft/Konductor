## Testing Tools and Frameworks

### Core Testing Stack

#### Primary Tools

| Tool | Purpose | Configuration |
|------|---------|--------------|
| pytest | Primary test runner | `pytest.ini`, `conftest.py` |
| pytest-asyncio | Async test support | Plugin configuration |
| pytest-cov | Coverage reporting | `.coveragerc` |
| pulumi | Infrastructure testing | Pulumi configuration |
| black | Code formatting | `pyproject.toml` |
| pylint | Code linting | `.pylintrc` |

#### Configuration Files

1. **pytest.ini**
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
markers =
    unit: Unit tests
    property: Property tests
    integration: Integration tests
    slow: Tests that take longer to run
filterwarnings =
    ignore::DeprecationWarning
    ignore::UserWarning
```

2. **.coveragerc**
```ini
[run]
source = modules
omit =
    tests/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError

[html]
directory = coverage_html
```

3. **pyproject.toml** (Testing Section)
```toml
[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q"
testpaths = [
    "tests",
]

[tool.coverage.run]
source = ["modules"]
omit = ["tests/*"]

[tool.black]
line-length = 88
include = '\.pyi?$'
extend-exclude = '''
# A regex preceded with ^/ will apply only to files and directories
# in the root of the project.
^/tests/fixtures/
'''

[tool.pylint.messages_control]
disable = [
    "C0111",  # missing-docstring
    "C0103",  # invalid-name
    "C0330",  # bad-continuation
    "R0903",  # too-few-public-methods
]
```

### CI/CD Integration

#### GitHub Actions Workflow

```yaml
# .github/workflows/tests.yml
name: Konductor Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      uses: snok/install-poetry@v1
      with:
        version: 1.5.1
        virtualenvs-create: true
        virtualenvs-in-project: true

    - name: Load cached venv
      id: cached-poetry-dependencies
      uses: actions/cache@v2
      with:
        path: .venv
        key: venv-${{ runner.os }}-${{ hashFiles('**/poetry.lock') }}

    - name: Install dependencies
      if: steps.cached-poetry-dependencies.outputs.cache-hit != 'true'
      run: poetry install --no-interaction --no-root

    - name: Run tests
      run: |
        poetry run pytest --cov=modules tests/
        poetry run pytest tests/integration/ --no-cov -v

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: true

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11

    - name: Install Poetry
      uses: snok/install-poetry@v1

    - name: Install dependencies
      run: poetry install --no-interaction --no-root

    - name: Run linters
      run: |
        poetry run black . --check
        poetry run pylint modules/ tests/
```

### Advanced Testing Patterns

#### Test Fixtures Factory

```python
# tests/fixtures/factory.py
import pytest
from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class TestResourceConfig:
    """Test resource configuration."""
    name: str
    type: str
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None

class TestResourceFactory:
    """Factory for creating test resources."""

    @staticmethod
    def create_vpc_config(name: str = "test-vpc") -> TestResourceConfig:
        """Create VPC test configuration."""
        return TestResourceConfig(
            name=name,
            type="aws:ec2/vpc:Vpc",
            inputs={
                "cidrBlock": "10.0.0.0/16",
                "enableDnsHostnames": True,
                "enableDnsSupport": True,
                "tags": {
                    "Name": name,
                    "Environment": "test"
                }
            },
            outputs={
                "id": f"{name}_id",
                "arn": f"arn:aws:ec2:region:account:{name}"
            }
        )

    @staticmethod
    def create_kubernetes_namespace_config(
        name: str = "test-namespace"
    ) -> TestResourceConfig:
        """Create Kubernetes namespace test configuration."""
        return TestResourceConfig(
            name=name,
            type="kubernetes:core/v1:Namespace",
            inputs={
                "metadata": {
                    "name": name,
                    "labels": {
                        "managed-by": "konductor",
                        "environment": "test"
                    }
                }
            },
            outputs={
                "status": {"phase": "Active"}
            }
        )

@pytest.fixture
def resource_factory():
    """Provide test resource factory."""
    return TestResourceFactory
```

#### Parameterized Tests

```python
# tests/core/test_resource_validation.py
import pytest
from modules.core.validation import validate_resource_config

@pytest.mark.parametrize("resource_type,config,expected_valid", [
    (
        "aws:ec2/instance:Instance",
        {
            "instanceType": "t2.micro",
            "tags": {"Name": "test"}
        },
        True
    ),
    (
        "aws:ec2/instance:Instance",
        {
            "instanceType": "t2.micro",
            "userData": "#!/bin/bash\necho hello"
        },
        False
    ),
    (
        "kubernetes:core/v1:Namespace",
        {
            "metadata": {
                "name": "test",
                "labels": {"managed-by": "konductor"}
            }
        },
        True
    ),
])
def test_resource_validation(resource_type, config, expected_valid):
    """Test resource configuration validation."""
    is_valid = validate_resource_config(resource_type, config)
    assert is_valid == expected_valid
```

#### Mock Helpers

```python
# tests/helpers/mocks.py
from typing import Any, Dict, Optional
from pulumi import ResourceOptions

class MockResourceResult:
    """Mock resource creation result."""

    def __init__(
        self,
        name: str,
        type: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        opts: Optional[ResourceOptions] = None
    ):
        self.name = name
        self.type = type
        self.inputs = inputs
        self.outputs = outputs or inputs
        self.opts = opts or ResourceOptions()
        self.id = f"{name}_id"
        self.urn = f"urn:pulumi:{type}::{name}"

def create_mock_outputs(
    outputs: Dict[str, Any]
) -> Dict[str, Any]:
    """Create mock Pulumi outputs."""
    from pulumi import Output
    return {
        k: Output.from_input(v)
        for k, v in outputs.items()
    }

def mock_resource_call(
    resource_type: str,
    name: str,
    inputs: Dict[str, Any],
    opts: Optional[ResourceOptions] = None
) -> MockResourceResult:
    """Mock Pulumi resource creation."""
    return MockResourceResult(
        name=name,
        type=resource_type,
        inputs=inputs,
        opts=opts
    )
```

### Test Result Analysis

#### Coverage Report Generation

```python
# scripts/generate_coverage_report.py
import subprocess
import webbrowser
from pathlib import Path

def generate_coverage_report():
    """Generate and display coverage report."""
    # Run tests with coverage
    subprocess.run([
        "poetry", "run", "pytest",
        "--cov=modules",
        "--cov-report=html",
        "--cov-report=xml",
        "tests/"
    ], check=True)

    # Open coverage report
    report_path = Path("coverage_html/index.html")
    if report_path.exists():
        webbrowser.open(report_path.absolute().as_uri())

if __name__ == "__main__":
    generate_coverage_report()
```

#### Test Result Analyzer

```python
# scripts/analyze_test_results.py
import json
from pathlib import Path
from typing import Dict, List

class TestResultAnalyzer:
    """Analyze test results and generate reports."""

    def __init__(self, results_file: Path):
        self.results_file = results_file
        self.results = self._load_results()

    def _load_results(self) -> Dict:
        """Load test results from file."""
        with open(self.results_file) as f:
            return json.load(f)

    def get_failed_tests(self) -> List[Dict]:
        """Get list of failed tests."""
        return [
            test for test in self.results["tests"]
            if test["outcome"] == "failed"
        ]

    def get_slow_tests(self, threshold: float = 1.0) -> List[Dict]:
        """Get list of slow tests."""
        return [
            test for test in self.results["tests"]
            if test.get("duration", 0) > threshold
        ]

    def generate_report(self) -> Dict:
        """Generate test analysis report."""
        return {
            "total_tests": len(self.results["tests"]),
            "failed_tests": len(self.get_failed_tests()),
            "slow_tests": len(self.get_slow_tests()),
            "total_duration": sum(
                test.get("duration", 0)
                for test in self.results["tests"]
            )
        }

# Usage
if __name__ == "__main__":
    analyzer = TestResultAnalyzer(
        Path(".pytest_cache/v/cache/lastfailed")
    )
    report = analyzer.generate_report()
    print(json.dumps(report, indent=2))
```

### Testing Best Practices

1. **Test Organization**
   - Group tests by functionality
   - Use clear, descriptive test names
   - Maintain test independence
   - Follow naming conventions

2. **Resource Management**
   - Clean up test resources
   - Use smallest viable resources
   - Implement proper error handling
   - Monitor resource costs

3. **Test Data**
   - Use fixtures for test data
   - Implement data factories
   - Maintain test data separately
   - Version control test data

4. **Documentation**
   - Document test purpose
   - Include usage examples
   - Document test dependencies
   - Maintain test documentation

5. **Performance**
   - Optimize test execution
   - Use appropriate test types
   - Implement test parallelization
   - Monitor test duration

6. **Security**
   - Secure test credentials
   - Use test environments
   - Implement access controls
   - Follow security best practices
