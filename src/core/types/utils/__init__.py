# src/core/types/utils/__init__.py

"""
Utility functions and helpers for the Core Module type system.

This package contains utility functions related to type checking,
conversion, and other type-related operations.
"""

from .type_checking import is_optional_type, get_origin_type, get_type_args
from .converters import convert_to_type, convert_dict_types

__all__ = [
    'is_optional_type',
    'get_origin_type',
    'get_type_args',
    'convert_to_type',
    'convert_dict_types',
]
