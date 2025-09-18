"""Graphical interface for the Pokémon randomizer."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from .core import randomize_rom
from .options import build_options, resolve_paths


def main() -> None:
    """Launch the graphical interface."""

    root = tk.Tk()
    root.title("Pokémon Randomizer")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.configure("Status.TLabel", foreground=style.lookup("TLabel", "foreground"))
    style.configure("Error.TLabel", foreground="#b00020")
    style.configure("Success.TLabel", foreground="#006400")

    rom_var = tk.StringVar()
    output_var = tk.StringVar()
    seed_var = tk.StringVar()
    allow_legendaries_var = tk.BooleanVar()
    disable_wild_var = tk.BooleanVar()
    status_var = tk.StringVar()

    mainframe = ttk.Frame(root, padding="12 12 12 12")
    mainframe.grid(column=0, row=0, sticky="nsew")
    mainframe.columnconfigure(1, weight=1)

    ttk.Label(mainframe, text="ROM path:").grid(column=0, row=0, sticky="w")
    rom_entry = ttk.Entry(mainframe, textvariable=rom_var, width=45)
    rom_entry.grid(column=1, row=0, sticky="ew")

    def choose_rom() -> None:
        filename = filedialog.askopenfilename(
            title="Select a Pokémon ROM",
            filetypes=[
                ("Game Boy / Game Boy Color ROMs", "*.gb *.gbc *.gbx"),
                ("All files", "*.*"),
            ],
        )
        if filename:
            rom_var.set(filename)

    ttk.Button(mainframe, text="Browse…", command=choose_rom).grid(column=2, row=0, sticky="ew")

    ttk.Label(mainframe, text="Output path:").grid(column=0, row=1, sticky="w")
    output_entry = ttk.Entry(mainframe, textvariable=output_var, width=45)
    output_entry.grid(column=1, row=1, sticky="ew")

    def choose_output() -> None:
        initialfile = ""
        rom_value = rom_var.get()
        if rom_value:
            initialfile = rom_value
        filename = filedialog.asksaveasfilename(
            title="Save randomized ROM",
            defaultextension=".gbc",
            filetypes=[
                ("Game Boy / Game Boy Color ROMs", "*.gb *.gbc *.gbx"),
                ("All files", "*.*"),
            ],
            initialfile=initialfile,
        )
        if filename:
            output_var.set(filename)

    ttk.Button(mainframe, text="Browse…", command=choose_output).grid(column=2, row=1, sticky="ew")

    ttk.Label(mainframe, text="Seed (optional):").grid(column=0, row=2, sticky="w")
    seed_entry = ttk.Entry(mainframe, textvariable=seed_var, width=45)
    seed_entry.grid(column=1, row=2, sticky="ew")

    allow_legendaries_check = ttk.Checkbutton(
        mainframe,
        text="Allow legendaries",
        variable=allow_legendaries_var,
    )
    allow_legendaries_check.grid(column=1, row=3, sticky="w")

    disable_wild_check = ttk.Checkbutton(
        mainframe,
        text="Disable wild encounters",
        variable=disable_wild_var,
    )
    disable_wild_check.grid(column=1, row=4, sticky="w")

    status_label = ttk.Label(mainframe, textvariable=status_var, style="Status.TLabel", wraplength=420)
    status_label.grid(column=0, row=6, columnspan=3, sticky="ew")

    def set_status(message: str, *, error: bool = False) -> None:
        status_var.set(message)
        if not message:
            status_label.configure(style="Status.TLabel")
        elif error:
            status_label.configure(style="Error.TLabel")
        else:
            status_label.configure(style="Success.TLabel")

    def run_randomization(event: object | None = None) -> None:
        set_status("")
        rom_value = rom_var.get().strip()
        output_value = output_var.get().strip()

        if not rom_value:
            set_status("Please choose a ROM file to randomize.", error=True)
            rom_entry.focus_set()
            return
        if not output_value:
            set_status("Please choose where to save the randomized ROM.", error=True)
            output_entry.focus_set()
            return

        options = build_options(
            seed=seed_var.get(),
            allow_legendaries=allow_legendaries_var.get(),
            disable_wild=disable_wild_var.get(),
        )
        rom_path, output_path = resolve_paths(rom_value, output_value)

        try:
            info = randomize_rom(rom_path, output_path, options)
        except FileNotFoundError as exc:
            set_status(str(exc), error=True)
        except ValueError as exc:
            set_status(str(exc), error=True)
        except Exception as exc:  # pragma: no cover - safety net for GUI usage
            set_status(f"Unexpected error: {exc}", error=True)
        else:
            feature_summary = "wild encounters" if options.randomize_wild else "no features"
            seed_display = str(options.seed) if options.seed is not None else "None"
            set_status(
                "Randomized {title} (Generation {generation}) with seed {seed}. Modified features: {features}.".format(
                    title=info.title,
                    generation=info.generation,
                    seed=seed_display,
                    features=feature_summary,
                ),
                error=False,
            )

    randomize_button = ttk.Button(mainframe, text="Randomize", command=run_randomization)
    randomize_button.grid(column=1, row=5, sticky="e")

    for child in mainframe.winfo_children():
        child.grid_configure(padx=4, pady=4)

    rom_entry.focus_set()
    root.bind("<Return>", run_randomization)

    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()
