"""Graphical interface for the Pokémon randomizer."""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from .core import randomize_rom
from .options import build_options, parse_optional_int, resolve_paths, summarize_features


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
    randomize_trainers_var = tk.BooleanVar()
    trainer_type_theme_var = tk.StringVar(value="off")
    randomize_starters_var = tk.BooleanVar()
    randomize_static_var = tk.BooleanVar()
    randomize_items_var = tk.BooleanVar()
    safeguard_items_var = tk.BooleanVar(value=True)
    randomize_movesets_var = tk.BooleanVar()
    randomize_typings_var = tk.BooleanVar()
    randomize_evolutions_var = tk.BooleanVar()
    evolution_consistency_var = tk.BooleanVar()
    randomize_tmhm_var = tk.BooleanVar()
    randomize_stats_var = tk.BooleanVar()
    min_bst_var = tk.StringVar()
    max_bst_var = tk.StringVar()
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

    options_frame = ttk.LabelFrame(mainframe, text="Additional randomization features")
    options_frame.grid(column=0, row=5, columnspan=3, sticky="ew")
    options_frame.columnconfigure(0, weight=1)
    options_frame.columnconfigure(1, weight=1)
    options_frame.columnconfigure(2, weight=1)

    ttk.Checkbutton(
        options_frame,
        text="Randomize trainer parties",
        variable=randomize_trainers_var,
    ).grid(column=0, row=0, sticky="w")
    ttk.Label(options_frame, text="Trainer type theme:").grid(column=1, row=0, sticky="e")
    trainer_theme_combo = ttk.Combobox(
        options_frame,
        textvariable=trainer_type_theme_var,
        values=("off", "monotype"),
        state="readonly",
        width=12,
    )
    trainer_theme_combo.grid(column=2, row=0, sticky="w")
    trainer_theme_combo.current(0)

    ttk.Checkbutton(
        options_frame,
        text="Randomize starters",
        variable=randomize_starters_var,
    ).grid(column=0, row=1, sticky="w")
    ttk.Checkbutton(
        options_frame,
        text="Randomize static encounters",
        variable=randomize_static_var,
    ).grid(column=1, row=1, columnspan=2, sticky="w")

    ttk.Checkbutton(
        options_frame,
        text="Randomize items and shops",
        variable=randomize_items_var,
    ).grid(column=0, row=2, sticky="w")
    ttk.Checkbutton(
        options_frame,
        text="Keep progression items safe",
        variable=safeguard_items_var,
    ).grid(column=1, row=2, columnspan=2, sticky="w")

    ttk.Checkbutton(
        options_frame,
        text="Randomize movesets",
        variable=randomize_movesets_var,
    ).grid(column=0, row=3, sticky="w")
    ttk.Checkbutton(
        options_frame,
        text="Randomize typings",
        variable=randomize_typings_var,
    ).grid(column=1, row=3, columnspan=2, sticky="w")

    ttk.Checkbutton(
        options_frame,
        text="Randomize evolutions",
        variable=randomize_evolutions_var,
    ).grid(column=0, row=4, sticky="w")
    ttk.Checkbutton(
        options_frame,
        text="Preserve evolution difficulty",
        variable=evolution_consistency_var,
    ).grid(column=1, row=4, columnspan=2, sticky="w")

    ttk.Checkbutton(
        options_frame,
        text="Randomize TM/HM compatibility",
        variable=randomize_tmhm_var,
    ).grid(column=0, row=5, sticky="w")
    ttk.Checkbutton(
        options_frame,
        text="Randomize base stats",
        variable=randomize_stats_var,
    ).grid(column=1, row=5, columnspan=2, sticky="w")

    ttk.Label(options_frame, text="BST filter (min / max):").grid(column=0, row=6, sticky="w")
    min_bst_entry = ttk.Entry(options_frame, textvariable=min_bst_var, width=8)
    min_bst_entry.grid(column=1, row=6, sticky="w")
    max_bst_entry = ttk.Entry(options_frame, textvariable=max_bst_var, width=8)
    max_bst_entry.grid(column=2, row=6, sticky="w")

    for child in options_frame.winfo_children():
        child.grid_configure(padx=4, pady=2)

    status_label = ttk.Label(mainframe, textvariable=status_var, style="Status.TLabel", wraplength=420)
    status_label.grid(column=0, row=7, columnspan=3, sticky="ew")

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

        try:
            min_bst = parse_optional_int(min_bst_var.get())
            max_bst = parse_optional_int(max_bst_var.get())
        except ValueError:
            set_status("BST filters must be whole numbers.", error=True)
            return

        try:
            options = build_options(
                seed=seed_var.get(),
                allow_legendaries=allow_legendaries_var.get(),
                disable_wild=disable_wild_var.get(),
                randomize_trainers=randomize_trainers_var.get(),
                trainer_type_theme=trainer_type_theme_var.get(),
                randomize_starters=randomize_starters_var.get(),
                randomize_static=randomize_static_var.get(),
                randomize_items=randomize_items_var.get(),
                safeguard_progression_items=safeguard_items_var.get(),
                randomize_movesets=randomize_movesets_var.get(),
                randomize_typings=randomize_typings_var.get(),
                randomize_evolutions=randomize_evolutions_var.get(),
                evolution_consistency=evolution_consistency_var.get(),
                randomize_tm_compatibility=randomize_tmhm_var.get(),
                randomize_base_stats=randomize_stats_var.get(),
                min_bst=min_bst,
                max_bst=max_bst,
            )
        except ValueError as exc:
            set_status(str(exc), error=True)
            return
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
            feature_summary = summarize_features(options)
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
    randomize_button.grid(column=1, row=6, sticky="e")

    for child in mainframe.winfo_children():
        child.grid_configure(padx=4, pady=4)

    rom_entry.focus_set()
    root.bind("<Return>", run_randomization)

    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - manual execution entry point
    main()
