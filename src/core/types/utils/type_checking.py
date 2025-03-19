# src/core/types/utils/type_checking.py

"""
Type checking utilities for the Core Module type system.

This module provides helper functions for runtime type checking and inspection.
"""

from typing import Any, Dict, List, Set, Union, Tuple, Type, get_type_hints
import inspect
import sys


def is_optional_type(type_hint: Any) -> bool:
    """Check if a type hint represents an Optional type.

    Args:
        type_hint: Type hint to check

    Returns:
        True if type is Optional[X], otherwise False
    """
    # Get the origin type (e.g., Union from Optional[int])
    origin = get_origin_type(type_hint)

    if origin is Union:
        # Get the type arguments (e.g., (int, NoneType) from Optional[int])
        args = get_type_args(type_hint)
        # Check if one of the union types is NoneType
        return len(args) == 2 and type(None) in args

    return False


def get_origin_type(type_hint: Any) -> Any:
    """Get the origin type from a typing annotation.

    Args:
        type_hint: Type hint to inspect

    Returns:
        Origin type or None
    """
    # Python 3.8+
    return type_hint.__origin__ if hasattr(type_hint, "__origin__") else None


def get_type_args(type_hint: Any) -> Tuple[Any, ...]:
    """Get the type arguments from a typing annotation.

    Args:
        type_hint: Type hint to inspect

    Returns:
        Tuple of type arguments
    """
    # Python 3.8+
    return type_hint.__args__ if hasattr(type_hint, "__args__") else ()


def get_inner_type(type_hint: Any) -> Any:
    """Get the inner type from an Optional or container type.

    Args:
        type_hint: Type hint to inspect

    Returns:
        Inner type
    """
    if is_optional_type(type_hint):
        args = get_type_args(type_hint)
        return next((arg for arg in args if arg is not type(None)), None)
    origin = get_origin_type(type_hint)
    if origin in (list, List):
        args = get_type_args(type_hint)
        return args[0] if args else Any
    if origin in (dict, Dict):
        args = get_type_args(type_hint)
        return args[1] if len(args) > 1 else Any
    if origin in (set, Set):
        args = get_type_args(type_hint)
        return args[0] if args else Any

    return type_hint


def is_subclass_safe(obj: Any, cls: Type) -> bool:
    """Safely check if an object is a subclass of a class.

    Args:
        obj: Object to check
        cls: Class to check against

    Returns:
        True if obj is a subclass of cls, otherwise False
    """
    try:
        return inspect.isclass(obj) and issubclass(obj, cls)
    except TypeError:
        return False


def is_instance_safe(obj: Any, cls: Type) -> bool:
    """Safely check if an object is an instance of a class.

    Args:
        obj: Object to check
        cls: Class to check against

    Returns:
        True if obj is an instance of cls, otherwise False
    """
    try:
        return isinstance(obj, cls)
    except TypeError:
        return False


def get_class_type_hints(cls: Type) -> Dict[str, Any]:
    """Get type hints for a class, following the MRO chain.

    Args:
        cls: Class to inspect

    Returns:
        Dictionary of attribute names to type hints
    """
    hints = {}
    for base in reversed(cls.__mro__):
        if base is object:
            continue
        hints |= get_type_hints(base, globalns=sys.modules[base.__module__].__dict__)
    return hints
