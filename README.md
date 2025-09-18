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
2. Click Build1.bat, allow time to run
3. .exe will be in /dist folder

To verify the packaged app, launch the executable, select a clean Generation I
or II ROM, choose an output path for the randomized file, and click **Randomize**.
The status bar should report success once the ROM has been processed. You can
confirm the end-to-end flow by opening the randomized ROM in your preferred
emulator and observing the new encounter tables.

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
