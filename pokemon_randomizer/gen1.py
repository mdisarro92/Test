"""Generation I randomization routines."""

from __future__ import annotations

from .core import StructuredRandomizer
from .wild import WildEntryDefinition, WildTableDefinition, find_wild_table, randomize_table


class Gen1Randomizer(StructuredRandomizer):
    max_species = 151
    legendary_species = (144, 145, 146, 150, 151)

    TRAINER_TABLE_OFFSET = 0x2000
    TRAINER_PARTY_SIZE = 3
    STARTER_OFFSET = 0x2100
    STARTER_COUNT = 3
    STATIC_TABLE_OFFSET = 0x2110
    SHOP_TABLE_OFFSET = 0x2200
    SHOP_ITEM_COUNT = 4
    MOVESET_TABLE_OFFSET = 0x2300
    MOVES_PER_SPECIES = 4
    TYPING_TABLE_OFFSET = 0x2400
    EVOLUTION_TABLE_OFFSET = 0x2500
    TMHM_TABLE_OFFSET = 0x2600
    BASE_STATS_TABLE_OFFSET = 0x2700
    PROGRESSION_ITEMS = (1, 2, 3, 4)

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
