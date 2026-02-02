"""Lightweight type utilities used across the project."""

from __future__ import annotations

import json
from collections.abc import Mapping
from hashlib import sha256
from types import UnionType
from typing import ClassVar, TypeGuard, Union, get_args, get_origin

type JsonSchema = Mapping[str, object]
type TypeKey = str


def _is_type(value: object) -> TypeGuard[type[object]]:
    return isinstance(value, type)


class TypeSafeUnion:
    """Utilities for union type inspection."""

    @staticmethod
    def safe_getattr(
        obj: object, attr: str, default: object | None = None
    ) -> object | None:
        """Safely get an attribute with a default fallback.

        Args:
            obj: Object to inspect.
            attr: Attribute name.
            default: Value to return if attribute is missing.

        Returns:
            Attribute value or default.

        """
        return getattr(obj, attr, default)

    @staticmethod
    def is_union_type(obj_type: object) -> bool:
        """Check whether the provided type is a Union.

        Args:
            obj_type: Type object to inspect.

        Returns:
            True if the type is a Union, False otherwise.

        """
        origin = get_origin(obj_type)
        return origin is UnionType or origin is Union

    @staticmethod
    def get_union_args(union_type: object) -> tuple[object, ...]:
        """Return arguments of a Union type.

        Args:
            union_type: Union type to inspect.

        Returns:
            Tuple of member types.

        """
        return get_args(union_type)


class DiscriminatedUnion:
    """Simple discriminated union matching by runtime type."""

    @staticmethod
    def match(value: object, union_type: object) -> tuple[str, object]:
        """Match a value against union member types.

        Args:
            value: Value to match.
            union_type: Union type to inspect.

        Returns:
            Tuple of (matched type name, value).

        """
        if not TypeSafeUnion.is_union_type(union_type):
            return ("single", value)

        for arg in TypeSafeUnion.get_union_args(union_type):
            if _is_type(arg) and isinstance(value, arg):
                return (arg.__name__, value)

        return ("unknown", value)


class TypeRegistry:
    """Small cache for types derived from JSON schemas."""

    _type_cache: ClassVar[dict[TypeKey, type[object]]] = {}

    @classmethod
    def get_or_create_type(cls, schema: JsonSchema) -> type[object]:
        """Get a cached type for a schema or create a new one.

        Args:
            schema: JSON schema mapping.

        Returns:
            A Python type corresponding to the schema.

        """
        type_key = cls._generate_type_key(schema)
        if type_key in cls._type_cache:
            return cls._type_cache[type_key]

        created_type = cls._create_type(schema)
        cls._type_cache[type_key] = created_type
        return created_type

    @staticmethod
    def _generate_type_key(schema: JsonSchema) -> TypeKey:
        schema_str = json.dumps(dict(schema), sort_keys=True, default=str)
        return sha256(schema_str.encode("utf-8")).hexdigest()

    @staticmethod
    def _create_type(schema: JsonSchema) -> type[object]:
        schema_type = schema.get("type")
        type_map: dict[object, type[object]] = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "null": type(None),
            "array": list,
            "object": dict,
        }
        return type_map.get(schema_type, object)


class TypeSafeSerializer:
    """Serialize and deserialize data with light type awareness."""

    @staticmethod
    def serialize(obj: object) -> dict[str, object]:
        """Serialize an object into a dictionary payload.

        Args:
            obj: Object to serialize.

        Returns:
            Serialized dictionary representation.

        """
        if hasattr(obj, "model_dump") and callable(obj.model_dump):
            result = obj.model_dump()
            if isinstance(result, Mapping):
                return dict(result)
        if hasattr(obj, "to_dict") and callable(obj.to_dict):
            result = obj.to_dict()
            if isinstance(result, Mapping):
                return dict(result)
        if isinstance(obj, Mapping):
            return dict(obj)
        return {"_type": type(obj).__name__, "_value": str(obj)}

    @staticmethod
    def deserialize(
        data: Mapping[str, object], target_type: type[object]
    ) -> object | None:
        """Deserialize data into a target type when possible.

        Args:
            data: Serialized mapping data.
            target_type: Desired output type.

        Returns:
            Parsed object or None if parsing fails.

        """
        if hasattr(target_type, "model_validate") and callable(
            target_type.model_validate,
        ):
            validated: object = target_type.model_validate(data)
            return validated
        if hasattr(target_type, "from_dict") and callable(
            target_type.from_dict,
        ):
            parsed: object = target_type.from_dict(data)
            return parsed
        try:
            return target_type(**dict(data))
        except (TypeError, ValueError):
            return None
