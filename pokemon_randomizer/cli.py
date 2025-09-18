"""Command line interface for the Pokémon randomizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from .core import RandomizationOptions, randomize_rom


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Randomize wild Pokémon encounters for Generation I and II Game Boy games. "
            "Only ROMs with their original headers are supported."
        )
    )
    parser.add_argument("rom", type=Path, help="Path to the original ROM file")
    parser.add_argument(
        "output",
        type=Path,
        help="Where to write the randomized ROM",
    )
    parser.add_argument(
        "--seed",
        type=str,
        default=None,
        help="Random seed (numbers or arbitrary strings are accepted)",
    )
    parser.add_argument(
        "--allow-legendaries",
        action="store_true",
        help="Permit legendary Pokémon to appear in the wild",
    )
    parser.add_argument(
        "--no-wild",
        action="store_true",
        help="Disable wild Pokémon randomization",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    options = RandomizationOptions(
        seed=args.seed,
        randomize_wild=not args.no_wild,
        allow_legendaries=args.allow_legendaries,
    )

    try:
        info = randomize_rom(args.rom, args.output, options)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(str(exc))

    if not args.no_wild:
        feature_summary = "wild encounters"
    else:
        feature_summary = "no features"
    print(
        f"Randomized {info.title} (Generation {info.generation}) using seed {options.seed!r}. "
        f"Modified features: {feature_summary}."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    sys.exit(main())
