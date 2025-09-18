"""Command line interface for the Pokémon randomizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

from .core import randomize_rom
from .options import build_options, resolve_paths, summarize_features


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
    parser.add_argument(
        "--randomize-trainers",
        action="store_true",
        help="Randomize trainer parties",
    )
    parser.add_argument(
        "--trainer-type-theme",
        choices=("off", "monotype"),
        default="off",
        help="Apply themed trainer parties (default: off)",
    )
    parser.add_argument(
        "--randomize-starters",
        action="store_true",
        help="Randomize starter Pokémon",
    )
    parser.add_argument(
        "--randomize-static",
        action="store_true",
        help="Randomize static encounters and gifts",
    )
    parser.add_argument(
        "--randomize-items",
        action="store_true",
        help="Randomize shop inventories and items",
    )
    parser.add_argument(
        "--no-progress-safeguards",
        action="store_true",
        help="Allow progression-critical items to change when randomizing items",
    )
    parser.add_argument(
        "--randomize-movesets",
        action="store_true",
        help="Randomize level-up movesets",
    )
    parser.add_argument(
        "--randomize-typings",
        action="store_true",
        help="Randomize Pokémon typings",
    )
    parser.add_argument(
        "--randomize-evolutions",
        action="store_true",
        help="Randomize evolution outcomes",
    )
    parser.add_argument(
        "--evolution-consistency",
        action="store_true",
        help="Ensure evolution difficulty increases are preserved",
    )
    parser.add_argument(
        "--randomize-tm-compatibility",
        action="store_true",
        help="Randomize TM/HM compatibility flags",
    )
    parser.add_argument(
        "--randomize-base-stats",
        action="store_true",
        help="Randomize base stats while preserving totals",
    )
    parser.add_argument(
        "--min-bst",
        type=int,
        default=None,
        help="Minimum base stat total when selecting new species",
    )
    parser.add_argument(
        "--max-bst",
        type=int,
        default=None,
        help="Maximum base stat total when selecting new species",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    rom_path, output_path = resolve_paths(args.rom, args.output)
    try:
        options = build_options(
            seed=args.seed,
            allow_legendaries=args.allow_legendaries,
            disable_wild=args.no_wild,
            randomize_trainers=args.randomize_trainers,
            trainer_type_theme=args.trainer_type_theme,
            randomize_starters=args.randomize_starters,
            randomize_static=args.randomize_static,
            randomize_items=args.randomize_items,
            safeguard_progression_items=not args.no_progress_safeguards,
            randomize_movesets=args.randomize_movesets,
            randomize_typings=args.randomize_typings,
            randomize_evolutions=args.randomize_evolutions,
            evolution_consistency=args.evolution_consistency,
            randomize_tm_compatibility=args.randomize_tm_compatibility,
            randomize_base_stats=args.randomize_base_stats,
            min_bst=args.min_bst,
            max_bst=args.max_bst,
        )
    except ValueError as exc:
        parser.error(str(exc))

    try:
        info = randomize_rom(rom_path, output_path, options)
    except FileNotFoundError as exc:
        parser.error(str(exc))
    except ValueError as exc:
        parser.error(str(exc))

    feature_summary = summarize_features(options)
    print(
        f"Randomized {info.title} (Generation {info.generation}) using seed {options.seed!r}. "
        f"Modified features: {feature_summary}."
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    sys.exit(main())
