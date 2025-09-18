"""Generation I randomization routines."""

from __future__ import annotations

from .core import BaseRandomizer
from .wild import WildEntryDefinition, WildTableDefinition, find_wild_table, randomize_table


class Gen1Randomizer(BaseRandomizer):
    max_species = 151
    legendary_species = (144, 145, 146, 150, 151)

    WILD_TABLE = WildTableDefinition(
        name="Kanto wild encounters",
        pointer_count=249,
        entry=WildEntryDefinition(
            length=21,
            species_offsets=tuple(2 + i * 2 for i in range(10)),
        ),
    )

    def randomize_wild_pokemon(self, rom: bytearray) -> None:
        table = find_wild_table(rom, self.WILD_TABLE, self.max_species)
        species_pool = self.build_species_pool()
        randomize_table(table, rom, species_pool, self.rng)
