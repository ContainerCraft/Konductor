# Konductor Documentation Style Guide

## Introduction

This style guide establishes standards for creating and maintaining documentation within the Konductor project. It ensures consistency, clarity, and accessibility across all documentation while aligning with the project's technical standards outlined in `PULUMI_PYTHON.md`.

## Table of Contents

1. [General Principles](#general-principles)
2. [Document Structure](#document-structure)
3. [Writing Style](#writing-style)
4. [Formatting Standards](#formatting-standards)
5. [Code Examples](#code-examples)
6. [Links and References](#links-and-references)
7. [Images and Diagrams](#images-and-diagrams)
8. [Accessibility Guidelines](#accessibility-guidelines)
9. [Version Control](#version-control)
10. [File Organization](#file-organization)

## General Principles

### Clarity
- Write for your audience's knowledge level
- Define technical terms on first use
- Use consistent terminology throughout
- Avoid jargon unless necessary

### Completeness
- Include all necessary information
- Provide context for technical concepts
- Link to related documentation
- Include troubleshooting guidance

### Maintainability
- Keep content modular
- Use relative links
- Follow the DRY (Don't Repeat Yourself) principle
- Regular reviews and updates

## Document Structure

### Required Sections

1. **Title**: Clear, descriptive title using H1 (`#`)
2. **Introduction**: Brief overview of the document's purpose
3. **Table of Contents**: For documents longer than 3 sections
4. **Prerequisites** (if applicable): Required knowledge or setup
5. **Main Content**: Organized in logical sections
6. **Conclusion** (if applicable): Summary or next steps
7. **Related Resources**: Links to related documentation

### Header Hierarchy

```markdown
# Document Title (H1)
## Section Title (H2)
### Sub-section Title (H3)
#### Minor Sub-section Title (H4)
```

### Metadata Block (Optional)

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
- Use active voice
- Be direct and concise
- Maintain a professional, friendly tone
- Write in present tense

### Paragraphs
- Keep paragraphs focused on a single topic
- Use short paragraphs (3-5 sentences)
- Include transition sentences between sections

### Lists
- Use bullet points for unordered lists
- Use numbered lists for sequential steps
- Maintain parallel structure in list items

## Formatting Standards

### Text Formatting

- **Bold**: Use for emphasis and UI elements
- *Italic*: Use for introducing new terms
- `Code`: Use for code snippets, file names, and commands
- ***Bold Italic***: Avoid unless absolutely necessary

### Code Blocks

- Use triple backticks with language identifier
- Include description of code's purpose
- Add line numbers for longer snippets

```python
# Example code block
def example_function():
    """Docstring describing the purpose of the function."""
    pass
```

### Tables

- Use tables for structured data
- Include header row
- Align columns consistently

| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Data     | Data     | Data     |

## Code Examples

### General Guidelines

- Keep examples simple and focused
- Include comments explaining key concepts
- Use meaningful variable and function names
- Follow `PULUMI_PYTHON.md` coding standards

### Example Structure

```python
from typing import TypedDict, Optional

class ConfigExample(TypedDict):
    """Example configuration structure.
    Attributes:
        name: Resource name
        enabled: Whether the resource is enabled
    """
    name: str
    enabled: bool

def example_function(config: ConfigExample) -> None:
    """Example function with type annotations.
    Args:
        config: Configuration dictionary
    """
    if config.get("enabled", True):
        print(f"Resource {config['name']} is enabled.")
```

## Links and References

### Internal Links
- Use relative paths
- Link to specific sections where applicable
- Check links regularly for validity

### External Links
- Include link text that makes sense out of context
- Add notes for external dependencies
- Consider link stability

### Cross-References
- Use consistent terminology
- Link to glossary terms
- Reference related documentation

## Images and Diagrams

### Requirements
- Use SVG format when possible
- Include alt text for accessibility
- Provide high-resolution versions
- Keep file sizes reasonable

### Captions
- Include descriptive captions
- Number figures sequentially
- Reference figures in text

## Accessibility Guidelines

### Text Content
- Use sufficient color contrast
- Avoid relying solely on color
- Provide text alternatives for media
- Use semantic markup

### Navigation
- Logical heading structure
- Descriptive link text
- Keyboard navigation support
- Skip navigation links

### Media
- Alt text for images
- Transcripts for audio
- Captions for video
- Accessible data tables

## Version Control

### Commit Messages
- Use clear, descriptive messages
- Reference issue numbers
- Indicate documentation changes
- Follow conventional commits

Example:

```
docs(aws): update EKS cluster setup guide
```

* Add troubleshooting section
* Update configuration examples
* Fix broken links

Fixes:
- #123: Fixed broken link to EKS documentation


### Branching
- Create feature branches for substantial changes
- Use `docs/` prefix for documentation branches
- Review changes before merging
- Keep documentation in sync with code

## File Organization

### Naming Conventions
- Use lowercase with underscores
- Be descriptive but concise
- Include relevant prefixes
- Maintain consistent extensions

### Directory Structure
- Follow the established hierarchy
- Group related documents
- Use README files for navigation
- Maintain clean organization

### File Templates
- Use standard templates
- Include required sections
- Maintain consistent structure
- Update templates as needed

---

## Implementation Notes

This style guide should be:
- Referenced during documentation creation
- Updated based on team feedback
- Reviewed quarterly
- Enforced through automation where possible

## Related Documents

- [PULUMI_PYTHON.md](./PULUMI_PYTHON.md)
- [TypedDict.md](./TypedDict.md)
- [Contribution Guidelines](../developer_guide/contribution_guidelines.md)
