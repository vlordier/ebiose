"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

import json
from pathlib import Path
from typing import cast


def load_model_prices_and_context_window() -> dict[str, object]:
    """Load model pricing metadata from the bundled JSON file."""
    # Compute the project root relative to this file
    project_root = Path(__file__).parents[2]
    json_path = (
        project_root / "ebiose" / "tools" / "model_prices_and_context_window.json"
    )

    with json_path.open(encoding="utf-8") as file:
        return cast("dict[str, object]", json.load(file))
