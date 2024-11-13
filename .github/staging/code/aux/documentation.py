# pulumi/core/documentation.py

import inspect
import ast
import re
from typing import Dict, Any, List, Optional, Type, get_type_hints
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel

@dataclass
class DocSection:
    """Represents a section of documentation."""
    title: str
    content: str
    subsections: List['DocSection'] = None

    def to_markdown(self, level: int = 1) -> str:
        """Convert section to markdown."""
        markdown = f"{'#' * level} {self.title}\n\n{self.content}\n\n"
        if self.subsections:
            for subsection in self.subsections:
                markdown += subsection.to_markdown(level + 1)
        return markdown

class DocGenerator:
    """Generates comprehensive documentation for modules."""

    def __init__(self, output_dir: Path):
        """
        Initialize DocGenerator.

        Args:
            output_dir: Directory where documentation will be written
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_module_docs(self, module: Any) -> str:
        """
        Generate documentation for a module.

        Args:
            module: The module to document

        Returns:
            str: Generated markdown documentation
        """
        # Get module info
        module_name = module.__name__
        module_doc = inspect.getdoc(module) or "No module documentation available."

        sections = [
            DocSection("Overview", module_doc),
            self._generate_configuration_section(module),
            self._generate_interface_section(module),
            self._generate_examples_section(module),
            self._generate_schema_section(module)
        ]

        # Combine all sections
        markdown = f"# {module_name}\n\n"
        markdown += self._generate_toc(sections)
        markdown += "\n---\n\n"
        for section in sections:
            markdown += section.to_markdown()

        # Write to file
        doc_file = self.output_dir / f"{module_name}.md"
        doc_file.write_text(markdown)
        return markdown

    def _generate_toc(self, sections: List[DocSection]) -> str:
        """Generate table of contents."""
        toc = "## Table of Contents\n\n"
        for i, section in enumerate(sections, 1):
            toc += f"{i}. [{section.title}](#{section.title.lower().replace(' ', '-')})\n"
            if section.subsections:
                for j, subsection in enumerate(section.subsections, 1):
                    toc += f"   {i}.{j}. [{subsection.title}](#{subsection.title.lower().replace(' ', '-')})\n"
        return toc + "\n"

    def _generate_configuration_section(self, module: Any) -> DocSection:
        """Generate configuration documentation."""
        config_classes = self._find_config_classes(module)
        content = "## Configuration\n\n"

        for config_class in config_classes:
            content += f"### {config_class.__name__}\n\n"

            # Get docstring
            class_doc = inspect.getdoc(config_class)
            if class_doc:
                content += f"{class_doc}\n\n"

            # Get type hints and field documentation
            content += "| Field | Type | Required | Description |\n"
            content += "|-------|------|----------|-------------|\n"

            hints = get_type_hints(config_class)
            for field_name, field_type in hints.items():
                required = "Yes" if self._is_field_required(config_class, field_name) else "No"
                desc = self._get_field_description(config_class, field_name)
                content += f"| {field_name} | `{field_type}` | {required} | {desc} |\n"

            content += "\n"

        return DocSection("Configuration", content)

    def _generate_interface_section(self, module: Any) -> DocSection:
        """Generate interface documentation."""
        content = ""

        # Document public functions
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                content += self._document_function(obj)

        return DocSection("Interface", content)

    def _document_function(self, func: Any) -> str:
        """Generate documentation for a function."""
        doc = inspect.getdoc(func) or "No documentation available."
        signature = inspect.signature(func)

        content = f"### `{func.__name__}`\n\n"
        content += f"```python\n{func.__name__}{signature}\n```\n\n"
        content += f"{doc}\n\n"

        # Add example usage if available
        if "Example:" in doc:
            example = doc[doc.index("Example:"):].split("\n", 1)[1]
            content += f"**Example:**\n```python\n{example}\n```\n\n"

        return content

    def _generate_examples_section(self, module: Any) -> DocSection:
        """Generate examples documentation."""
        # Look for examples in module docstring or dedicated examples
        examples = self._extract_examples(module)
        content = "Usage examples for this module:\n\n"

        for i, example in enumerate(examples, 1):
            content += f"### Example {i}\n\n"
            content += f"```python\n{example}\n```\n\n"

        return DocSection("Examples", content)

    def _generate_schema_section(self, module: Any) -> DocSection:
        """Generate schema documentation."""
        # Find all Pydantic models and TypedDict classes
        schemas = self._find_schemas(module)
        content = "Configuration and data schemas used by this module:\n\n"

        for schema in schemas:
            content += f"### {schema.__name__}\n\n"
            if issubclass(schema, BaseModel):
                content += self._document_pydantic_model(schema)
            else:
                content += self._document_typed_dict(schema)

        return DocSection("Schemas", content)

    def _document_pydantic_model(self, model: Type[BaseModel]) -> str:
        """Generate documentation for a Pydantic model."""
        content = f"```python\n{inspect.getsource(model)}\n```\n\n"

        # Add field descriptions
        content += "| Field | Type | Description |\n"
        content += "|-------|------|-------------|\n"

        for field_name, field in model.__fields__.items():
            desc = field.field_info.description or "No description"
            content += f"| {field_name} | `{field.type_}` | {desc} |\n"

        return content + "\n"

    def _find_config_classes(self, module: Any) -> List[Type]:
        """Find all configuration classes in a module."""
        return [
            obj for _, obj in inspect.getmembers(module)
            if inspect.isclass(obj) and (
                issubclass(obj, BaseModel) or
                hasattr(obj, "__annotations__")
            )
        ]

    def _is_field_required(self, cls: Type, field_name: str) -> bool:
        """Determine if a field is required."""
        if issubclass(cls, BaseModel):
            return cls.__fields__[field_name].required
        return True  # Default to True for TypedDict fields

    def _get_field_description(self, cls: Type, field_name: str) -> str:
        """Get field description from docstring or annotations."""
        if issubclass(cls, BaseModel):
            return cls.__fields__[field_name].field_info.description or "No description"

        # Try to extract from class docstring
        doc = inspect.getdoc(cls) or ""
        field_doc_match = re.search(
            rf"{field_name}\s*:\s*([^\n]+)",
            doc,
            re.MULTILINE
        )
        return field_doc_match.group(1) if field_doc_match else "No description"

    def _extract_examples(self, module: Any) -> List[str]:
        """Extract example code from module."""
        examples = []

        # Look for examples in module docstring
        doc = inspect.getdoc(module) or ""
        example_blocks = re.finditer(
            r'```python\s*(.*?)\s*```',
            doc,
            re.DOTALL
        )
        examples.extend(match.group(1) for match in example_blocks)

        # Look for example functions
        for name, obj in inspect.getmembers(module):
            if (inspect.isfunction(obj) and
                (name.startswith('example_') or name.endswith('_example'))):
                examples.append(inspect.getsource(obj))

        return examples

    def _find_schemas(self, module: Any) -> List[Type]:
        """Find all schema classes in a module."""
        return [
            obj for _, obj in inspect.getmembers(module)
            if inspect.isclass(obj) and (
                issubclass(obj, BaseModel) or
                hasattr(obj, "__total__")  # TypedDict check
            )
        ]

def generate_module_documentation():
    """Generate documentation for all modules."""
    doc_generator = DocGenerator(Path("./docs/modules"))

    # Generate docs for each module
    import my_module
    doc_generator.generate_module_docs(my_module)

# Run documentation generation
if __name__ == "__main__":
    generate_module_documentation()
