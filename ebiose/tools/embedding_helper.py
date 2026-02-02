"""Copyright (c) 2024, Inria.

Pre-release Version - DO NOT DISTRIBUTE
This software is licensed under the MIT License. See LICENSE for details.
"""

from collections.abc import Sequence
from typing import cast

import numpy as np


def generate_embeddings(text: str) -> np.ndarray:
    """Generate an embedding for the given text.

    Args:
        text: Input text to embed.

    Returns:
        Embedding vector.

    """
    fake = True
    if fake:
        return generate_fake_embedding()
    return generate_embeddings_impl(text)


def embedding_distance(
    emb_a: np.ndarray | Sequence[float],
    emb_b: np.ndarray | Sequence[float],
) -> float:
    """Compute cosine distance between two embeddings.

    Args:
        emb_a: First embedding.
        emb_b: Second embedding.

    Returns:
        Cosine distance as a float.

    """
    vec_a = np.asarray(emb_a, dtype=float)
    vec_b = np.asarray(emb_b, dtype=float)
    return cast(
        "float",
        1 - np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)),
    )


def generate_fake_embedding(dimension: int = 1536) -> np.ndarray:
    """Generate a normalized random embedding for testing.

    Args:
        dimension: Embedding dimensionality.

    Returns:
        Random unit-length embedding vector.

    """
    rng = np.random.default_rng()
    fake_embedding = rng.random(dimension)
    return fake_embedding / np.linalg.norm(fake_embedding)


def generate_embeddings_impl(text: str) -> np.ndarray:
    """Generate embeddings using the real backend (not implemented).

    Args:
        text: Input text to embed.

    Raises:
        NotImplementedError: Always, until a backend is integrated.

    """
    msg = "This function is not implemented yet"
    raise NotImplementedError(msg)
