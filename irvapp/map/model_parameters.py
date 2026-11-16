"""Stable scenario keys shared by model creation and API lookups."""

import json


def canonical_parameter_key(values):
    def normalize(value):
        # JSON numbers do not distinguish between 2 and 2.0. In particular,
        # JavaScript serializes both as 2, including inside arrays and objects.
        if isinstance(value, float) and value.is_integer():
            return int(value)
        if isinstance(value, dict):
            return {name: normalize(item) for name, item in value.items()}
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    return json.dumps(normalize(values), sort_keys=True, separators=(",", ":"))
