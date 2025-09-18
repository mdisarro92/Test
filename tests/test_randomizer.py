import random
from itertools import cycle

from pokemon_randomizer.core import RandomizationOptions
from pokemon_randomizer.gen1 import Gen1Randomizer
from pokemon_randomizer.gen2 import Gen2Randomizer
from pokemon_randomizer.wild import BANK_SIZE


def _write_pointer(rom: bytearray, offset: int, value: int) -> None:
    rom[offset] = value & 0xFF
    rom[offset + 1] = (value >> 8) & 0xFF


def build_gen1_test_rom() -> bytearray:
    rom = bytearray([0] * (BANK_SIZE * 3))
    table = Gen1Randomizer.WILD_TABLE
    bank = 1
    table_offset = bank * BANK_SIZE
    entry_len = table.entry.length
    data_offset = table_offset + table.pointer_count * 2

    species_iter = cycle(range(1, Gen1Randomizer.max_species + 1))
    for index in range(table.pointer_count):
        entry_start = data_offset + index * entry_len
        pointer_value = 0x4000 + (entry_start - bank * BANK_SIZE)
        _write_pointer(rom, table_offset + index * 2, pointer_value)
        rom[entry_start] = 10  # encounter rate
        for slot in range(10):
            level = (slot + 5) % 99 + 1
            species = next(species_iter)
            species_offsets = table.entry.species_offsets
            species_pos = entry_start + species_offsets[slot]
            level_pos = species_pos - 1
            rom[level_pos] = level
            rom[species_pos] = species
    return rom


def build_gen2_test_rom() -> bytearray:
    rom = bytearray([0] * (BANK_SIZE * 8))
    tables = zip(
        (1, 2, 3, 4),
        Gen2Randomizer.WILD_TABLES,
    )
    for bank, table in tables:
        table_offset = bank * BANK_SIZE
        entry_len = table.entry.length
        data_offset = table_offset + table.pointer_count * 2
        species_iter = cycle(range(1, Gen2Randomizer.max_species + 1))
        for index in range(table.pointer_count):
            entry_start = data_offset + index * entry_len
            pointer_value = 0x4000 + (entry_start - bank * BANK_SIZE)
            _write_pointer(rom, table_offset + index * 2, pointer_value)
            if table.entry.length == 45:
                # grass encounter, three time slots with seven entries each
                for block in range(3):
                    for slot in range(7):
                        species_pos = entry_start + table.entry.species_offsets[block * 7 + slot]
                        level_pos = species_pos - 1
                        rom[level_pos] = (slot + block + 5) % 99 + 1
                        rom[species_pos] = next(species_iter)
                rom[entry_start] = 5
                rom[entry_start + 1] = 5
                rom[entry_start + 2] = 5
            else:
                # water encounter with three slots
                rom[entry_start] = 5
                for slot in range(3):
                    species_pos = entry_start + table.entry.species_offsets[slot]
                    level_pos = species_pos - 1
                    rom[level_pos] = (slot + 10) % 99 + 1
                    rom[species_pos] = next(species_iter)
    return rom


def test_gen1_randomization_excludes_legendaries():
    rom = build_gen1_test_rom()
    options = RandomizationOptions(seed=123, allow_legendaries=False)
    randomizer = Gen1Randomizer(random.Random(options.seed), options)
    randomizer.randomize_wild_pokemon(rom)

    legendary_set = set(randomizer.legendary_species)
    table = Gen1Randomizer.WILD_TABLE
    bank = 1
    data_offset = bank * BANK_SIZE + table.pointer_count * 2
    for entry_index in range(table.pointer_count):
        entry_start = data_offset + entry_index * table.entry.length
        for rel in table.entry.species_offsets:
            species = rom[entry_start + rel]
            level = rom[entry_start + rel - 1]
            if level == 0 and species == 0:
                continue
            assert species not in legendary_set


def test_gen2_randomization_excludes_legendaries():
    rom = build_gen2_test_rom()
    options = RandomizationOptions(seed=456, allow_legendaries=False)
    randomizer = Gen2Randomizer(random.Random(options.seed), options)
    randomizer.randomize_wild_pokemon(rom)

    legendary_set = set(randomizer.legendary_species)
    for bank, table in zip((1, 2, 3, 4), Gen2Randomizer.WILD_TABLES):
        data_offset = bank * BANK_SIZE + table.pointer_count * 2
        for entry_index in range(table.pointer_count):
            entry_start = data_offset + entry_index * table.entry.length
            for rel in table.entry.species_offsets:
                species = rom[entry_start + rel]
                level = rom[entry_start + rel - 1]
                if level == 0 and species == 0:
                    continue
                assert species not in legendary_set
