import inspect
from typing import get_type_hints, get_origin, get_args, Union


def tool(f):
    sig = inspect.signature(f)
    hints = get_type_hints(f)
    props, required = {}, []
    type_map = {
        int: "integer",
        float: "number",
        str: "string",
        bool: "boolean",
        list: "array",
        dict: "object",
    }

    for name, p in sig.parameters.items():
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        typ = hints.get(name, str)
        origin = get_origin(typ)
        if origin in (Union, type(Union)):  # handle Optional
            typ = next((a for a in get_args(typ) if a is not type(None)), str)
        js_type = type_map.get(origin or typ, "string")
        props[name] = {
            "type": js_type,
            "description": f"'{name}'"
            + (
                f" (default {p.default})"
                if p.default is not inspect.Parameter.empty
                else ""
            ),
        }
        if p.default is inspect.Parameter.empty:
            required.append(name)

    doc = inspect.getdoc(f) or ""
    description = doc or f.__name__

    f._tool_schema = {
        "type": "function",
        "function": {
            "name": f.__name__,
            "description": description,
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }
    return f
