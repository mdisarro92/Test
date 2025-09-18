"""Shared helpers for building randomization options from user input."""

from __future__ import annotations

from pathlib import Path

from .core import RandomizationOptions


def normalize_seed(seed: str | int | None) -> str | int | None:
    """Return a normalized seed value.

    Empty strings are converted to ``None`` so optional UI elements can pass
    blank values without additional checks.
    """

    if seed is None:
        return None
    if isinstance(seed, str):
        seed = seed.strip()
        if not seed:
            return None
    return seed


def build_options(
    *,
    seed: str | int | None,
    allow_legendaries: bool,
    disable_wild: bool,
) -> RandomizationOptions:
    """Create :class:`RandomizationOptions` from raw flag values."""

    normalized_seed = normalize_seed(seed)
    return RandomizationOptions(
        seed=normalized_seed,
        randomize_wild=not disable_wild,
        allow_legendaries=allow_legendaries,
    )


def resolve_paths(rom: str | Path, output: str | Path) -> tuple[Path, Path]:
    """Normalize input and output paths.

    ``Path`` objects passed by the CLI are accepted, while strings coming from
    the GUI are expanded to allow user shortcuts such as ``~``.
    """

    rom_path = Path(rom).expanduser()
    output_path = Path(output).expanduser()
    return rom_path, output_path
