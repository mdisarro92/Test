"""Generation II randomization routines."""

from __future__ import annotations

from .core import BaseRandomizer
from .wild import WildEntryDefinition, WildTableDefinition, find_wild_table, randomize_table


def _grass_species_offsets() -> tuple[int, ...]:
    offsets = []
    base = 3
    block_length = 14
    for block in range(3):  # morning, day, night
        block_base = base + block * block_length
        for slot in range(7):
            offsets.append(block_base + slot * 2 + 1)
    return tuple(offsets)


def _water_species_offsets() -> tuple[int, ...]:
    return (2, 4, 6)


class Gen2Randomizer(BaseRandomizer):
    max_species = 251
    legendary_species = (
        144,
        145,
        146,
        150,
        151,
        243,
        244,
        245,
        249,
        250,
        251,
    )

    WILD_TABLES = (
        WildTableDefinition(
            name="Johto grass encounters",
            pointer_count=61,
            entry=WildEntryDefinition(length=45, species_offsets=_grass_species_offsets()),
        ),
        WildTableDefinition(
            name="Kanto grass encounters",
            pointer_count=30,
            entry=WildEntryDefinition(length=45, species_offsets=_grass_species_offsets()),
        ),
        WildTableDefinition(
            name="Johto water encounters",
            pointer_count=38,
            entry=WildEntryDefinition(length=7, species_offsets=_water_species_offsets()),
        ),
        WildTableDefinition(
            name="Kanto water encounters",
            pointer_count=24,
            entry=WildEntryDefinition(length=7, species_offsets=_water_species_offsets()),
        ),
    )

    def randomize_wild_pokemon(self, rom: bytearray) -> None:
        species_pool = self.build_species_pool()
        used_entries: set[int] = set()
        for definition in self.WILD_TABLES:
            table = find_wild_table(
                rom,
                definition,
                self.max_species,
                used_entries=used_entries,
            )
            used_entries.update(table.entry_offsets)
            randomize_table(table, rom, species_pool, self.rng)
