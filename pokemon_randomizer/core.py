"""Core orchestration logic for the Pokémon randomizer."""

from __future__ import annotations

import random as _random
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Type


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

    #: Human readable type names used by the simplified deterministic model.
    TYPE_NAMES: tuple[str, ...] = (
        "NORMAL",
        "FIRE",
        "WATER",
        "GRASS",
        "ELECTRIC",
        "ICE",
        "FIGHTING",
        "POISON",
        "GROUND",
        "FLYING",
        "PSYCHIC",
        "BUG",
        "ROCK",
        "GHOST",
        "DRAGON",
        "DARK",
        "STEEL",
    )
    TYPE_NAME_TO_ID: dict[str, int] = {name: index for index, name in enumerate(TYPE_NAMES, start=1)}
    TYPE_ID_TO_NAME: dict[int, str] = {index: name for name, index in TYPE_NAME_TO_ID.items()}
    TYPE_NONE: int = 0

    #: Items that should remain stable when progression safeguards are enabled.
    PROGRESSION_ITEMS: tuple[int, ...] = (1, 2, 3, 4, 5)

    def __init__(self, rng, options: "RandomizationOptions") -> None:
        self.rng = rng
        self.options = options
        self._custom_typings: dict[int, tuple[str, ...]] = {}
        self._custom_base_stats: dict[int, tuple[int, ...]] = {}
        self._base_stat_cache: dict[int, tuple[int, ...]] = {}

    def randomize_wild_pokemon(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_trainer_parties(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_starters(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_static_encounters(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_items_and_shops(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_movesets(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_typings(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_evolutions(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_tm_hm_compatibility(self, rom: bytearray) -> None:
        raise NotImplementedError

    def randomize_base_stats(self, rom: bytearray) -> None:
        raise NotImplementedError

    def build_species_pool(self) -> list[int]:
        """Return a pool of species IDs that satisfy the configured filters."""

        species = list(range(1, self.max_species + 1))
        if not self.options.allow_legendaries and self.legendary_species:
            forbidden = set(self.legendary_species)
            species = [s for s in species if s not in forbidden]

        min_bst = self.options.min_bst
        if min_bst is not None:
            species = [s for s in species if self.get_species_bst(s) >= min_bst]

        max_bst = self.options.max_bst
        if max_bst is not None:
            species = [s for s in species if self.get_species_bst(s) <= max_bst]

        if not species:
            species = list(range(1, self.max_species + 1))
        return species

    @classmethod
    def type_id_to_name(cls, type_id: int) -> str | None:
        if type_id == cls.TYPE_NONE:
            return None
        return cls.TYPE_ID_TO_NAME.get(type_id)

    def get_species_types(self, species_id: int) -> tuple[str, ...]:
        """Return the configured types for *species_id*."""

        if species_id in self._custom_typings:
            return self._custom_typings[species_id]

        primary_index = (species_id - 1) % len(self.TYPE_NAMES)
        primary = self.TYPE_NAMES[primary_index]
        secondary_index = (species_id - 1) // len(self.TYPE_NAMES)
        secondary_index = secondary_index % len(self.TYPE_NAMES)
        secondary = self.TYPE_NAMES[secondary_index]
        if secondary == primary:
            return (primary,)
        return (primary, secondary)

    def get_species_by_type(
        self, type_name: str, pool: Sequence[int] | None = None
    ) -> list[int]:
        """Return all species that include *type_name* within *pool*."""

        if pool is None:
            pool = range(1, self.max_species + 1)
        return [species for species in pool if type_name in self.get_species_types(species)]

    def get_species_base_stats(self, species_id: int) -> tuple[int, ...]:
        if species_id in self._custom_base_stats:
            return self._custom_base_stats[species_id]
        if species_id not in self._base_stat_cache:
            rng = _random.Random(species_id)
            self._base_stat_cache[species_id] = tuple(
                30 + rng.randint(0, 70) for _ in range(6)
            )
        return self._base_stat_cache[species_id]

    def get_species_bst(self, species_id: int) -> int:
        return sum(self.get_species_base_stats(species_id))

    def _pick_species(self, pool: Sequence[int]) -> int:
        if not pool:
            raise ValueError("Cannot select a species from an empty pool")
        return self.rng.choice(list(pool))

    def _sample_species(self, pool: Sequence[int], count: int) -> list[int]:
        pool_list = list(pool)
        if not pool_list:
            raise ValueError("Cannot sample species from an empty pool")
        if len(pool_list) >= count:
            return self.rng.sample(pool_list, count)
        return [self.rng.choice(pool_list) for _ in range(count)]

    def _species_for_monotype(self, pool: Sequence[int]) -> list[int]:
        type_names = list(self.TYPE_NAMES)
        self.rng.shuffle(type_names)
        for type_name in type_names:
            themed_pool = self.get_species_by_type(type_name, pool)
            if themed_pool:
                return themed_pool
        return list(pool)

    def _apply_trainer_theme(self, pool: Sequence[int]) -> list[int]:
        theme = (self.options.trainer_type_theme or "off").lower()
        if theme == "monotype":
            themed_pool = self._species_for_monotype(pool)
            if themed_pool:
                return themed_pool
        return list(pool)

    def _random_item_id(self, current: int | None = None) -> int:
        while True:
            candidate = self.rng.randint(1, 250)
            if current is not None and candidate == current:
                continue
            if self.options.safeguard_progression_items and candidate in self.PROGRESSION_ITEMS:
                continue
            return candidate

    def _random_unique_moves(self, count: int) -> list[int]:
        moves: list[int] = []
        while len(moves) < count:
            move = self.rng.randint(1, 250)
            if move not in moves:
                moves.append(move)
        return moves

    def _redistribute_stats(self, total: int, *, count: int = 6) -> list[int]:
        if total <= 0:
            total = 300
        weights = [self.rng.random() for _ in range(count)]
        weight_sum = sum(weights) or 1.0
        stats = [
            max(1, min(255, int(total * weight / weight_sum))) for weight in weights
        ]
        difference = total - sum(stats)
        while difference > 0:
            index = self.rng.randrange(count)
            if stats[index] < 255:
                stats[index] += 1
                difference -= 1
        while difference < 0:
            index = self.rng.randrange(count)
            if stats[index] > 1:
                stats[index] -= 1
                difference += 1
        return stats


class StructuredRandomizer(BaseRandomizer):
    """Utility class implementing the shared structured table logic."""

    TRAINER_TABLE_OFFSET: int | None = None
    TRAINER_PARTY_SIZE: int = 0
    STARTER_OFFSET: int | None = None
    STARTER_COUNT: int = 0
    STATIC_TABLE_OFFSET: int | None = None
    SHOP_TABLE_OFFSET: int | None = None
    SHOP_ITEM_COUNT: int = 0
    MOVESET_TABLE_OFFSET: int | None = None
    MOVES_PER_SPECIES: int = 0
    TYPING_TABLE_OFFSET: int | None = None
    EVOLUTION_TABLE_OFFSET: int | None = None
    TMHM_TABLE_OFFSET: int | None = None
    BASE_STATS_TABLE_OFFSET: int | None = None

    def randomize_trainer_parties(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.TRAINER_TABLE_OFFSET is None or self.TRAINER_PARTY_SIZE <= 0:
            raise NotImplementedError("Trainer table not defined for this game.")
        offset = self.TRAINER_TABLE_OFFSET
        trainer_count = rom[offset]
        if trainer_count == 0:
            return
        pos = offset + 1
        base_pool = self.build_species_pool()
        for _ in range(trainer_count):
            themed_pool = self._apply_trainer_theme(base_pool)
            for slot in range(self.TRAINER_PARTY_SIZE):
                rom[pos + slot] = self._pick_species(themed_pool)
            pos += self.TRAINER_PARTY_SIZE

    def randomize_starters(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.STARTER_OFFSET is None or self.STARTER_COUNT <= 0:
            raise NotImplementedError("Starter table not defined for this game.")
        pool = self.build_species_pool()
        starters = self._sample_species(pool, self.STARTER_COUNT)
        for index, species in enumerate(starters):
            rom[self.STARTER_OFFSET + index] = species

    def randomize_static_encounters(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.STATIC_TABLE_OFFSET is None:
            raise NotImplementedError("Static encounter table not defined for this game.")
        offset = self.STATIC_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        pool = self.build_species_pool()
        pos = offset + 1
        for _ in range(count):
            rom[pos] = self._pick_species(pool)
            pos += 1

    def randomize_items_and_shops(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.SHOP_TABLE_OFFSET is None or self.SHOP_ITEM_COUNT <= 0:
            raise NotImplementedError("Shop table not defined for this game.")
        offset = self.SHOP_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        pos = offset + 1
        for _ in range(count):
            for _ in range(self.SHOP_ITEM_COUNT):
                current = rom[pos]
                if (
                    self.options.safeguard_progression_items
                    and current in self.PROGRESSION_ITEMS
                ):
                    pos += 1
                    continue
                rom[pos] = self._random_item_id(current)
                pos += 1

    def randomize_movesets(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.MOVESET_TABLE_OFFSET is None or self.MOVES_PER_SPECIES <= 0:
            raise NotImplementedError("Moveset table not defined for this game.")
        offset = self.MOVESET_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        pos = offset + 1
        for _ in range(count):
            pos += 1  # skip species identifier
            moves = self._random_unique_moves(self.MOVES_PER_SPECIES)
            for move in moves:
                rom[pos] = move
                pos += 1

    def randomize_typings(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.TYPING_TABLE_OFFSET is None:
            raise NotImplementedError("Typing table not defined for this game.")
        offset = self.TYPING_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        pos = offset + 1
        for _ in range(count):
            species = rom[pos]
            pos += 1
            primary = self.rng.choice(self.TYPE_NAMES)
            secondary = self.rng.choice([None] + list(self.TYPE_NAMES))
            if secondary == primary:
                secondary = None
            rom[pos] = self.TYPE_NAME_TO_ID[primary]
            pos += 1
            if secondary is None:
                rom[pos] = self.TYPE_NONE
                types = (primary,)
            else:
                rom[pos] = self.TYPE_NAME_TO_ID[secondary]
                types = (primary, secondary)
            pos += 1
            self._custom_typings[species] = types

    def randomize_evolutions(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.EVOLUTION_TABLE_OFFSET is None:
            raise NotImplementedError("Evolution table not defined for this game.")
        offset = self.EVOLUTION_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        base_pool = self.build_species_pool()
        pos = offset + 1
        for _ in range(count):
            species = rom[pos]
            pos += 1
            target_offset = pos
            current_target = rom[target_offset]
            if current_target != 0:
                pool = [s for s in base_pool if s != species]
                if not pool:
                    pool = [s for s in range(1, self.max_species + 1) if s != species]
                if self.options.evolution_consistency:
                    base_bst = self.get_species_bst(species)
                    consistent = [
                        candidate
                        for candidate in pool
                        if self.get_species_bst(candidate) >= base_bst
                    ]
                    if consistent:
                        pool = consistent
                    else:
                        pos += 1
                        continue
                rom[target_offset] = self._pick_species(pool)
            pos += 1

    def randomize_tm_hm_compatibility(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.TMHM_TABLE_OFFSET is None:
            raise NotImplementedError("TM/HM table not defined for this game.")
        offset = self.TMHM_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        pos = offset + 1
        for _ in range(count):
            pos += 1  # skip species identifier
            rom[pos] = self.rng.randint(1, 255)
            pos += 1

    def randomize_base_stats(self, rom: bytearray) -> None:  # noqa: D401 - see base
        if self.BASE_STATS_TABLE_OFFSET is None:
            raise NotImplementedError("Base stats table not defined for this game.")
        offset = self.BASE_STATS_TABLE_OFFSET
        count = rom[offset]
        if count == 0:
            return
        pos = offset + 1
        for _ in range(count):
            species = rom[pos]
            pos += 1
            original = [int(value) for value in rom[pos : pos + 6]]
            total = sum(original)
            new_stats = self._redistribute_stats(total)
            for value in new_stats:
                rom[pos] = value
                pos += 1
            stats_tuple = tuple(new_stats)
            self._custom_base_stats[species] = stats_tuple
            self._base_stat_cache[species] = stats_tuple


@dataclass
class RandomizationOptions:
    """Configuration for the randomization process."""

    seed: Optional[int] = None
    randomize_wild: bool = True
    allow_legendaries: bool = False
    randomize_trainers: bool = False
    trainer_type_theme: str = "off"
    randomize_starters: bool = False
    randomize_static: bool = False
    randomize_items: bool = False
    safeguard_progression_items: bool = True
    randomize_movesets: bool = False
    randomize_typings: bool = False
    randomize_evolutions: bool = False
    evolution_consistency: bool = False
    randomize_tm_compatibility: bool = False
    randomize_base_stats: bool = False
    min_bst: Optional[int] = None
    max_bst: Optional[int] = None


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

    rng = _random.Random(options.seed)
    randomizer = info.randomizer_cls(rng, options)

    if options.randomize_base_stats:
        randomizer.randomize_base_stats(data)
    if options.randomize_typings:
        randomizer.randomize_typings(data)
    if options.randomize_wild:
        randomizer.randomize_wild_pokemon(data)
    if options.randomize_trainers:
        randomizer.randomize_trainer_parties(data)
    if options.randomize_starters:
        randomizer.randomize_starters(data)
    if options.randomize_static:
        randomizer.randomize_static_encounters(data)
    if options.randomize_items:
        randomizer.randomize_items_and_shops(data)
    if options.randomize_movesets:
        randomizer.randomize_movesets(data)
    if options.randomize_evolutions:
        randomizer.randomize_evolutions(data)
    if options.randomize_tm_compatibility:
        randomizer.randomize_tm_hm_compatibility(data)

    Path(output_path).write_bytes(data)
    return info
