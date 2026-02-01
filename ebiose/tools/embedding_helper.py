"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from collections.abc import Sequence
from typing import cast

import numpy as np


def generate_embeddings(text: str) -> np.ndarray:
    fake = True
    if fake:
        return generate_fake_embedding()
    return generate_embeddings_impl(text)


def embedding_distance(
    emb_a: np.ndarray | Sequence[float],
    emb_b: np.ndarray | Sequence[float],
) -> float:
    vec_a = np.asarray(emb_a, dtype=float)
    vec_b = np.asarray(emb_b, dtype=float)
    return cast(
        "float",
        1 - np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)),
    )


def generate_fake_embedding(dimension: int = 1536) -> np.ndarray:
    rng = np.random.default_rng()
    fake_embedding = rng.random(dimension)
    return fake_embedding / np.linalg.norm(fake_embedding)


def generate_embeddings_impl(text: str) -> np.ndarray:
    msg = "This function is not implemented yet"
    raise NotImplementedError(msg)
