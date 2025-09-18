import random
from itertools import cycle
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pokemon_randomizer.core import RandomizationOptions
from pokemon_randomizer.gen1 import Gen1Randomizer
from pokemon_randomizer.gen2 import Gen2Randomizer
from pokemon_randomizer.options import build_options, summarize_features
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

    # Trainer parties
    trainer_offset = Gen1Randomizer.TRAINER_TABLE_OFFSET
    trainer_count = 2
    rom[trainer_offset] = trainer_count
    trainer_pos = trainer_offset + 1
    base_species = [1, 4, 7, 10, 12, 15]
    for index in range(trainer_count * Gen1Randomizer.TRAINER_PARTY_SIZE):
        rom[trainer_pos + index] = base_species[index % len(base_species)]

    # Starters
    starters = [1, 4, 7]
    for index, species in enumerate(starters):
        rom[Gen1Randomizer.STARTER_OFFSET + index] = species

    # Static encounters
    static_species = [25, 35, 63, 129]
    static_offset = Gen1Randomizer.STATIC_TABLE_OFFSET
    rom[static_offset] = len(static_species)
    for index, species in enumerate(static_species):
        rom[static_offset + 1 + index] = species

    # Shop inventories
    shops = [
        [1, 5, 10, 20],
        [2, 6, 11, 21],
    ]
    shop_offset = Gen1Randomizer.SHOP_TABLE_OFFSET
    rom[shop_offset] = len(shops)
    shop_pos = shop_offset + 1
    for shop in shops:
        for item in shop:
            rom[shop_pos] = item
            shop_pos += 1

    # Level-up movesets
    movesets = [
        (1, [10, 11, 12, 13]),
        (4, [14, 15, 16, 17]),
        (7, [18, 19, 20, 21]),
    ]
    moveset_offset = Gen1Randomizer.MOVESET_TABLE_OFFSET
    rom[moveset_offset] = len(movesets)
    moveset_pos = moveset_offset + 1
    for species, moves in movesets:
        rom[moveset_pos] = species
        moveset_pos += 1
        for move in moves:
            rom[moveset_pos] = move
            moveset_pos += 1

    # Typing table
    typings = [
        (1, "GRASS", "POISON"),
        (4, "FIRE", None),
        (7, "WATER", None),
        (25, "ELECTRIC", None),
        (63, "PSYCHIC", None),
    ]
    typing_offset = Gen1Randomizer.TYPING_TABLE_OFFSET
    rom[typing_offset] = len(typings)
    typing_pos = typing_offset + 1
    for species, primary, secondary in typings:
        rom[typing_pos] = species
        typing_pos += 1
        rom[typing_pos] = Gen1Randomizer.TYPE_NAME_TO_ID[primary]
        typing_pos += 1
        if secondary is None:
            rom[typing_pos] = Gen1Randomizer.TYPE_NONE
        else:
            rom[typing_pos] = Gen1Randomizer.TYPE_NAME_TO_ID[secondary]
        typing_pos += 1

    # Evolution table
    evolutions = [
        (1, 2),
        (2, 3),
        (4, 5),
        (7, 8),
        (25, 26),
    ]
    evolution_offset = Gen1Randomizer.EVOLUTION_TABLE_OFFSET
    rom[evolution_offset] = len(evolutions)
    evolution_pos = evolution_offset + 1
    for species, target in evolutions:
        rom[evolution_pos] = species
        rom[evolution_pos + 1] = target
        evolution_pos += 2

    # TM/HM compatibility table
    tmhm_entries = [
        (1, 0b00001111),
        (4, 0b00110011),
        (7, 0b01010101),
    ]
    tmhm_offset = Gen1Randomizer.TMHM_TABLE_OFFSET
    rom[tmhm_offset] = len(tmhm_entries)
    tmhm_pos = tmhm_offset + 1
    for species, mask in tmhm_entries:
        rom[tmhm_pos] = species
        tmhm_pos += 1
        rom[tmhm_pos] = mask
        tmhm_pos += 1

    # Base stat table
    base_stats = [
        (1, [45, 49, 49, 45, 65, 65]),
        (4, [39, 52, 43, 65, 60, 50]),
        (7, [44, 48, 65, 43, 50, 64]),
        (25, [35, 55, 40, 90, 50, 50]),
    ]
    stats_offset = Gen1Randomizer.BASE_STATS_TABLE_OFFSET
    rom[stats_offset] = len(base_stats)
    stats_pos = stats_offset + 1
    for species, stats in base_stats:
        rom[stats_pos] = species
        stats_pos += 1
        for value in stats:
            rom[stats_pos] = value
            stats_pos += 1
    return rom


def read_trainer_parties(rom: bytearray, randomizer_cls) -> list[list[int]]:
    offset = randomizer_cls.TRAINER_TABLE_OFFSET
    count = rom[offset]
    parties: list[list[int]] = []
    pos = offset + 1
    for _ in range(count):
        party = []
        for _ in range(randomizer_cls.TRAINER_PARTY_SIZE):
            party.append(rom[pos])
            pos += 1
        parties.append(party)
    return parties


def read_starters(rom: bytearray, randomizer_cls) -> list[int]:
    return [rom[randomizer_cls.STARTER_OFFSET + index] for index in range(randomizer_cls.STARTER_COUNT)]


def read_static_encounters(rom: bytearray, randomizer_cls) -> list[int]:
    offset = randomizer_cls.STATIC_TABLE_OFFSET
    count = rom[offset]
    return [rom[offset + 1 + index] for index in range(count)]


def read_shop_items(rom: bytearray, randomizer_cls) -> list[list[int]]:
    offset = randomizer_cls.SHOP_TABLE_OFFSET
    count = rom[offset]
    shops: list[list[int]] = []
    pos = offset + 1
    for _ in range(count):
        shop = []
        for _ in range(randomizer_cls.SHOP_ITEM_COUNT):
            shop.append(rom[pos])
            pos += 1
        shops.append(shop)
    return shops


def read_movesets(rom: bytearray, randomizer_cls) -> list[tuple[int, list[int]]]:
    offset = randomizer_cls.MOVESET_TABLE_OFFSET
    count = rom[offset]
    entries: list[tuple[int, list[int]]] = []
    pos = offset + 1
    for _ in range(count):
        species = rom[pos]
        pos += 1
        moves = [rom[pos + index] for index in range(randomizer_cls.MOVES_PER_SPECIES)]
        pos += randomizer_cls.MOVES_PER_SPECIES
        entries.append((species, moves))
    return entries


def read_typings(rom: bytearray, randomizer_cls) -> list[tuple[int, int, int]]:
    offset = randomizer_cls.TYPING_TABLE_OFFSET
    count = rom[offset]
    entries: list[tuple[int, int, int]] = []
    pos = offset + 1
    for _ in range(count):
        species = rom[pos]
        type1 = rom[pos + 1]
        type2 = rom[pos + 2]
        pos += 3
        entries.append((species, type1, type2))
    return entries


def read_evolutions(rom: bytearray, randomizer_cls) -> list[tuple[int, int]]:
    offset = randomizer_cls.EVOLUTION_TABLE_OFFSET
    count = rom[offset]
    entries: list[tuple[int, int]] = []
    pos = offset + 1
    for _ in range(count):
        species = rom[pos]
        target = rom[pos + 1]
        pos += 2
        entries.append((species, target))
    return entries


def read_tmhm_masks(rom: bytearray, randomizer_cls) -> list[tuple[int, int]]:
    offset = randomizer_cls.TMHM_TABLE_OFFSET
    count = rom[offset]
    entries: list[tuple[int, int]] = []
    pos = offset + 1
    for _ in range(count):
        species = rom[pos]
        mask = rom[pos + 1]
        pos += 2
        entries.append((species, mask))
    return entries


def read_base_stats(rom: bytearray, randomizer_cls) -> list[tuple[int, list[int]]]:
    offset = randomizer_cls.BASE_STATS_TABLE_OFFSET
    count = rom[offset]
    entries: list[tuple[int, list[int]]] = []
    pos = offset + 1
    for _ in range(count):
        species = rom[pos]
        pos += 1
        stats = [rom[pos + index] for index in range(6)]
        pos += 6
        entries.append((species, stats))
    return entries


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

    # Trainer parties
    trainer_offset = Gen2Randomizer.TRAINER_TABLE_OFFSET
    trainer_count = 2
    rom[trainer_offset] = trainer_count
    trainer_pos = trainer_offset + 1
    trainer_species = [152, 153, 154, 155, 156, 157, 158, 159]
    for index in range(trainer_count * Gen2Randomizer.TRAINER_PARTY_SIZE):
        rom[trainer_pos + index] = trainer_species[index % len(trainer_species)]

    # Starters
    starters = [152, 155, 158]
    for index, species in enumerate(starters):
        rom[Gen2Randomizer.STARTER_OFFSET + index] = species

    # Static encounters
    static_species = [172, 179, 246, 247]
    static_offset = Gen2Randomizer.STATIC_TABLE_OFFSET
    rom[static_offset] = len(static_species)
    for index, species in enumerate(static_species):
        rom[static_offset + 1 + index] = species

    # Shop inventories
    shops = [
        [1, 30, 40, 50, 60],
        [2, 35, 45, 55, 65],
        [3, 70, 80, 90, 100],
    ]
    shop_offset = Gen2Randomizer.SHOP_TABLE_OFFSET
    rom[shop_offset] = len(shops)
    shop_pos = shop_offset + 1
    for shop in shops:
        for item in shop:
            rom[shop_pos] = item
            shop_pos += 1

    # Level-up movesets
    movesets = [
        (152, [33, 45, 75, 22, 73]),
        (155, [10, 52, 83, 98, 28]),
        (158, [55, 44, 61, 30, 99]),
    ]
    moveset_offset = Gen2Randomizer.MOVESET_TABLE_OFFSET
    rom[moveset_offset] = len(movesets)
    moveset_pos = moveset_offset + 1
    for species, moves in movesets:
        rom[moveset_pos] = species
        moveset_pos += 1
        for move in moves:
            rom[moveset_pos] = move
            moveset_pos += 1

    # Typing table
    typings = [
        (152, "GRASS", None),
        (155, "FIRE", None),
        (158, "WATER", None),
        (172, "ELECTRIC", None),
        (246, "ROCK", "GROUND"),
    ]
    typing_offset = Gen2Randomizer.TYPING_TABLE_OFFSET
    rom[typing_offset] = len(typings)
    typing_pos = typing_offset + 1
    for species, primary, secondary in typings:
        rom[typing_pos] = species
        typing_pos += 1
        rom[typing_pos] = Gen2Randomizer.TYPE_NAME_TO_ID[primary]
        typing_pos += 1
        if secondary is None:
            rom[typing_pos] = Gen2Randomizer.TYPE_NONE
        else:
            rom[typing_pos] = Gen2Randomizer.TYPE_NAME_TO_ID[secondary]
        typing_pos += 1

    # Evolution table
    evolutions = [
        (152, 153),
        (153, 154),
        (155, 156),
        (156, 157),
        (158, 159),
    ]
    evolution_offset = Gen2Randomizer.EVOLUTION_TABLE_OFFSET
    rom[evolution_offset] = len(evolutions)
    evolution_pos = evolution_offset + 1
    for species, target in evolutions:
        rom[evolution_pos] = species
        rom[evolution_pos + 1] = target
        evolution_pos += 2

    # TM/HM compatibility
    tmhm_entries = [
        (152, 0b11110000),
        (155, 0b00111100),
        (158, 0b00001111),
        (172, 0b01010101),
    ]
    tmhm_offset = Gen2Randomizer.TMHM_TABLE_OFFSET
    rom[tmhm_offset] = len(tmhm_entries)
    tmhm_pos = tmhm_offset + 1
    for species, mask in tmhm_entries:
        rom[tmhm_pos] = species
        tmhm_pos += 1
        rom[tmhm_pos] = mask
        tmhm_pos += 1

    # Base stats
    base_stats = [
        (152, [45, 49, 65, 45, 49, 65]),
        (155, [39, 52, 43, 65, 60, 50]),
        (158, [50, 65, 64, 43, 50, 64]),
        (172, [90, 75, 85, 55, 90, 75]),
    ]
    stats_offset = Gen2Randomizer.BASE_STATS_TABLE_OFFSET
    rom[stats_offset] = len(base_stats)
    stats_pos = stats_offset + 1
    for species, stats in base_stats:
        rom[stats_pos] = species
        stats_pos += 1
        for value in stats:
            rom[stats_pos] = value
            stats_pos += 1
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


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_trainer_randomization_applies_theme_and_bst(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(seed=789, randomize_trainers=True, trainer_type_theme="monotype")
    randomizer = randomizer_cls(random.Random(options.seed), options)
    sorted_species = sorted(range(1, randomizer.max_species + 1), key=randomizer.get_species_bst)
    options.min_bst = randomizer.get_species_bst(sorted_species[-10])
    pool = set(randomizer.build_species_pool())
    randomizer.randomize_trainer_parties(rom)
    parties = read_trainer_parties(rom, randomizer_cls)
    assert parties
    for party in parties:
        assert len(party) == randomizer_cls.TRAINER_PARTY_SIZE
        for species in party:
            assert species in pool
        common_types = set(randomizer.get_species_types(party[0]))
        for species in party[1:]:
            common_types &= set(randomizer.get_species_types(species))
        assert common_types


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_starters_and_static_use_species_pool(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(seed=321, randomize_starters=True, randomize_static=True)
    randomizer = randomizer_cls(random.Random(options.seed), options)
    pool = set(randomizer.build_species_pool())
    randomizer.randomize_starters(rom)
    randomizer.randomize_static_encounters(rom)
    starters = read_starters(rom, randomizer_cls)
    static_species = read_static_encounters(rom, randomizer_cls)
    for species in starters + static_species:
        assert species in pool


def test_item_randomization_respects_progression_safeguards():
    rom = build_gen1_test_rom()
    options = RandomizationOptions(seed=135, randomize_items=True)
    randomizer = Gen1Randomizer(random.Random(options.seed), options)
    original_shops = read_shop_items(rom, Gen1Randomizer)
    progression_items = set(randomizer.PROGRESSION_ITEMS)
    randomizer.randomize_items_and_shops(rom)
    safeguarded = read_shop_items(rom, Gen1Randomizer)
    for before, after in zip(original_shops, safeguarded):
        for old, new in zip(before, after):
            if old in progression_items:
                assert new == old

    options.safeguard_progression_items = False
    rom = build_gen1_test_rom()
    randomizer = Gen1Randomizer(random.Random(options.seed), options)
    randomizer.randomize_items_and_shops(rom)
    unguarded = read_shop_items(rom, Gen1Randomizer)
    assert any(
        old in progression_items and new != old
        for before, after in zip(original_shops, unguarded)
        for old, new in zip(before, after)
    )


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_moveset_randomization_changes_moves(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(seed=246, randomize_movesets=True)
    randomizer = randomizer_cls(random.Random(options.seed), options)
    original = read_movesets(rom, randomizer_cls)
    randomizer.randomize_movesets(rom)
    updated = read_movesets(rom, randomizer_cls)
    assert updated != original
    for _, moves in updated:
        assert len(moves) == randomizer_cls.MOVES_PER_SPECIES
        assert len(set(moves)) == len(moves)
        for move in moves:
            assert 1 <= move <= 250


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_typing_randomization_updates_cache(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(seed=975, randomize_typings=True)
    randomizer = randomizer_cls(random.Random(options.seed), options)
    original = read_typings(rom, randomizer_cls)
    randomizer.randomize_typings(rom)
    updated = read_typings(rom, randomizer_cls)
    assert updated != original
    for species, type1_id, type2_id in updated:
        expected: list[str] = []
        primary_name = randomizer.type_id_to_name(type1_id)
        if primary_name is not None:
            expected.append(primary_name)
        secondary_name = randomizer.type_id_to_name(type2_id)
        if secondary_name is not None and secondary_name != primary_name:
            expected.append(secondary_name)
        assert tuple(expected) == randomizer.get_species_types(species)


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_evolution_randomization_respects_consistency(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(
        seed=864,
        randomize_evolutions=True,
        evolution_consistency=True,
    )
    randomizer = randomizer_cls(random.Random(options.seed), options)
    original = read_evolutions(rom, randomizer_cls)
    randomizer.randomize_evolutions(rom)
    updated = read_evolutions(rom, randomizer_cls)
    original_map = dict(original)
    changed = False
    for species, target in updated:
        if target == 0:
            continue
        if original_map.get(species) == target:
            continue
        changed = True
        assert randomizer.get_species_bst(target) >= randomizer.get_species_bst(species)
    assert changed


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_tmhm_randomization_is_deterministic(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(seed=531, randomize_tm_compatibility=True)
    randomizer = randomizer_cls(random.Random(options.seed), options)
    count = rom[randomizer_cls.TMHM_TABLE_OFFSET]
    expected_rng = random.Random(options.seed)
    expected_masks = [expected_rng.randint(1, 255) for _ in range(count)]
    randomizer.randomize_tm_hm_compatibility(rom)
    updated_masks = [mask for _, mask in read_tmhm_masks(rom, randomizer_cls)]
    assert updated_masks == expected_masks


@pytest.mark.parametrize(
    ("randomizer_cls", "build_rom"),
    [
        (Gen1Randomizer, build_gen1_test_rom),
        (Gen2Randomizer, build_gen2_test_rom),
    ],
)
def test_base_stats_randomization_preserves_totals(randomizer_cls, build_rom):
    rom = build_rom()
    options = RandomizationOptions(seed=2468, randomize_base_stats=True)
    randomizer = randomizer_cls(random.Random(options.seed), options)
    original_stats = read_base_stats(rom, randomizer_cls)
    original_totals = {species: sum(stats) for species, stats in original_stats}
    randomizer.randomize_base_stats(rom)
    updated_stats = read_base_stats(rom, randomizer_cls)
    updated_totals = {species: sum(stats) for species, stats in updated_stats}
    assert original_totals == updated_totals
    assert any(
        original_stats[index][1] != updated_stats[index][1]
        for index in range(len(original_stats))
    )


def test_build_options_handles_extended_flags():
    options = build_options(
        seed="99",
        allow_legendaries=True,
        disable_wild=True,
        randomize_trainers=True,
        trainer_type_theme="monotype",
        randomize_starters=True,
        randomize_static=True,
        randomize_items=True,
        safeguard_progression_items=False,
        randomize_movesets=True,
        randomize_typings=True,
        randomize_evolutions=True,
        evolution_consistency=True,
        randomize_tm_compatibility=True,
        randomize_base_stats=True,
        min_bst=400,
        max_bst=600,
    )
    assert not options.randomize_wild
    assert options.randomize_trainers
    assert options.trainer_type_theme == "monotype"
    assert options.randomize_items
    assert not options.safeguard_progression_items
    assert options.min_bst == 400
    assert options.max_bst == 600


def test_summarize_features_lists_enabled_modes():
    options = RandomizationOptions(
        randomize_wild=True,
        randomize_trainers=True,
        randomize_tm_compatibility=True,
    )
    summary = summarize_features(options)
    assert "wild encounters" in summary
    assert "trainer parties" in summary
    assert "TM/HM compatibility" in summary
