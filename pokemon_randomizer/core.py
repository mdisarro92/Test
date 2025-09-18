"""Core orchestration logic for the Pokémon randomizer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Type


@dataclass(frozen=True)
class GameInfo:
    """Metadata and handler for a supported game."""

    title: str
    generation: int
    randomizer_cls: Type["BaseRandomizer"]


class BaseRandomizer:
    """Base interface for generation specific randomizers."""

    #: Maximum species ID present in the game.
    max_species: int = 0
    #: Species IDs that should be treated as legendary.
    legendary_species: tuple[int, ...] = ()

    def __init__(self, rng, options: "RandomizationOptions") -> None:
        self.rng = rng
        self.options = options

    def randomize_wild_pokemon(self, rom: bytearray) -> None:
        raise NotImplementedError

    def build_species_pool(self) -> list[int]:
        species = list(range(1, self.max_species + 1))
        if not self.options.allow_legendaries and self.legendary_species:
            forbidden = set(self.legendary_species)
            species = [s for s in species if s not in forbidden]
        return species


@dataclass
class RandomizationOptions:
    """Configuration for the randomization process."""

    seed: Optional[int] = None
    randomize_wild: bool = True
    allow_legendaries: bool = False


def _build_title_map() -> dict[str, GameInfo]:
    from .gen1 import Gen1Randomizer
    from .gen2 import Gen2Randomizer

    return {
        "POKEMON RED": GameInfo("Pokémon Red", 1, Gen1Randomizer),
        "POKEMON BLUE": GameInfo("Pokémon Blue", 1, Gen1Randomizer),
        "POKEMON BL": GameInfo("Pokémon Blue", 1, Gen1Randomizer),
        "POKEMON GREEN": GameInfo("Pokémon Green", 1, Gen1Randomizer),
        "POKEMON Y": GameInfo("Pokémon Yellow", 1, Gen1Randomizer),
        "POKEMON G": GameInfo("Pokémon Gold", 2, Gen2Randomizer),
        "POKEMON S": GameInfo("Pokémon Silver", 2, Gen2Randomizer),
        "POKEMON C": GameInfo("Pokémon Crystal", 2, Gen2Randomizer),
    }


GAME_TITLE_MAP: dict[str, GameInfo] = _build_title_map()


def detect_game(rom_bytes: bytes) -> GameInfo:
    """Return information about the provided ROM."""

    if len(rom_bytes) < 0x150:
        raise ValueError("Provided file is smaller than a valid Game Boy ROM header")

    raw_title = rom_bytes[0x134:0x144]
    try:
        decoded = raw_title.decode("ascii")
    except UnicodeDecodeError:
        decoded = raw_title.decode("latin-1", errors="ignore")
    title = decoded.strip("\0\uffff ")
    for key, info in GAME_TITLE_MAP.items():
        if title.startswith(key):
            return info
    raise ValueError(f"Unsupported or unknown ROM title: {title!r}")


def randomize_rom(
    input_path: str | Path,
    output_path: str | Path,
    options: RandomizationOptions,
) -> GameInfo:
    """Randomize the ROM located at *input_path* and write the result to *output_path*."""

    data = bytearray(Path(input_path).read_bytes())
    info = detect_game(data)

    import random

    rng = random.Random(options.seed)
    randomizer = info.randomizer_cls(rng, options)

    if options.randomize_wild:
        randomizer.randomize_wild_pokemon(data)

    Path(output_path).write_bytes(data)
    return info
