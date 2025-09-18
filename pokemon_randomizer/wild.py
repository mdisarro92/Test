"""Utility helpers for detecting and randomizing wild encounter tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

BANK_SIZE = 0x4000


def read_u16le(data: Sequence[int], offset: int) -> int:
    return data[offset] | (data[offset + 1] << 8)


def bank_offset(bank: int, address: int) -> int:
    if bank == 0:
        return address
    return bank * BANK_SIZE + (address - 0x4000)


@dataclass(frozen=True)
class WildEntryDefinition:
    """Describes the layout of a single wild-encounter entry."""

    length: int
    species_offsets: tuple[int, ...]
    min_level: int = 1
    max_level: int = 100

    def validate(self, rom: Sequence[int], offset: int, max_species: int) -> bool:
        if offset < 0 or offset + self.length > len(rom):
            return False
        for species_rel in self.species_offsets:
            species_pos = offset + species_rel
            level_pos = species_pos - 1
            species = rom[species_pos]
            level = rom[level_pos]
            if level == 0 and species == 0:
                continue
            if not (self.min_level <= level <= self.max_level):
                return False
            if not (1 <= species <= max_species):
                return False
        return True

    def iter_species_positions(self, offset: int) -> Iterable[int]:
        for species_rel in self.species_offsets:
            yield offset + species_rel


@dataclass(frozen=True)
class WildTableDefinition:
    name: str
    pointer_count: int
    entry: WildEntryDefinition


@dataclass
class WildTable:
    definition: WildTableDefinition
    bank: int
    pointer_offset: int
    entry_offsets: list[int]

    def species_positions(self) -> Iterable[int]:
        for entry_offset in self.entry_offsets:
            yield from self.definition.entry.iter_species_positions(entry_offset)


class WildTableNotFoundError(RuntimeError):
    pass


def find_wild_table(
    rom: Sequence[int],
    definition: WildTableDefinition,
    max_species: int,
    *,
    used_entries: set[int] | None = None,
) -> WildTable:
    table_bytes = definition.pointer_count * 2
    rom_length = len(rom)
    banks = rom_length // BANK_SIZE

    for bank in range(1, banks):
        bank_start = bank * BANK_SIZE
        bank_end = min(bank_start + BANK_SIZE, rom_length)
        for offset in range(bank_start, bank_end - table_bytes):
            ok = True
            entries: list[int] = []
            for index in range(definition.pointer_count):
                pointer = read_u16le(rom, offset + index * 2)
                if pointer < 0x4000 or pointer >= 0x8000:
                    ok = False
                    break
                entry_offset = bank_offset(bank, pointer)
                if used_entries and entry_offset in used_entries:
                    ok = False
                    break
                if not definition.entry.validate(rom, entry_offset, max_species):
                    ok = False
                    break
                entries.append(entry_offset)
            if ok:
                next_ptr_offset = offset + definition.pointer_count * 2
                if next_ptr_offset + 1 < bank_end:
                    next_pointer = read_u16le(rom, next_ptr_offset)
                    if 0x4000 <= next_pointer < 0x8000:
                        next_entry_offset = bank_offset(bank, next_pointer)
                        if definition.entry.validate(rom, next_entry_offset, max_species):
                            continue
                return WildTable(definition, bank, offset, entries)
    raise WildTableNotFoundError(f"Could not locate {definition.name} pointer table")


def randomize_table(table: WildTable, rom: bytearray, species_pool: Sequence[int], rng) -> None:
    for entry_offset in table.entry_offsets:
        for species_pos in table.definition.entry.iter_species_positions(entry_offset):
            level = rom[species_pos - 1]
            species = rom[species_pos]
            if level == 0 and species == 0:
                continue
            rom[species_pos] = rng.choice(species_pool)
