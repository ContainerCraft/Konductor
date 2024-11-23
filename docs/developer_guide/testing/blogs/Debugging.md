# Debugging Infrastructure Code with VSCode

1. **Introduction and Setup**
   - Overview of debugging infrastructure code
   - VSCode + Pulumi tools setup
   - Integration with Konductor development environment

2. **Basic Debugging Concepts**
   - Understanding Pulumi execution model
   - Debug session types
   - IDE integration patterns

3. **VSCode-Specific Debugging**
   - Configuration and setup
   - Launch configurations
   - Debug console usage
   - Breakpoint management

4. **Advanced Debugging Techniques**
   - Stack manipulation during debug
   - Resource state inspection
   - Error handling patterns
   - Runtime validation

5. **Troubleshooting Common Issues**
   - Configuration problems
   - Resource creation failures
   - State management issues
   - Provider-specific debugging

6. **Best Practices and Tips**
   - Debugging workflow optimization
   - Performance considerations
   - Security during debug sessions
   - Team debugging patterns

## Introduction

Debugging infrastructure-as-code differs from traditional application debugging. When working with Pulumi programs through Konductor, you're defining infrastructure using Python, but the execution happens through Pulumi's engine. This guide will help you effectively use debugging tools to troubleshoot your infrastructure definitions.

> **Note for Konductor Users**: The devcontainer includes all necessary debugging tools and extensions. No additional installation is required.

## Getting Started with Debugging

### Understanding the Debug Process

Unlike traditional Python applications, you can't directly launch your infrastructure code with F5. Instead, the process works as follows:

1. Pulumi CLI launches your program via the Python runtime
2. Your IDE attaches to this process for debugging
3. The Pulumi engine orchestrates the actual infrastructure operations

This architecture means debugging requires proper configuration of both your IDE and the Pulumi process.

### Setting Up VSCode for Debugging

The Konductor devcontainer comes with the Pulumi VSCode extension preinstalled. When you open your project in the devcontainer, you'll have immediate access to:

- Debug configurations for Pulumi programs
- Stack management interface
- Resource visualization
- Debug console integration

### Starting Your First Debug Session

1. **Open Your Infrastructure Code**
   - Navigate to your module's deployment file
   - Set breakpoints where you want to inspect variables or pause execution

2. **Access Debug Configuration**
   - Click the "Run and Debug" icon in the Activity Bar (or press `Ctrl+Shift+D`)
   - Look for "Show all automatic debug configurations"
   - Select "Pulumi..." followed by either:
     - `pulumi preview` for testing without deployment
     - `pulumi up` for full deployment debugging

3. **Select Your Stack**
   If you haven't already selected a stack, VSCode will prompt you to either:
   - Choose an existing stack
   - Create a new stack for testing

### Debug Console and Output

The Debug Console provides crucial information during your debugging session:

- Pulumi CLI output
- Resource creation/modification status
- Error messages and stack traces
- Variable inspection results

You can access this through:
- View → Debug Console
- Or the Debug Console tab in the lower panel

### Basic Debugging Operations

When your breakpoint is hit, you can:

- Step through code line by line
- Inspect variable values
- View the stack trace
- Evaluate expressions
- Monitor resource states

These operations help you understand:
- How your configuration values are processed
- When and how resources are created
- What data is being passed to Pulumi
- How dependencies are resolved

## Understanding Debug Configurations

While automatic configurations work for basic scenarios, understanding the configuration options helps with more complex debugging needs:

```json
{
    "name": "Pulumi Debug",
    "type": "pulumi",
    "request": "launch",
    "command": "preview",  // or "up"
    "stackName": "dev",    // optional
    "workDir": "${workspaceFolder}",
    "env": {
        "PULUMI_DEBUG": "true"
    }
}
```

Key configuration fields:
- `command`: The Pulumi command to execute
- `stackName`: Target stack (will prompt if omitted)
- `workDir`: Working directory for the command
- `env`: Environment variables for the debug session

## Running Different Debug Modes

### Preview vs. Update Debugging

Understanding when to use each debug mode is crucial:

- **Preview Mode** (`pulumi preview`)
  - Safer for initial debugging
  - Shows planned changes without making them
  - Useful for configuration validation
  - Runs program once

- **Update Mode** (`pulumi up`)
  - Runs your program twice (preview then update)
  - Actually creates/modifies resources
  - Use `--skip-preview` to debug only the update phase
  - Essential for validating resource creation

> **Note**: Your program will hit breakpoints twice during `pulumi up` unless you use the `--skip-preview` flag.

### Running Without Debugging

Sometimes you need to run without the debugger attached. You can:

- Select "Run Without Debugging" from the Run menu
- Add `"noDebug": true` to your launch configuration
- Use the CLI directly in the integrated terminal

## Debug Console Usage

The Debug Console is your window into the Pulumi execution process:

### Viewing Output
- Infrastructure operation logs
- Resource state changes
- Error messages and warnings
- Pulumi engine messages

### Interactive Debugging
- Evaluate expressions during breakpoints
- Check variable values
- Test configuration settings
- Inspect resource properties

## Using Breakpoints Effectively

### Strategic Breakpoint Placement

Place breakpoints at critical points:
- Before resource creation
- During configuration processing
- Where dynamic values are computed
- Error handling sections

### Conditional Breakpoints

VSCode allows setting conditions for breakpoints:
- Break only if a condition is true
- Break when a value changes
- Break after a certain hit count

This is particularly useful when debugging:
- Specific resource types
- Certain configuration values
- Error conditions

## Debug Session Control

### Attach/Detach Behavior

When using `--attach-debugger`:
1. Pulumi pauses execution
2. Waits for debugger connection
3. Continues once attached
4. Maintains connection until completion

### Session Management

During active debugging:
- Use the debug toolbar for control
- Step through code execution
- Jump to specific points
- Restart the debug session if needed

## Alternative Debug Methods

If not using VSCode, you can still debug using:

```bash
pulumi up --attach-debugger
# or
pulumi preview --attach-debugger
```

Then attach your preferred debugger to the Python process.

## IDE Integration Features

### ESC Explorer Integration

The Pulumi extension provides:
- Environment visualization
- Secret management
- Configuration viewing
- Stack management

### Navigation and Reference Features

- Go to Definition
- Find All References
- Symbol search
- Value tracking

### Diff and Compare

Compare different aspects:
- Environment configurations
- Stack states
- Resource definitions
- Configuration revisions

## Debug Process Flow

A typical debug session follows this pattern:

1. **Initialization**
   - Open infrastructure code
   - Set breakpoints
   - Select debug configuration

2. **Execution**
   - Program starts
   - Debugger attaches
   - Breakpoints hit
   - Step through code

3. **Inspection**
   - Check variables
   - Verify resource properties
   - Validate configurations
   - Test conditions

4. **Completion**
   - Resources created/updated
   - Final state verification
   - Debug session ends

## Working with Launch Configurations

### Automatic vs. Custom Configurations

VSCode's Pulumi extension provides two approaches:

1. **Automatic Configurations**
   - Quick start for common scenarios
   - Generated based on project structure
   - Accessible through "Show all automatic debug configurations"
   - Ideal for standard debugging tasks

2. **Custom Launch Configurations**
   - Created in `launch.json`
   - More control over debug behavior
   - Supports environment variables
   - Enables complex debugging scenarios

### Creating Custom Configurations

Access through either:
- Click the gear icon in automatic configuration
- Manually create/edit `launch.json`

Common configuration templates:
```json
{
    "name": "Preview Infrastructure",
    "type": "pulumi",
    "request": "launch",
    "command": "preview"
}
```

```json
{
    "name": "Deploy with Debug",
    "type": "pulumi",
    "request": "launch",
    "command": "up",
    "stackName": "dev",
    "workDir": "${workspaceFolder}/infrastructure"
}
```

## Environment and Stack Management

### Debug Environment Variables

The extension supports environment configuration:
- Set through launch configuration
- Applied only during debug sessions
- Useful for testing different scenarios
- Maintains security of sensitive values

### Stack Selection and Management

During debugging:
- Select stacks directly in VSCode
- Create new stacks for testing
- Switch between stacks
- View stack status

## Using the Pulumi ESC Explorer

### Environment Management

The ESC Explorer provides:
- Visual environment management
- Configuration editing
- Secret handling
- Version control integration

### Key Operations

1. **Environment Creation/Editing**
   - Click '+' to create new environments
   - Edit existing configurations
   - Save revisions
   - Track changes

2. **Environment Operations**
   - Preview configurations
   - Open environments
   - Delete environments
   - Decrypt sensitive data

3. **Version Control**
   - Tag revisions
   - Compare versions
   - Track changes
   - Manage history

### Search and Navigation

The ESC Explorer includes:
- Search functionality for environments
- Quick navigation between configurations
- Filter capabilities
- Reference tracking

## Advanced Debug Features

### Symbol Navigation

The extension enables:
- Go to definition
- Find all references
- Track value usage
- Navigate dependencies

### Comparison Tools

Compare across:
- Environment configurations
- Stack states
- Resource definitions
- Configuration versions

### Terminal Integration

Features include:
- ESC Run command population
- Direct terminal access
- Command history
- Output capture

## Debug Console Enhancement

### Output Management

The Debug Console provides:
- Filtered output views
- Error highlighting
- Stack trace navigation
- Variable inspection

### Interactive Features

During debug sessions:
- Evaluate expressions
- Modify variables
- Test conditions
- Inspect resource states

## Workspace Integration

### Multi-root Workspace Support

The extension handles:
- Multiple projects
- Shared configurations
- Resource dependencies
- Cross-stack references

### Resource Visualization

Provides visibility into:
- Resource relationships
- Configuration hierarchy
- Stack dependencies
- Deployment status

## Debug Session Best Practices

### Session Preparation

1. **Environment Readiness**
   - Ensure clean workspace state
   - Verify stack selection
   - Check configuration values
   - Confirm provider credentials

2. **Breakpoint Strategy**
   - Place strategic breakpoints
   - Use conditional breakpoints wisely
   - Consider resource dependencies
   - Plan for preview vs. update phases

### Debug Workflow Optimization

1. **Preview First**
   ```bash
   # Start with preview to validate configuration
   pulumi preview --attach-debugger
   ```

2. **Targeted Debugging**
   - Debug specific resources
   - Focus on changed components
   - Validate configuration processing
   - Check dependency resolution

3. **Resource State Validation**
   - Monitor state transitions
   - Verify property values
   - Check metadata application
   - Validate tags and labels

## Common Debugging Scenarios

### Configuration Processing

When debugging configuration issues:
1. Set breakpoints in configuration loading
2. Inspect variable values during processing
3. Validate type conversions
4. Check default value application

### Resource Creation Flow

Monitor resource creation:
1. Break before resource definition
2. Inspect input properties
3. Validate dependency order
4. Check resource options

### Error Investigation

When troubleshooting failures:
1. Enable detailed logging
2. Break on error conditions
3. Inspect stack traces
4. Check resource state

## IDE-Specific Features

### VSCode Debug Views

Utilize available views:
- CALL STACK
- WATCH
- VARIABLES
- BREAKPOINTS

### Debug Actions

Common debug operations:
- Continue (F5)
- Step Over (F10)
- Step Into (F11)
- Step Out (Shift+F11)
- Restart (Ctrl+Shift+F5)

## Advanced Debugging Techniques

### Multi-Stack Debugging

When working with multiple stacks:
1. Use clear naming conventions
2. Set stack-specific breakpoints
3. Monitor cross-stack references
4. Validate stack outputs

### Provider Debugging

For provider-specific issues:
1. Enable provider debugging
2. Monitor API calls
3. Validate credentials
4. Check resource specifics

## Debug Output Management

### Console Organization

Organize debug output:
1. Filter relevant information
2. Group related messages
3. Track resource operations
4. Monitor state changes

### Log Level Control

Adjust logging detail:
- ERROR - Critical failures
- WARN - Potential issues
- INFO - General progress
- DEBUG - Detailed information

## Performance Considerations

### Debug Session Impact

Minimize performance impact:
1. Use targeted breakpoints
2. Clear inactive breakpoints
3. Limit watch expressions
4. Close completed sessions

### Resource Management

During debugging:
1. Monitor resource usage
2. Clean up test resources
3. Track session duration
4. Manage stack history

## Security During Debugging

### Credential Management

Protect sensitive information:
1. Use environment variables
2. Leverage secret management
3. Avoid logging credentials
4. Clear debug history

### Access Control

Maintain security during debug:
1. Use least privilege access
2. Monitor resource creation
3. Validate policy compliance
4. Track operation history

## Team Debugging Patterns

### Shared Configurations

When sharing debug configurations:
1. Use version control
2. Document custom settings
3. Maintain consistency
4. Update team documentation

### Collaborative Debugging

For team debugging sessions:
1. Share debug configurations
2. Document breakpoint locations
3. Track investigation progress
4. Maintain session logs

## Documentation and Tracking

### Session Documentation

Record debug sessions:
1. Document findings
2. Track resolution steps
3. Note configuration changes
4. Share team insights

### Issue Tracking

Maintain debugging history:
1. Link to issues
2. Document solutions
3. Track patterns
4. Share learnings

## Recovery and Cleanup

### Session Cleanup

After debugging:
1. Remove breakpoints
2. Clear watch expressions
3. Reset configurations
4. Clean up resources

### State Recovery

Maintain stack health:
1. Verify final state
2. Check resource cleanup
3. Validate configurations
4. Document changes

## Advanced Troubleshooting Patterns

### Pulumi Runtime Analysis

1. **Process Inspection**
   - Monitor Python runtime process
   - Track Pulumi engine execution
   - Observe resource provider interactions
   - Analyze state transitions

2. **State Debugging**
   ```bash
   # Export stack state for analysis
   pulumi stack export > state.json

   # Import after inspection
   pulumi stack import < state.json
   ```

### Cross-Tool Debug Integration

1. **Terminal Integration**
   - Use VSCode integrated terminal
   - Execute Pulumi commands directly
   - Monitor CLI output
   - Capture debug logs

2. **Source Control Debugging**
   - Track configuration changes
   - Compare state versions
   - Review resource modifications
   - Validate deployment history

## Extended IDE Integration

### Additional VSCode Features

1. **Problem Detection**
   - Syntax validation
   - Type checking
   - Resource validation
   - Configuration verification

2. **Integrated Search**
   - Find in files
   - Symbol search
   - Reference tracking
   - Resource location

### External Tool Integration

1. **Cloud Provider Tools**
   - AWS Console integration
   - Azure Portal links
   - GCP Console access
   - Provider-specific logging

2. **Monitoring Integration**
   - Resource health checks
   - Performance monitoring
   - State tracking
   - Alert integration

## Advanced Debug Scenarios

### Complex Resource Dependencies

1. **Dependency Chain Analysis**
   - Track resource relationships
   - Validate creation order
   - Monitor update sequence
   - Verify deletion order

2. **Cross-Stack References**
   - Debug stack references
   - Validate outputs
   - Check input resolution
   - Monitor state sharing

### State Management Issues

1. **State Drift Detection**
   - Compare expected vs. actual state
   - Identify manual changes
   - Track resource modifications
   - Validate metadata

2. **State Recovery**
   - Backup state data
   - Restore previous versions
   - Fix corruption issues
   - Migrate state data

## Integration Patterns

### CI/CD Pipeline Integration

1. **Debug in Pipeline**
   - Configure CI debug mode
   - Capture detailed logs
   - Track deployment steps
   - Monitor resource states

2. **Automated Testing**
   - Integration test debugging
   - Property test validation
   - Resource verification
   - State validation

### External Tool Chains

1. **Log Aggregation**
   - Centralize debug logs
   - Correlate events
   - Track resource changes
   - Monitor state transitions

2. **Monitoring Systems**
   - Resource health tracking
   - Performance monitoring
   - State verification
   - Alert correlation

## Advanced Debug Configurations

### Custom Debug Profiles

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Advanced Debug",
            "type": "pulumi",
            "request": "launch",
            "command": "up",
            "stackName": "dev",
            "env": {
                "PULUMI_DEBUG_LOGGING": "1",
                "PULUMI_PROVIDER_DEBUG": "1"
            },
            "args": [
                "--skip-preview",
                "--debug-logflow"
            ]
        }
    ]
}
```

### Debug Environment Management

1. **Environment Variables**
   - Debug-specific settings
   - Provider configuration
   - Authentication details
   - Logging controls

2. **Configuration Profiles**
   - Development settings
   - Testing configurations
   - Debug-specific values
   - Temporary overrides

## Tool Chain Integration

### Logging Systems

1. **Structured Logging**
   - JSON format logs
   - Timestamp correlation
   - Resource tracking
   - State changes

2. **Log Analysis**
   - Pattern detection
   - Error correlation
   - Performance analysis
   - State tracking

### Monitoring Integration

1. **Resource Health**
   - Status monitoring
   - Performance tracking
   - Dependency validation
   - State verification

2. **Alert Integration**
   - Failure notifications
   - State drift alerts
   - Performance warnings
   - Security notifications

## Debug Workflow Integration

### Development Workflow

1. **Local Development**
   - Quick iterations
   - Rapid testing
   - State validation
   - Configuration testing

2. **Team Collaboration**
   - Shared debugging
   - Knowledge transfer
   - Issue tracking
   - Solution documentation

### Production Support

1. **Live Debugging**
   - Safe investigation
   - State inspection
   - Resource validation
   - Configuration verification

2. **Problem Resolution**
   - Issue tracking
   - Solution implementation
   - State recovery
   - Configuration updates

## Conclusion

The integration of debugging tools and patterns provides a comprehensive environment for troubleshooting infrastructure code. By leveraging these advanced features and integrations, developers can:

- Efficiently identify issues
- Rapidly implement solutions
- Maintain infrastructure stability
- Ensure deployment reliability
- Document resolution patterns
- Share knowledge effectively

Remember that debugging infrastructure code requires careful consideration of:
- Resource state
- Provider interactions
- Configuration management
- Security implications
- Team coordination
- Documentation requirements
