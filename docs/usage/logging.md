# Logging System

## Overview

The Core Module implements a standardized logging system that provides consistent logging capabilities across all provider modules and submodules. The logging system is built on top of Python's native logging module and provides additional functionality for controlling log output verbosity based on component types.

## Configuration

The logging level can be configured in two ways:

1. **Environment Variables**: Setting the `PULUMI_LOG_LEVEL` environment variable (highest priority)
2. **Pulumi Stack Configuration**: Setting the `logging.level` property in the stack YAML file

Example stack configuration:

```yaml
config:
  # Logging configuration
  logging:
    level: "info"  # debug, info, warning, error, critical
```

## Log Levels

The following log levels are supported, in order of increasing severity:

- `debug`: Detailed information, typically useful only for diagnosing problems
- `info`: Confirmation that things are working as expected
- `warning`: Indication that something unexpected happened, but the program is still working
- `error`: Due to a more serious problem, the program has not been able to perform some function
- `critical`: A serious error, indicating that the program itself may be unable to continue running

## Component Classification

The logging system classifies components into different categories to control verbosity:

1. **Verbose Components**: Components that generate a lot of detailed logs. These components only log at `WARNING` or higher severity by default, but log everything in `debug` mode.
   - `provider_discovery`
   - `provider_registry`
   - `config_manager`

2. **Standard Info Components**: Components that always log at `INFO` level or higher, regardless of the default log level.
   - `core`

3. **Other Components**: All other components use the configured default log level.

## Development Tips

1. For development and debugging, create a `dev` stack with debug-level logging:

```bash
pulumi stack init dev
# Configure debug logging in the Pulumi.dev.yaml
```

2. For production deployments, maintain separate stacks with appropriate logging levels:

```bash
pulumi stack init production
# Configure info or warning level logging in the Pulumi.production.yaml
```

3. To temporarily enable debug logging for troubleshooting:

```bash
PULUMI_LOG_LEVEL=debug pulumi up
```

## Best Practices

1. Use the appropriate log level for each message:
   - `debug`: Detailed information for developers
   - `info`: General operational information
   - `warning`: Non-critical issues that should be reviewed
   - `error`: Significant problems that need attention
   - `critical`: Severe errors that prevent continued operation

2. Always obtain loggers through the LogManager to ensure consistent configuration:

```python
log_manager = LogManager(log_level="info")
logger = log_manager.get_logger("my_component")
```

3. Include contextual information in log messages to make them more useful for troubleshooting.
