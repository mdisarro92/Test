"""Shared helpers for building randomization options from user input."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

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
    randomize_trainers: bool,
    trainer_type_theme: str,
    randomize_starters: bool,
    randomize_static: bool,
    randomize_items: bool,
    safeguard_progression_items: bool,
    randomize_movesets: bool,
    randomize_typings: bool,
    randomize_evolutions: bool,
    evolution_consistency: bool,
    randomize_tm_compatibility: bool,
    randomize_base_stats: bool,
    min_bst: int | None,
    max_bst: int | None,
) -> RandomizationOptions:
    """Create :class:`RandomizationOptions` from raw flag values."""

    normalized_seed = normalize_seed(seed)
    normalized_theme = validate_trainer_theme(trainer_type_theme)
    if min_bst is not None and max_bst is not None and min_bst > max_bst:
        raise ValueError("Minimum base stat total cannot exceed the maximum value")
    return RandomizationOptions(
        seed=normalized_seed,
        randomize_wild=not disable_wild,
        allow_legendaries=allow_legendaries,
        randomize_trainers=randomize_trainers,
        trainer_type_theme=normalized_theme,
        randomize_starters=randomize_starters,
        randomize_static=randomize_static,
        randomize_items=randomize_items,
        safeguard_progression_items=safeguard_progression_items,
        randomize_movesets=randomize_movesets,
        randomize_typings=randomize_typings,
        randomize_evolutions=randomize_evolutions,
        evolution_consistency=evolution_consistency,
        randomize_tm_compatibility=randomize_tm_compatibility,
        randomize_base_stats=randomize_base_stats,
        min_bst=min_bst,
        max_bst=max_bst,
    )


def resolve_paths(rom: str | Path, output: str | Path) -> tuple[Path, Path]:
    """Normalize input and output paths.

    ``Path`` objects passed by the CLI are accepted, while strings coming from
    the GUI are expanded to allow user shortcuts such as ``~``.
    """

    rom_path = Path(rom).expanduser()
    output_path = Path(output).expanduser()
    return rom_path, output_path


def validate_trainer_theme(theme: str) -> str:
    """Return a normalized trainer type theme name."""

    normalized = theme.strip().lower()
    if normalized not in {"off", "monotype"}:
        raise ValueError(f"Unsupported trainer type theme: {theme!r}")
    return normalized


def parse_optional_int(value: str | int | None) -> Optional[int]:
    """Convert *value* to an integer if provided, otherwise return ``None``."""

    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = value.strip()
    if not text:
        return None
    return int(text, 10)


FEATURE_FLAGS: tuple[tuple[str, str], ...] = (
    ("randomize_wild", "wild encounters"),
    ("randomize_trainers", "trainer parties"),
    ("randomize_starters", "starter Pokémon"),
    ("randomize_static", "static encounters"),
    ("randomize_items", "items and shops"),
    ("randomize_movesets", "movesets"),
    ("randomize_typings", "typings"),
    ("randomize_evolutions", "evolutions"),
    ("randomize_tm_compatibility", "TM/HM compatibility"),
    ("randomize_base_stats", "base stats"),
)


def summarize_features(options: RandomizationOptions) -> str:
    """Return a comma separated description of the enabled randomizations."""

    enabled = [label for attr, label in FEATURE_FLAGS if getattr(options, attr)]
    if not enabled:
        return "no features"
    return ", ".join(enabled)
