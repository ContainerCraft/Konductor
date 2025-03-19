# src/core/types/utils/converters.py

"""
Type conversion utilities for the Core Module type system.

This module provides helper functions for converting between different types.
"""

from typing import Any, Dict, List, Set, Optional, Type, TypeVar, cast
import datetime
import json
from decimal import Decimal

from .type_checking import (
    get_origin_type, get_type_args, is_optional_type, get_inner_type
)

T = TypeVar('T')


def convert_to_type(value: Any, target_type: Type[T]) -> Optional[T]:
    """Convert a value to a target type.

    Args:
        value: Value to convert
        target_type: Target type

    Returns:
        Converted value or None if conversion fails
    """
    if value is None:
        return None

    # If already the correct type, return as is
    if isinstance(value, target_type):
        return cast(T, value)

    # Handle Optional types
    if is_optional_type(target_type):
        inner_type = get_inner_type(target_type)
        return convert_to_type(value, inner_type)

    # Handle container types
    origin = get_origin_type(target_type)
    if origin is not None:
        args = get_type_args(target_type)

        # List conversion
        if origin in (list, List):
            return _extracted_from_convert_to_type_30(value, args, convert_to_type)
        # Dict conversion
        if origin in (dict, Dict):
            return _extracted_from_convert_to_type_47(value, args, convert_to_type)
        # Set conversion
        if origin in (set, Set):
            return _extracted_from_convert_to_type_71(value, args, convert_to_type)
    # Basic type conversions
    try:
        if target_type == str:
            return cast(T, str(value))

        if target_type == int:
            if isinstance(value, str) and not value.strip():
                return None
            return cast(T, int(value))

        if target_type == float:
            if isinstance(value, str) and not value.strip():
                return None
            return cast(T, float(value))

        if target_type == bool:
            if isinstance(value, str):
                value = value.lower().strip()
                if value in ('true', 'yes', '1', 'y'):
                    return cast(T, True)
                return cast(T, False) if value in ('false', 'no', '0', 'n') else None
            return cast(T, bool(value))

        if target_type == datetime.datetime:
            if isinstance(value, str):
                return cast(T, datetime.datetime.fromisoformat(value))
            if isinstance(value, (int, float)):
                return cast(T, datetime.datetime.fromtimestamp(value))

        if target_type == datetime.date:
            if isinstance(value, str):
                return cast(T, datetime.date.fromisoformat(value))
            if isinstance(value, datetime.datetime):
                return cast(T, value.date())

        if target_type == Decimal:
            return cast(T, Decimal(str(value)))

    except (ValueError, TypeError, OverflowError):
        return None

    try:
        return cast(T, target_type(value))
    except (ValueError, TypeError):
        return None


# TODO Rename this here and in `convert_to_type`
def _extracted_from_convert_to_type_71(value, args, convert_to_type):
    if not isinstance(value, (list, tuple, set)):
        return None

    item_type = args[0] if args else Any
    if item_type is Any:
        return cast(T, set(value))

    result = set()
    for item in value:
        converted = convert_to_type(item, item_type)
        if converted is None:
            return None
        result.add(converted)
    return cast(T, result)


# TODO Rename this here and in `convert_to_type`
def _extracted_from_convert_to_type_47(value, args, convert_to_type):
    if not isinstance(value, dict):
        return None

    key_type = args[0] if args else Any
    val_type = args[1] if len(args) > 1 else Any

    if key_type is Any and val_type is Any:
        return cast(T, dict(value))

    result = {}
    for k, v in value.items():
        converted_key = convert_to_type(k, key_type)
        if converted_key is None:
            return None

        converted_val = convert_to_type(v, val_type)
        if converted_val is None:
            return None

        result[converted_key] = converted_val
    return cast(T, result)


# TODO Rename this here and in `convert_to_type`
def _extracted_from_convert_to_type_30(value, args, convert_to_type):
    if not isinstance(value, (list, tuple)):
        return None

    item_type = args[0] if args else Any
    if item_type is Any:
        return cast(T, list(value))

    result = []
    for item in value:
        converted = convert_to_type(item, item_type)
        if converted is None:
            return None
        result.append(converted)
    return cast(T, result)


def convert_dict_types(
    data: Dict[str, Any],
    type_hints: Dict[str, Any]
) -> Dict[str, Any]:
    """Convert dictionary values according to type hints.

    Args:
        data: Dictionary to convert
        type_hints: Dictionary of key to expected type

    Returns:
        New dictionary with converted values
    """
    result = {}

    for key, value in data.items():
        if key in type_hints:
            target_type = type_hints[key]
            converted = convert_to_type(value, target_type)
            result[key] = converted if converted is not None else value
        else:
            # Keep values without type hints unchanged
            result[key] = value

    return result


def to_json_serializable(obj: Any) -> Any:
    """Convert an object to a JSON-serializable form.

    Args:
        obj: Object to convert

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()

    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, (list, tuple)):
        return [to_json_serializable(item) for item in obj]

    if isinstance(obj, dict):
        return {str(k): to_json_serializable(v) for k, v in obj.items()}

    if isinstance(obj, set):
        return [to_json_serializable(item) for item in obj]

    # Try to convert to dictionary using __dict__
    if hasattr(obj, '__dict__'):
        return to_json_serializable(obj.__dict__)

    # Last resort: convert to string
    return str(obj)


def dict_to_json(data: Dict[str, Any]) -> str:
    """Convert a dictionary to a JSON string.

    Args:
        data: Dictionary to convert

    Returns:
        JSON string
    """
    serializable = to_json_serializable(data)
    return json.dumps(serializable, indent=2)


def json_to_dict(json_str: str) -> Dict[str, Any]:
    """Convert a JSON string to a dictionary.

    Args:
        json_str: JSON string to convert

    Returns:
        Dictionary
    """
    return json.loads(json_str)
