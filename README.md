# Pokémon Game Boy Randomizer

This repository contains a small Python project that shuffles the wild Pokémon you
encounter in the Generation I and II Game Boy and Game Boy Color games (Red,
Blue, Yellow, Gold, Silver and Crystal). The tool edits an existing ROM file and
writes the randomized version to a new location.

⚠️ **ROM files are not distributed with this project.** You must provide your
own legal backups of the games you wish to randomize.

## Features

* Detects whether a supplied ROM is from Generation I or Generation II.
* Randomizes grass and water encounters for both generations.
* Optional seed parameter so results can be reproduced.
* Optionally keep legendary Pokémon out of the encounter tables (default).

## Getting started

1. Ensure you have Python 3.10 or newer available.
2. Install the package in editable mode (use a virtual environment if desired):

   ```bash
   pip install -e .
   ```

3. Run the command line interface. You must provide the path to your clean
   ROM and the path for the randomized result:

   ```bash
   pokemon-randomizer /path/to/PokemonRed.gbc randomized-red.gbc
   ```

   Use the same command with Generation II ROMs; the tool will automatically
   detect the generation.

### Launching the graphical interface

Prefer a windowed experience? Install the project and run:

```bash
pokemon-randomizer-gui
```

The GUI includes browse buttons for the ROM you want to randomize and the
location where the modified ROM should be written. You can optionally supply a
seed, toggle legendary encounters, or disable wild encounter randomization.
Status messages appear at the bottom of the window so you immediately know when
the process succeeds or if the provided paths need attention.

### Useful command line flags

* `--seed 12345` – specify a seed for reproducible results. Any string or
  integer is accepted.
* `--allow-legendaries` – allow legendary Pokémon to appear in the wild.
* `--no-wild` – skip the wild encounter randomization (useful if you only want
  to test detection or generate a copy).

## Development and testing

After installing the package in editable mode you can run the unit tests with:

```bash
pytest
```

The tests use synthetic ROM data to exercise the detection code; no actual game
files are required.
