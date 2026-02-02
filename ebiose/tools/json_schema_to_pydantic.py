"""Utilities for building Pydantic models from JSON Schema."""

import logging  # Use logging for warnings/errors
from contextlib import suppress
from typing import Any, ForwardRef, Optional, Union, cast

from pydantic import BaseModel, create_model  # Import Field for potential future use

LOGGER = logging.getLogger(__name__)

# --- Configuration ---
_DEFS_KEY = "$defs"  # Pydantic V2 uses $defs
_RECURSION_DEPTH_LIMIT = 20  # Protection against infinite recursion

# --- Type Mapping ---
# Maps JSON schema types to Python types
TYPE_MAP: dict[str, type] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "null": type(None),
}

# --- Type aliases ---
type JsonSchema = dict[str, object]
type ModelType = type[BaseModel]
type CacheValue = ModelType | ForwardRef


def _as_schema_dict(schema: object) -> JsonSchema | None:
    if isinstance(schema, dict):
        return schema
    return None


def _is_optional_type(field_type: object) -> bool:
    if field_type is type(None):
        return True
    return getattr(field_type, "__origin__", None) is Union and type(None) in getattr(
        field_type, "__args__", ()
    )


def _build_field_definition(
    model_name: str,
    field_name: str,
    field_props: JsonSchema,
    required_fields: set[str],
    recursion_depth: int,
) -> tuple[object, object]:
    try:
        field_type = _get_python_type(field_props, recursion_depth + 1)
    except RecursionError:
        LOGGER.exception(
            "Recursion limit hit parsing type for '%s.%s'. Using object.",
            model_name,
            field_name,
        )
        field_type = object
    except ValueError:
        LOGGER.exception(
            "Type resolution error for '%s.%s'. Using object.",
            model_name,
            field_name,
        )
        field_type = object

    is_required = field_name in required_fields
    default_value: object = field_props.get("default")

    field_definition: object = ...
    if not is_required:
        field_definition = default_value if default_value is not None else None
        if not _is_optional_type(field_type):
            field_type = cast("type | ForwardRef", field_type) | None
    elif default_value is not None:
        field_definition = default_value

    return field_type, field_definition


# --- Caching (Module Level for a Single Run) ---
# These caches store models created during a single call to the main function.
# They are cleared at the start of each top-level create_pydantic_model_from_schema call.
_MODEL_CACHE: dict[str, CacheValue] = {}
_DEFS_CACHE: dict[str, CacheValue] = {}


def _resolve_ref(ref_path: str) -> CacheValue:
    """Resolve a $ref string."""
    try:
        # Expecting format like "#/$defs/ModelName"
        def_name = ref_path.split("/")[-1]
    except (IndexError, AttributeError) as e:
        msg = f"Invalid $ref format: {ref_path}"
        raise ValueError(msg) from e

    # Check caches first
    if def_name in _DEFS_CACHE:
        return _DEFS_CACHE[def_name]
    if (
        def_name in _MODEL_CACHE
    ):  # Could be a reference to the model currently being defined
        return _MODEL_CACHE[def_name]
    # If not found, create a ForwardRef. Pydantic V2 resolves these later via model_rebuild.
    LOGGER.info("Creating ForwardRef for unresolved $ref: %s", ref_path)
    fwd_ref = ForwardRef(def_name)
    # Store the ForwardRef in the cache
    _MODEL_CACHE[def_name] = fwd_ref
    return fwd_ref


def _resolve_single_type(
    schema_type: str,
    schema: JsonSchema,
    recursion_depth: int,
) -> type | None:
    """Resolve a single string type."""
    mapped_type = TYPE_MAP.get(schema_type)
    if mapped_type:
        return mapped_type
    if schema_type == "array":
        items_schema = schema.get("items", {})
        if items_schema:
            _get_python_type(items_schema, recursion_depth + 1)
        return list[object]
    if schema_type == "object":
        if "properties" in schema:
            LOGGER.warning(
                "Inline object with properties found (not using $ref). "
                "Treating as Dict[str, object]. Schema: %s",
                str(schema.get("title", "N/A")),
            )
        return dict[str, object]

    LOGGER.warning("Unknown single type '%s'. Returning object.", schema_type)
    return cast("type", object)


def _combine_types(possible_types: list[object]) -> object:
    """Combine a list of types into a single type (Union or direct type)."""
    if not possible_types:
        return object

    non_none_types = [t for t in possible_types if t is not type(None)]
    has_null = len(non_none_types) < len(possible_types)

    if not non_none_types:
        return type(None)

    # Combine actual types using Union because | can be problematic with mixed types/ForwardRefs
    # in some contexts, or simpler to just use Union check.
    # Note: X | Y is syntax sugar, but strict type checkers might prefer Union for mixed bags.
    final_type: object = non_none_types[0]
    for other_type in non_none_types[1:]:
        final_type = cast("type | ForwardRef", final_type) | cast(
            "type | ForwardRef",
            other_type,
        )

    if has_null:
        return cast("type | ForwardRef", final_type) | None

    return final_type


def _types_from_schema_type(
    schema_type: object,
    schema_dict: JsonSchema,
    recursion_depth: int,
) -> list[object] | None:
    if isinstance(schema_type, list):
        possible_types: list[object] = []
        for item in schema_type:
            if isinstance(item, str):
                res = _resolve_single_type(item, schema_dict, recursion_depth)
                if res:
                    possible_types.append(res)
        return possible_types
    if isinstance(schema_type, str):
        res = _resolve_single_type(schema_type, schema_dict, recursion_depth)
        return [res] if res else []
    return None


def _types_from_any_of(
    schema_dict: JsonSchema,
    recursion_depth: int,
) -> list[object] | None:
    if "anyOf" not in schema_dict:
        return None
    any_of_schemas = cast("list[JsonSchema]", schema_dict["anyOf"])
    return [
        _get_python_type(sub_schema, recursion_depth + 1)
        for sub_schema in any_of_schemas
    ]


def _types_from_implicit(
    schema_dict: JsonSchema,
    recursion_depth: int,
) -> list[object] | None:
    if "properties" in schema_dict:
        LOGGER.warning(
            "Schema object without explicit 'type' or '$ref'. Treating as Dict[str, object]. "
            "Schema: %s",
            str(schema_dict.get("title", "N/A")),
        )
        return [dict[str, object]]
    if "items" in schema_dict:
        items_schema = cast("JsonSchema", schema_dict.get("items", {}))
        if items_schema:
            _get_python_type(items_schema, recursion_depth + 1)
        return [list[object]]
    return None


def _get_cached_model(model_name: str) -> ModelType | None:
    cached_val = _MODEL_CACHE.get(model_name)
    if isinstance(cached_val, type):
        return cached_val
    return None


def _ensure_forward_ref_cached(model_name: str) -> None:
    if model_name in _MODEL_CACHE:
        return
    fwd_ref = ForwardRef(model_name)
    _MODEL_CACHE[model_name] = fwd_ref
    if model_name in _DEFS_CACHE and isinstance(
        _DEFS_CACHE.get(model_name),
        ForwardRef,
    ):
        _DEFS_CACHE[model_name] = fwd_ref


def _get_python_type(
    schema: object,
    recursion_depth: int = 0,
) -> object:
    """Recursively determines the Python type hint for a given schema fragment.

    Args:
        schema: The JSON schema fragment.
        recursion_depth: Current depth of recursion.

    Returns:
        The corresponding Python type or a ForwardRef.

    Raises:
        ValueError: If a $ref cannot be resolved or schema is invalid.
        RecursionError: If recursion depth limit is exceeded.

    """
    if recursion_depth > _RECURSION_DEPTH_LIMIT:
        msg = (
            f"Maximum recursion depth ({_RECURSION_DEPTH_LIMIT}) exceeded. "
            "Check schema for circular references."
        )
        raise RecursionError(msg)

    schema_dict = _as_schema_dict(schema)
    if schema_dict is None:
        LOGGER.warning(
            "Encountered non-dict schema fragment: %s. Returning object.",
            schema,
        )
        return object

    # 1. Handle $ref (references to definitions)
    if "$ref" in schema_dict:
        return _resolve_ref(cast("str", schema_dict["$ref"]))

    # 2. Handle explicit type definitions
    schema_type = cast("str | list[str] | None", schema_dict.get("type"))
    possible_types = _types_from_schema_type(
        schema_type,
        schema_dict,
        recursion_depth,
    )
    if possible_types is None:
        possible_types = _types_from_any_of(schema_dict, recursion_depth)
    if possible_types is None and schema_type is None:
        possible_types = _types_from_implicit(schema_dict, recursion_depth)

    if not possible_types:
        return object

    return _combine_types(possible_types)


def _create_model_recursive(
    model_name: str,
    schema: JsonSchema,
    recursion_depth: int = 0,
) -> ModelType:
    """Recursively creates a Pydantic V2 BaseModel from its schema definition.

    Args:
        model_name: The desired name for the Pydantic model.
        schema: The JSON schema fragment defining the model.
        recursion_depth: Current depth of recursion.

    Returns:
        The dynamically created Pydantic BaseModel class.

    Raises:
        RecursionError: If recursion depth limit is exceeded.
        RuntimeError: If Pydantic fails to create the model.

    """
    if recursion_depth > _RECURSION_DEPTH_LIMIT:
        msg = (
            f"Maximum recursion depth ({_RECURSION_DEPTH_LIMIT}) exceeded while creating model "
            f"'{model_name}'. Check schema for circular references."
        )
        raise RecursionError(msg)

    cached_model = _get_cached_model(model_name)
    if cached_model is not None:
        return cached_model

    # Add a ForwardRef to cache temporarily to handle self/circular references
    _ensure_forward_ref_cached(model_name)

    fields: dict[str, tuple[object, object]] = {}
    properties = cast("JsonSchema", schema.get("properties", {}))
    required_fields: set[str] = set(cast("list[str]", schema.get("required", [])))

    # Iterate through properties defined in the schema
    for field_name, field_props in properties.items():
        if not isinstance(field_props, dict):
            LOGGER.warning(
                "Field '%s' in model '%s' has invalid properties schema (expected dict): %s. Skipping field.",
                field_name,
                model_name,
                field_props,
            )
            continue

        # Cast field_props to dict now that we verified it
        field_props_dict = cast("JsonSchema", field_props)

        field_type, field_definition = _build_field_definition(
            model_name,
            field_name,
            field_props_dict,
            required_fields,
            recursion_depth,
        )
        fields[field_name] = (field_type, field_definition)

    # Create the Pydantic V2 model using create_model
    field_definitions: dict[str, tuple[object, object]] = {
        key: (value[0], value[1]) for key, value in fields.items()
    }
    try:
        created_model: ModelType = create_model(
            model_name,
            __base__=BaseModel,  # Explicitly inherit from BaseModel
            **cast("dict[str, Any]", field_definitions),
        )
    except Exception as e:
        LOGGER.exception(
            "Pydantic create_model failed for '%s' with fields %s.",
            model_name,
            fields,
        )
        # Fallback or re-raise depending on desired robustness
        msg = f"Failed to create Pydantic model '{model_name}'"
        raise RuntimeError(msg) from e

    # --- Post-creation updates ---
    # 1. Update global namespace for ForwardRef resolution
    #    This makes the created type available by name for resolving ForwardRefs.
    globals()[model_name] = created_model

    # 2. Replace ForwardRef in caches with the actual created model type
    _MODEL_CACHE[model_name] = created_model
    if model_name in _DEFS_CACHE:  # Update defs cache as well if it was a definition
        _DEFS_CACHE[model_name] = created_model

    # 3. Trigger resolution of ForwardRefs using model_rebuild (crucial for V2)
    #    This should be called after the model is defined and potentially in globals().
    try:
        # Call model_rebuild safely, handling potential errors during rebuild
        created_model.model_rebuild(force=True)
        LOGGER.info("Model '%s' created and rebuilt successfully.", model_name)
    except (ValueError, TypeError, AttributeError) as e:
        # Log error during rebuild but proceed; some refs might remain unresolved
        LOGGER.warning(
            "Exception during model_rebuild for '%s': %s. ForwardRefs might not be fully resolved.",
            model_name,
            e,
        )

    return created_model


def _process_definitions(schema: JsonSchema) -> None:
    """Pre-process definitions ($defs) to handle forward references."""
    definitions = cast("JsonSchema", schema.get(_DEFS_KEY, {}))
    # Create ForwardRefs for all definitions first
    for def_name in definitions:
        if def_name not in _DEFS_CACHE:
            fwd_ref = ForwardRef(def_name)
            _DEFS_CACHE[def_name] = fwd_ref
            # Also add to model cache, as it might be referenced directly
            _MODEL_CACHE[def_name] = fwd_ref

    # Now, recursively create models for all definitions.
    for def_name, def_schema in definitions.items():
        if not isinstance(def_schema, dict):
            LOGGER.warning(
                "Invalid schema found for definition '%s'. Skipping.",
                str(def_name),
            )
            continue
        # Check if it's still a ForwardRef (meaning not processed yet by recursion)
        if (
            isinstance(_DEFS_CACHE.get(def_name), ForwardRef)
            or def_name not in _DEFS_CACHE
        ):
            try:
                # This call will create/update the model in the caches
                _create_model_recursive(
                    def_name,
                    cast("JsonSchema", def_schema),
                    recursion_depth=0,
                )
            except (RecursionError, ValueError, RuntimeError):
                LOGGER.exception(
                    "Error processing definition '%s'. Model creation might fail.",
                    str(def_name),
                )


def create_pydantic_model_from_schema(
    schema: object,
    model_name: str | None = None,
) -> ModelType:
    """Create a Pydantic V2 BaseModel class dynamically from a JSON schema dictionary.

    Handles nested models defined in the schema's '$defs' section and resolves
    ForwardRefs using Pydantic V2 mechanisms.

    Args:
        schema: The dictionary representing the JSON schema (e.g., from
                some_model.model_json_schema()).
        model_name: Optional name for the top-level model. If None, uses the
                    'title' from the schema, falling back to "DynamicModel".

    Returns:
        A dynamically created Pydantic BaseModel class corresponding to the schema.

    Raises:
        ValueError: If the schema is invalid or essential parts are missing.
        RecursionError: If the schema contains deeply nested or circular references
                       exceeding the depth limit.
        RuntimeError: If Pydantic fails to create the model.

    """
    # --- Initialization ---
    _MODEL_CACHE.clear()
    _DEFS_CACHE.clear()

    if not isinstance(schema, dict):
        msg = "Invalid schema: Input must be a dictionary."
        raise TypeError(msg)

    schema_dict = cast("JsonSchema", schema)

    # Determine the name for the top-level model
    top_level_model_name = model_name or cast(
        "str", schema_dict.get("title", "DynamicModel")
    )

    # --- Step 1: Pre-process definitions ($defs) ---
    _process_definitions(schema_dict)

    # Step 2: Create the main model
    # Check if the main model was already created (e.g., if schema was just a $ref)
    if top_level_model_name in _MODEL_CACHE:
        cached_model = _MODEL_CACHE[top_level_model_name]
        if isinstance(cached_model, type):
            final_model = cached_model  # Already fully created
        else:
            # It was a ForwardRef or something went wrong, try creating it properly
            LOGGER.info(
                "Top-level model '%s' was a ForwardRef, creating now.",
                top_level_model_name,
            )
            final_model = _create_model_recursive(
                top_level_model_name,
                schema_dict,
                recursion_depth=0,
            )
    else:
        # Create the top-level model using the main schema content
        final_model = _create_model_recursive(
            top_level_model_name,
            schema_dict,
            recursion_depth=0,
        )

    # --- Step 3: Final model rebuild (Optional but can catch stragglers) ---
    # A final rebuild on the top-level model *after* all definitions might help ensure
    # all nested ForwardRefs within its structure are fully resolved.
    try:
        model_rebuild = getattr(final_model, "model_rebuild", None)
        if callable(model_rebuild):
            model_rebuild(force=True)
            LOGGER.info(
                "Final rebuild completed for top-level model '%s'.",
                final_model.__name__,
            )
    except (ValueError, TypeError, AttributeError) as e:
        LOGGER.warning(
            "Final model_rebuild for '%s' failed: %s. Some ForwardRefs might remain unresolved.",
            final_model.__name__,
            e,
        )

    # Optional: Clean up globals()? Be careful not to remove genuinely defined models.
    # Maybe remove only names that still map to ForwardRef in _MODEL_CACHE after all rebuilds.

    return final_model


# ==============================================================================
# Example Usage (within __main__ block)
# ==============================================================================
if __name__ == "__main__":
    import json  # Keep json import local to the example if only used here
    import sys
    from pathlib import Path

    # Add project root to sys.path to allow importing 'ebiose'
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import pydantic  # For version info and exceptions
    from pydantic import ValidationError  # Explicit import

    # Configure logging if it wasn't set globally
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    LOGGER.info("Using Pydantic Version: %s\n", pydantic.VERSION)

    # --- Define original Pydantic models ---
    class Address(BaseModel):
        """Example address model used for schema reconstruction."""

        street_address: str
        city: str
        zip_code: str | None = None

    class Person(BaseModel):
        """Example person model used for schema reconstruction."""

        name: str
        age: int
        is_student: bool = False
        address: Address  # Nested model
        tags: list[str]
        previous_addresses: list[Address] | None = None

    # --- Get the JSON schema ---
    person_schema = Person.model_json_schema()

    LOGGER.info("--- Original Person Schema ---")
    LOGGER.info(json.dumps(person_schema, indent=2))
    LOGGER.info("-" * 30)

    # --- Reconstruct the model from the schema ---
    LOGGER.info("\n--- Reconstructing Model ---")
    try:
        ReconstructedPerson = create_pydantic_model_from_schema(person_schema)
        LOGGER.info(
            "Successfully reconstructed model: %s",
            ReconstructedPerson.__name__,
        )

        # --- Inspect the reconstructed model ---
        LOGGER.info("\n--- Reconstructed Model Fields ---")
        # Use Pydantic V2 inspection API
        for name, field_info in ReconstructedPerson.model_fields.items():
            LOGGER.info("  - %s:", name)
            LOGGER.info("      Annotation: %s", field_info.annotation)
            LOGGER.info("      Required:   %s", field_info.is_required())
            # Use get_default() for potentially computed defaults, otherwise .default
            default_val = field_info.get_default(call_default_factory=False)
            LOGGER.info(
                "      Default:    %r",
                default_val,
            )  # Use !r via %r for representation

        # --- Test instantiation ---
        LOGGER.info("\n--- Testing Instantiation ---")
        person_data: dict[str, object] = {
            "name": "Alice",
            "age": 30,
            "address": {
                "street_address": "123 Main St",
                "city": "Anytown",
                "zip_code": "12345",
            },
            "tags": ["developer", "python"],
            "previous_addresses": [
                {"street_address": "456 Old Ave", "city": "Oldtown"},
            ],
            # is_student will use default (False)
        }

        instance = ReconstructedPerson(**person_data)
        LOGGER.info("Instantiation successful!")
        LOGGER.info("\nInstance Data (JSON):")
        LOGGER.info(
            instance.model_dump_json(indent=2),
        )  # Use Pydantic V2 method

        # --- Test validation ---
        LOGGER.info("\n--- Testing Validation (Missing Required Field) ---")
        invalid_data: dict[str, object] = {
            "name": "Bob",
            # age is missing
            "address": {"street_address": "789 Side St", "city": "Sometown"},
            "tags": [],
        }
        try:
            ReconstructedPerson(**invalid_data)
        except ValidationError as e:
            LOGGER.info("Validation failed as expected:")
            # Pydantic V2 error formatting is usually quite good
            LOGGER.info(e)

    except (ValueError, RuntimeError, RecursionError):
        LOGGER.info("\n--- Error during Person reconstruction or testing ---")
        LOGGER.exception("Reconstruction failed")  # Log full traceback

    # --- Example with circular reference ---
    LOGGER.info("\n%s", "=" * 40)
    LOGGER.info("--- Testing Circular Reference ---")

    # Define models with circular reference manually (Pydantic V2 style)
    # Use STRING HINTS ('Employee', 'Department') for smoother schema generation

    class Department(BaseModel):
        """Example department model with circular references."""

        name: str
        manager: Optional["Employee"] = None  # Use string hint
        staff: list["Employee"] = []  # Use string hint

    class Employee(BaseModel):
        """Example employee model with circular references."""

        name: str
        department: "Department"  # Use string hint

    # Resolve forward references manually for the example models
    # Calling model_rebuild on both is necessary for Pydantic to link the string hints
    # The order might matter less here than with ForwardRef, but calling both is key.
    Employee.model_rebuild()
    Department.model_rebuild()

    # Get schema (e.g., from Department) - This should now work
    try:
        dept_schema = Department.model_json_schema()
        LOGGER.info("\n--- Original Department Schema (with circular ref) ---")
        LOGGER.info(json.dumps(dept_schema, indent=2))
        LOGGER.info("-" * 30)

        # --- Reconstruct from Circular Schema ---
        LOGGER.info("\n--- Reconstructing Model with Circular Reference ---")

        # Provide explicit name to avoid potential conflicts if running multiple times
        ReconstructedDept = create_pydantic_model_from_schema(
            dept_schema,
            model_name="ReconstructedDept",
        )
        LOGGER.info(
            "Successfully reconstructed model: %s",
            ReconstructedDept.__name__,
        )

        # --- Inspect the circularly referenced model fields ---
        LOGGER.info("\n--- Reconstructed Department Fields ---")
        for name, field_info in ReconstructedDept.model_fields.items():
            LOGGER.info("  - %s: %s", name, field_info.annotation)

        LOGGER.info(
            "\n--- Testing Instantiation (Circular - Structure Check) ---",
        )

        manager_field = ReconstructedDept.model_fields.get("manager")
        manager_type = manager_field.annotation if manager_field else "Not Found"
        LOGGER.info("Manager type annotation: %s", manager_type)

        staff_field = ReconstructedDept.model_fields.get("staff")
        staff_type = staff_field.annotation if staff_field else "Not Found"
        LOGGER.info("Staff type annotation: %s", staff_type)

        # --- Check the nested 'Employee' model from the definition cache ---
        reconstructed_employee_type = _DEFS_CACHE.get(
            "Employee",
        )  # Name from schema $defs

        if isinstance(reconstructed_employee_type, type) and issubclass(
            reconstructed_employee_type,
            BaseModel,
        ):
            LOGGER.info(
                "\n--- Reconstructed Employee (from Cache: %s) Fields ---",
                reconstructed_employee_type.__name__,
            )
            for (
                name,
                field_info,
            ) in reconstructed_employee_type.model_fields.items():
                LOGGER.info("  - %s: %s", name, field_info.annotation)
        elif isinstance(reconstructed_employee_type, ForwardRef):
            LOGGER.info(
                "\nReconstructed Employee model in cache is still a ForwardRef (resolution might have failed).",
            )
        else:
            LOGGER.info(
                "\nCould not retrieve reconstructed Employee model from cache (found: %s).",
                reconstructed_employee_type,
            )

    except pydantic.errors.PydanticSchemaGenerationError:
        LOGGER.info(
            "\n--- Error Generating Schema for Manually Defined Circular Models ---",
        )
        LOGGER.exception("Schema generation failed")
    except (ValueError, RuntimeError, RecursionError):
        LOGGER.info(
            "\n--- Error during circular reference reconstruction or testing ---",
        )
        LOGGER.exception("Circular reconstruction failed")

    # --- Example with Ebiose's Graph ---
    LOGGER.info("\n%s", "=" * 40)
    LOGGER.info("--- Testing Ebiose's Graph ---")

    # Get schema (e.g., from Department) - This should now work
    try:
        from ebiose.core.engines.graph_engine.graph import Graph

        with suppress(pydantic.PydanticUserError):
            Graph.model_rebuild()

        graph_schema = Graph.model_json_schema()
        LOGGER.info("\n--- Original Graph Schema ---")
        LOGGER.info(json.dumps(graph_schema, indent=2))
        LOGGER.info("-" * 30)

        # --- Reconstruct from Circular Schema ---
        LOGGER.info("\n--- Reconstructing Model ---")

        # Provide explicit name to avoid potential conflicts if running multiple times
        ReconstructedGraph = create_pydantic_model_from_schema(
            graph_schema,
            model_name="ReconstructedGraph",
        )
        LOGGER.info(
            "Successfully reconstructed model: %s",
            ReconstructedGraph.__name__,
        )

        # --- Inspect the circularly referenced model fields ---
        LOGGER.info("\n--- Reconstructed Graph Fields ---")
        for name, field_info in ReconstructedGraph.model_fields.items():
            LOGGER.info("  - %s: %s", name, field_info.annotation)

    except ImportError as e:
        LOGGER.info("Skipping Ebiose Graph test due to environment/path issues: %s", e)
    except (RuntimeError, ValueError, RecursionError, pydantic.PydanticUserError) as e:
        LOGGER.info(
            "Skipping Ebiose Graph test due to Pydantic error in source model: %s", e
        )
