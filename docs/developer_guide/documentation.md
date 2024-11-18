# Konductor Documentation Style Guide

## Introduction

This style guide establishes standards for creating and maintaining documentation within the Konductor project. It ensures consistency, clarity, and accessibility across all documentation while aligning with the project's technical standards outlined in `PULUMI_PYTHON.md`.

This guide is intended for all contributors, including developers, documentation writers, and content engineers. By following these guidelines, we ensure that our documentation is user-friendly, maintainable, and helpful to both new and experienced users of the Konductor platform.

## Table of Contents

1. [General Principles](#general-principles)
2. [Document Structure](#document-structure)
3. [Writing Style](#writing-style)
4. [Formatting Standards](#formatting-standards)
5. [Code Examples](#code-examples)
6. [Code Commenting and Docstrings](#code-commenting-and-docstrings)
7. [Links and References](#links-and-references)
8. [Images and Diagrams](#images-and-diagrams)
9. [Accessibility Guidelines](#accessibility-guidelines)
10. [Version Control](#version-control)
11. [File Organization](#file-organization)
12. [Documentation Workflow and Maintenance](#documentation-workflow-and-maintenance)
13. [Conclusion](#conclusion)
14. [Related Documents](#related-documents)

## General Principles

### Clarity

- **Know Your Audience**: Write for your audience's knowledge level, which may range from junior developers to experienced platform engineers.
- **Define Technical Terms**: Introduce and define technical terms on their first use.
- **Consistent Terminology**: Use consistent terminology throughout the documentation.
- **Avoid Unnecessary Jargon**: Use simple language whenever possible and avoid unnecessary jargon.

### Completeness

- **Comprehensive Coverage**: Include all necessary information to understand the topic fully.
- **Contextual Information**: Provide context for technical concepts to help users understand why and how something works.
- **Link to Related Content**: Reference related documentation, tutorials, or external resources.
- **Troubleshooting Guidance**: Include troubleshooting tips and common issues where applicable.

### Maintainability

- **Modular Content**: Keep content modular to facilitate updates and reuse.
- **Use Relative Links**: Use relative links for internal references to maintain link validity across branches and forks.
- **DRY Principle**: Follow the Don't Repeat Yourself principle to avoid duplication.
- **Regular Updates**: Review and update documentation regularly to keep it current.

### Accessibility

- **Inclusive Language**: Use inclusive language and avoid bias.
- **Alternative Text**: Provide alternative text for images and diagrams.
- **Clear Structure**: Organize content logically with appropriate headings.
- **Usability**: Ensure that documentation is easy to navigate and understand.

## Document Structure

### Required Sections

1. **Title**: Clear, descriptive title using H1 (`#`).
2. **Introduction**: Brief overview of the document's purpose and scope.
3. **Table of Contents**: For documents longer than three sections.
4. **Prerequisites** (if applicable): Required knowledge, software, or setup before proceeding.
5. **Main Content**: Organized into logical sections with clear headings.
6. **Conclusion** (if applicable): Summary of key points or next steps.
7. **Related Resources**: Links to related documentation, tutorials, or external resources.

### Header Hierarchy

Use the following hierarchy for headings:

```markdown
# Document Title (H1)
## Section Title (H2)
### Sub-section Title (H3)
#### Minor Sub-section Title (H4)
##### Sub-sub-section Title (H5)
```

### Metadata Block (Optional)

Include a metadata block at the beginning of the document if additional context is needed:

```yaml
---
title: Document Title
description: Brief description of the document
authors: [Author Name]
date: YYYY-MM-DD
version: 0.0.1
---
```

## Writing Style

### Voice and Tone

- **Active Voice**: Use active voice to make sentences clear and direct.
- **Conciseness**: Be direct and concise; avoid unnecessary words.
- **Professional and Friendly Tone**: Maintain a professional tone while being approachable.
- **Present Tense**: Write in the present tense when possible.

### Language

- **Consistency**: Use consistent terminology and style throughout the documentation.
- **Imperative Mood**: Use the imperative mood for instructions (e.g., "Install the package by running...").
- **Avoid Ambiguity**: Be specific to avoid confusion.

### Paragraphs

- **Focused Paragraphs**: Keep paragraphs focused on a single idea or topic.
- **Short Paragraphs**: Use short paragraphs (3-5 sentences) to enhance readability.
- **Transitions**: Include transition sentences or phrases to connect ideas between paragraphs and sections.

### Lists

- **Bullet Points**: Use bullet points for unordered lists or items that do not require a specific order.
- **Numbered Lists**: Use numbered lists for sequential steps or when order is important.
- **Parallel Structure**: Ensure that list items have a parallel grammatical structure.

## Formatting Standards

### Text Formatting

- **Bold**: Use bold text for emphasis, UI elements (e.g., button names), and important terms.
- *Italic*: Use italics when introducing new terms or for light emphasis.
- `Code`: Use inline code formatting for code snippets, file names, commands, and configuration keys.
- ***Bold Italic***: Avoid using bold italic text unless necessary.

### Headings

- **Capitalization**: Use sentence case for headings (capitalize only the first word and proper nouns).
- **Avoid Punctuation**: Do not include periods at the end of headings.

### Code Blocks

- **Syntax Highlighting**: Use triple backticks with the language identifier for syntax highlighting.
- **Description**: Include a brief description or comment explaining the purpose of the code.
- **Line Numbers**: For longer code snippets, consider adding line numbers for reference.
- **Avoid Horizontal Scrolling**: Ensure code fits within the page width; break long lines if necessary.

Example:

```python
# Example code block: Function to calculate factorial
def factorial(n: int) -> int:
    """Calculate the factorial of a non-negative integer n."""
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)
```

### Tables

- **Usage**: Use tables for presenting structured data that is best displayed in rows and columns.
- **Header Row**: Include a header row to label columns.
- **Alignment**: Align columns consistently; left-align text for readability.

Example:

| Configuration Option | Type   | Description                          |
|----------------------|--------|--------------------------------------|
| `enabled`            | bool   | Whether the feature is enabled       |
| `timeout`            | int    | Timeout duration in seconds          |
| `retry_attempts`     | int    | Number of retry attempts on failure  |

## Code Examples

### General Guidelines

- **Relevance**: Ensure examples are relevant to the context and demonstrate best practices.
- **Simplicity**: Keep examples simple and focused on the key concept.
- **Clarity**: Include comments explaining key concepts or steps.
- **Consistency**: Use consistent code formatting and style, following the project's coding standards.

### Example Structure

- **Imports**: Include necessary imports for the code to be self-contained.
- **Docstrings and Comments**: Use docstrings and inline comments to explain the code.
- **Meaningful Names**: Use descriptive variable and function names.

Example:

```python
from typing import TypedDict, Optional

class ConfigExample(TypedDict):
    """Example configuration structure.

    Attributes:
        name: The name of the resource.
        enabled: Indicates if the resource is enabled.
    """
    name: str
    enabled: bool

def example_function(config: ConfigExample) -> None:
    """Process the configuration and print the resource status.

    Args:
        config: A configuration dictionary containing 'name' and 'enabled'.
    """
    if config.get("enabled", True):
        print(f"Resource '{config['name']}' is enabled.")
    else:
        print(f"Resource '{config['name']}' is disabled.")
```

## Code Commenting and Docstrings

### Docstring Standards

- **Purpose**: Every module, class, and function/method should have a docstring that describes its purpose and usage.
- **Style**: Use triple double-quotes (`"""`) for docstrings.
- **Content**:
  - **Modules**: Describe the module's purpose and main functionalities.
  - **Classes**: Provide an overview of the class, its responsibilities, and any important details.
  - **Functions/Methods**: Explain what the function does, its parameters, return values, exceptions raised, and any side effects.

### Docstring Format

- **Summary Line**: Begin with a concise summary of the object.
- **Blank Line**: Add a blank line after the summary.
- **Details**: Provide more detailed information if necessary.
- **Args**: List and describe each parameter.
- **Returns**: Describe the return value.
- **Raises**: List any exceptions that the function may raise.

Example:

```python
def connect_to_database(host: str, port: int) -> DatabaseConnection:
    """Establish a connection to the database.

    Args:
        host: The hostname of the database server.
        port: The port number on which the database is listening.

    Returns:
        A DatabaseConnection object representing the connection.

    Raises:
        ConnectionError: If the connection cannot be established.
    """
    # Function implementation
```

### Inline Comments

- **Usage**: Use inline comments sparingly to explain complex logic or important details not immediately apparent from the code.
- **Placement**: Place the comment above the code line or at the end of the line if brief.
- **Clarity**: Ensure comments are clear and add value beyond what the code expresses.

Example:

```python
# Calculate the Fibonacci sequence up to n terms
def fibonacci(n: int) -> List[int]:
    sequence = [0, 1]
    for _ in range(2, n):
        # Append the sum of the last two numbers
        sequence.append(sequence[-1] + sequence[-2])
    return sequence
```

### Code Formatting

- **Consistency**: Follow the project's coding standards as outlined in `PULUMI_PYTHON.md`.
- **PEP 8 Compliance**: Adhere to the PEP 8 style guide for Python code.
- **Type Annotations**: Use type hints consistently.
- **Linting**: Ensure code passes linting checks (e.g., using `flake8` or `pylint`).

## Links and References

### Internal Links

- **Relative Paths**: Use relative paths for internal links to ensure they work across branches and forks.
- **Section Links**: Link to specific sections using the heading text converted to lowercase and spaces replaced with hyphens (e.g., `#section-title`).
- **Validity**: Regularly check links to ensure they are valid and not broken.

Example:

- `[Introduction](#introduction)`
- `[PULUMI_PYTHON.md](../reference/PULUMI_PYTHON.md)`

### External Links

- **Descriptive Text**: Use link text that describes the content of the linked page.
- **Target Stability**: Prefer linking to stable URLs that are unlikely to change.
- **Notes on External Dependencies**: If the link is to an external dependency or resource, consider including the version or date accessed.

Example:

- `[Pulumi Documentation](https://www.pulumi.com/docs/)`

### Cross-References

- **Consistent Terminology**: Use the same terms when referring to concepts or components.
- **Glossary Terms**: Link to definitions of terms in a glossary if available.
- **Related Documentation**: Reference related guides or tutorials to provide additional context.

## Images and Diagrams

### Requirements

- **Format**: Use SVG format for diagrams when possible to ensure scalability.
- **Alternative Text**: Provide alt text that describes the image for accessibility.
- **Resolution**: Ensure images are high-resolution but optimized for web to reduce file size.
- **File Naming**: Use descriptive file names in lowercase with hyphens.

### Including Images

- **Placement**: Place images in an `images` or `assets` subdirectory relevant to the document.
- **Markdown Syntax**: Use the following syntax to include images:

  ```markdown
  ![Alt text describing the image](./images/diagram.svg)
  ```

### Captions

- **Descriptive Captions**: Include a caption below the image if additional explanation is needed.
- **Figure Numbers**: Number figures sequentially if the document contains multiple images.

Example:

```markdown
![Deployment Architecture Diagram](./images/deployment-architecture.svg)

*Figure 1: High-level deployment architecture of the Konductor platform.*
```

## Accessibility Guidelines

### Text Content

- **Color Contrast**: Ensure sufficient color contrast between text and background.
- **Avoid Color Reliance**: Do not rely solely on color to convey information.
- **Semantic Markup**: Use appropriate heading levels and list structures.

### Navigation

- **Logical Structure**: Organize content with a clear and logical structure.
- **Descriptive Links**: Use descriptive link text that makes sense out of context.
- **Keyboard Accessibility**: Ensure interactive elements can be accessed via keyboard navigation.

### Media

- **Alt Text**: Provide alternative text for images that conveys the same information.
- **Transcripts and Captions**: Provide transcripts for audio content and captions for videos.
- **Accessible Tables**: Use table headers and scope attributes to make tables accessible.

## Version Control

### Commit Messages

- **Descriptive Messages**: Write clear, descriptive commit messages that explain the changes made.
- **Issue References**: Reference related issue numbers in the commit message.
- **Conventional Commits**: Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

Example:

```
docs(developer_guide): add code commenting standards to documentation style guide

* Include section on code commenting and docstrings
* Update examples with docstrings
* Align with PULUMI_PYTHON.md coding standards

Fixes: #456
```

### Branching

- **Feature Branches**: Create feature branches for substantial changes or additions.
- **Naming Conventions**: Use prefixes like `docs/` for documentation branches (e.g., `docs/update-style-guide`).
- **Pull Requests**: Submit pull requests for review before merging changes into the main branch.
- **Synchronization**: Keep documentation in sync with code changes to maintain consistency.

## File Organization

### Naming Conventions

- **Lowercase with Hyphens**: Use lowercase letters with hyphens to separate words (e.g., `getting-started.md`).
- **Descriptive Names**: Choose descriptive but concise file names that reflect the content.
- **File Extensions**: Use `.md` for Markdown files.

### Directory Structure

- **Hierarchy**: Follow the established directory hierarchy of the project.
- **Grouping**: Group related documents in subdirectories (e.g., `developer_guide`, `user_guide`).
- **README Files**: Include `README.md` files in directories to provide an overview and navigation.
- **Clean Organization**: Avoid clutter by removing outdated or unnecessary files.

### File Templates

- **Standard Templates**: Use standard templates for common document types (e.g., guides, tutorials).
- **Consistency**: Maintain consistent structure and formatting across documents.
- **Updating Templates**: Update templates as needed to reflect changes in standards or practices.

## Documentation Workflow and Maintenance

### Review Process

- **Peer Review**: Have documentation reviewed by at least one other team member.
- **Feedback Incorporation**: Address feedback and make necessary revisions.
- **Approval**: Obtain necessary approvals before merging changes.

### Updating Documentation

- **Version Updates**: Update documentation when code changes affect existing content.
- **Deprecation Notices**: Clearly indicate when features are deprecated and provide alternatives.
- **Changelog**: Maintain a changelog of significant documentation updates.

### Automation Tools

- **Continuous Integration**: Use CI tools to check for broken links, spelling errors, and formatting issues.
- **Linting**: Implement Markdown linters to enforce style guidelines.
- **Documentation Generation**: Utilize tools to generate API documentation from code comments where applicable.

## Conclusion

By adhering to this documentation style guide, we ensure that the Konductor project's documentation is consistent, clear, and accessible. This facilitates better understanding among users and contributors, aids in onboarding new team members, and enhances the overall quality and maintainability of the project.

For questions or suggestions regarding this style guide, please reach out to the documentation team or submit an issue on the project's repository.

## Related Documents

- [Developer Guide](./README.md)
- [Pulumi Python Development Standards (`PULUMI_PYTHON.md`)](../reference/PULUMI_PYTHON.md)
- [TypedDict Reference Guide](../reference/TypedDict.md)
- [Contribution Guidelines](../contribution_guidelines.md)
- [Style Guide](../reference/style_guide.md)
