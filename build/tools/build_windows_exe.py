"""Helper for building the Windows GUI executable with PyInstaller."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    spec_path = Path(__file__).resolve().with_name("pokemon_randomizer_gui.spec")

    command = [sys.executable, "-m", "PyInstaller", str(spec_path)]

    print("Running:", " ".join(command))
    subprocess.run(command, check=True, cwd=repo_root)

    dist_dir = repo_root / "dist" / "PokemonRandomizerGui"
    exe_path = dist_dir / "PokemonRandomizerGui.exe"
    print(f"\nBuild complete. Check {exe_path} for the generated executable.")


if __name__ == "__main__":
    main()
