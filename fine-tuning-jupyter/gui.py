"""Tkinter GUI for CP Speech STT Evaluation."""

import json
import os
import platform
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# Paths relative to this script
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data" / "raw"
TRANSCRIPTS_FILE = BASE_DIR / "transcripts" / "ground_truth.json"
RESULTS_DIR = BASE_DIR / "results"
ENV_FILE = BASE_DIR / ".env"

# Provider registry (duplicated from providers/__init__ to avoid importing it
# at module level, which could trigger heavy imports)
PROVIDER_KEYS = {
    "whisper_local": [],
    "openai_whisper": ["OPENAI_API_KEY"],
    "assemblyai": ["ASSEMBLYAI_API_KEY"],
    "deepgram": ["DEEPGRAM_API_KEY"],
    "google_stt": ["GOOGLE_APPLICATION_CREDENTIALS"],
    "gpt4o_audio": ["OPENAI_API_KEY"],
    "gemini_audio": ["GEMINI_API_KEY"],
}

# Unique env var names for the Setup tab
ENV_VARS = [
    "OPENAI_API_KEY",
    "ASSEMBLYAI_API_KEY",
    "DEEPGRAM_API_KEY",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "GEMINI_API_KEY",
]


def _load_env_file() -> dict[str, str]:
    """Parse .env file into a dict. Returns empty dict if missing."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            env[key.strip()] = val.strip().strip("\"'")
    return env


def _save_env_file(env: dict[str, str]):
    """Write env vars to .env file."""
    lines = []
    for key, val in env.items():
        if val:
            lines.append(f"{key}={val}")
    ENV_FILE.write_text("\n".join(lines) + "\n")


def _open_file(path: Path):
    """Open a file with the system default viewer."""
    if platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
    elif platform.system() == "Windows":
        os.startfile(str(path))
    else:
        subprocess.Popen(["xdg-open", str(path)])


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CP Speech STT Evaluation")
        self.geometry("900x650")
        self.minsize(800, 550)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_setup_tab()
        self._build_run_tab()
        self._build_results_tab()

        self._running = False

    # ------------------------------------------------------------------ #
    #  Tab 1 — Setup                                                      #
    # ------------------------------------------------------------------ #
    def _build_setup_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Setup")

        # --- API Keys ---
        key_frame = ttk.LabelFrame(tab, text="API Keys", padding=8)
        key_frame.pack(fill="x", padx=8, pady=(8, 4))

        env = _load_env_file()
        self.key_entries: dict[str, tk.Entry] = {}
        self._key_show_vars: dict[str, tk.BooleanVar] = {}

        for i, var_name in enumerate(ENV_VARS):
            ttk.Label(key_frame, text=var_name).grid(
                row=i, column=0, sticky="w", padx=(0, 8), pady=2
            )
            entry = ttk.Entry(key_frame, width=50, show="*")
            entry.grid(row=i, column=1, sticky="ew", pady=2)
            entry.insert(0, env.get(var_name, ""))
            self.key_entries[var_name] = entry

            show_var = tk.BooleanVar(value=False)
            self._key_show_vars[var_name] = show_var
            cb = ttk.Checkbutton(
                key_frame, text="Show", variable=show_var,
                command=lambda e=entry, v=show_var: e.configure(
                    show="" if v.get() else "*"
                ),
            )
            cb.grid(row=i, column=2, padx=4, pady=2)

        key_frame.columnconfigure(1, weight=1)

        ttk.Button(key_frame, text="Save Keys", command=self._save_keys).grid(
            row=len(ENV_VARS), column=1, sticky="e", pady=(6, 0)
        )

        # --- Audio Files ---
        audio_frame = ttk.LabelFrame(tab, text="Audio Files & Ground Truth", padding=8)
        audio_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        btn_row = ttk.Frame(audio_frame)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Add WAV Files", command=self._add_wav_files).pack(
            side="left"
        )
        ttk.Button(btn_row, text="Remove Selected", command=self._remove_selected).pack(
            side="left", padx=8
        )
        ttk.Button(btn_row, text="Save Ground Truth", command=self._save_ground_truth).pack(
            side="right"
        )

        cols = ("filename", "ground_truth")
        self.audio_tree = ttk.Treeview(audio_frame, columns=cols, show="headings", height=8)
        self.audio_tree.heading("filename", text="Filename")
        self.audio_tree.heading("ground_truth", text="Ground Truth")
        self.audio_tree.column("filename", width=250)
        self.audio_tree.column("ground_truth", width=500)
        self.audio_tree.pack(fill="both", expand=True, pady=(6, 0))

        scrollbar = ttk.Scrollbar(audio_frame, orient="vertical", command=self.audio_tree.yview)
        self.audio_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.place(relx=1.0, rely=0.15, relheight=0.85, anchor="ne")

        self.audio_tree.bind("<Double-1>", self._edit_ground_truth)

        # Load existing ground truth
        self._load_audio_tree()

    def _save_keys(self):
        env = {}
        for var_name, entry in self.key_entries.items():
            val = entry.get().strip()
            if val:
                env[var_name] = val
                os.environ[var_name] = val
        _save_env_file(env)
        messagebox.showinfo("Saved", "API keys saved to .env")

    def _add_wav_files(self):
        paths = filedialog.askopenfilenames(
            title="Select WAV files",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if not paths:
            return
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        for p in paths:
            src = Path(p)
            dest = DATA_DIR / src.name
            if not dest.exists():
                shutil.copy2(src, dest)
            # Add to treeview if not already present
            existing = {self.audio_tree.set(iid, "filename")
                        for iid in self.audio_tree.get_children()}
            if src.name not in existing:
                gt = src.stem.replace("_", " ").replace("-", " ")
                self.audio_tree.insert("", "end", values=(src.name, gt))

    def _remove_selected(self):
        for iid in self.audio_tree.selection():
            self.audio_tree.delete(iid)

    def _save_ground_truth(self):
        gt = {}
        for iid in self.audio_tree.get_children():
            fname = self.audio_tree.set(iid, "filename")
            text = self.audio_tree.set(iid, "ground_truth")
            gt[fname] = text
        TRANSCRIPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRANSCRIPTS_FILE, "w") as f:
            json.dump(gt, f, indent=2)
        messagebox.showinfo("Saved", f"Ground truth saved ({len(gt)} entries)")

    def _load_audio_tree(self):
        gt = {}
        if TRANSCRIPTS_FILE.exists():
            with open(TRANSCRIPTS_FILE) as f:
                gt = json.load(f)
        # Also pick up WAV files in data/raw not in ground truth
        if DATA_DIR.exists():
            for wav in sorted(DATA_DIR.glob("*.wav")):
                if wav.name not in gt:
                    gt[wav.name] = wav.stem.replace("_", " ").replace("-", " ")
        for fname, text in gt.items():
            self.audio_tree.insert("", "end", values=(fname, text))

    def _edit_ground_truth(self, event):
        """Double-click to edit ground truth text in-place."""
        region = self.audio_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.audio_tree.identify_column(event.x)
        if col != "#2":  # Only edit ground_truth column
            return
        iid = self.audio_tree.identify_row(event.y)
        if not iid:
            return

        # Get cell bounding box
        bbox = self.audio_tree.bbox(iid, column="ground_truth")
        if not bbox:
            return
        x, y, w, h = bbox

        current = self.audio_tree.set(iid, "ground_truth")
        entry = tk.Entry(self.audio_tree, width=w // 7)
        entry.insert(0, current)
        entry.select_range(0, "end")
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()

        def _on_confirm(e=None):
            self.audio_tree.set(iid, "ground_truth", entry.get())
            entry.destroy()

        def _on_cancel(e=None):
            entry.destroy()

        entry.bind("<Return>", _on_confirm)
        entry.bind("<Escape>", _on_cancel)
        entry.bind("<FocusOut>", _on_confirm)

    # ------------------------------------------------------------------ #
    #  Tab 2 — Run                                                        #
    # ------------------------------------------------------------------ #
    def _build_run_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Run")

        # Provider checkboxes
        prov_frame = ttk.LabelFrame(tab, text="Providers", padding=8)
        prov_frame.pack(fill="x", padx=8, pady=(8, 4))

        self.provider_vars: dict[str, tk.BooleanVar] = {}
        for i, name in enumerate(PROVIDER_KEYS):
            var = tk.BooleanVar(value=False)
            self.provider_vars[name] = var
            cb = ttk.Checkbutton(prov_frame, text=name, variable=var)
            cb.grid(row=i // 4, column=i % 4, sticky="w", padx=8, pady=2)

        self._update_provider_checkboxes()

        ttk.Button(prov_frame, text="Refresh", command=self._update_provider_checkboxes).grid(
            row=2, column=3, sticky="e", pady=(4, 0)
        )

        # Run button + progress
        run_frame = ttk.Frame(tab)
        run_frame.pack(fill="x", padx=8, pady=4)

        self.run_btn = ttk.Button(run_frame, text="Run Evaluation", command=self._run_evaluation)
        self.run_btn.pack(side="left")

        self.progress = ttk.Progressbar(run_frame, mode="indeterminate", length=300)
        self.progress.pack(side="left", padx=12, fill="x", expand=True)

        # Log area
        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        self.log_text = tk.Text(log_frame, height=15, state="disabled", wrap="word",
                                font=("Courier", 11))
        self.log_text.pack(fill="both", expand=True)

        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side="right", fill="y")

    def _update_provider_checkboxes(self):
        """Enable/disable and check providers based on available keys."""
        for name, required_keys in PROVIDER_KEYS.items():
            var = self.provider_vars[name]
            if not required_keys:
                # whisper_local — always available
                var.set(True)
            else:
                has_keys = all(
                    self.key_entries.get(k, None) and self.key_entries[k].get().strip()
                    for k in required_keys
                )
                var.set(has_keys)

    def _log(self, msg: str):
        """Append message to log (thread-safe via after())."""
        def _do():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        self.after(0, _do)

    def _run_evaluation(self):
        if self._running:
            return

        # Collect selected providers
        selected = [name for name, var in self.provider_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("No providers", "Select at least one provider.")
            return

        # Collect audio files & ground truth
        gt = {}
        for iid in self.audio_tree.get_children():
            fname = self.audio_tree.set(iid, "filename")
            text = self.audio_tree.set(iid, "ground_truth")
            gt[fname] = text

        if not gt:
            messagebox.showwarning("No audio", "Add WAV files in the Setup tab first.")
            return

        audio_files = [DATA_DIR / fname for fname in sorted(gt.keys())]
        missing = [f for f in audio_files if not f.exists()]
        if missing:
            messagebox.showwarning(
                "Missing files",
                f"{len(missing)} audio file(s) not found in data/raw/.\n"
                f"First missing: {missing[0].name}",
            )
            audio_files = [f for f in audio_files if f.exists()]
            if not audio_files:
                return

        # Set env vars from key entries so providers can find them
        for var_name, entry in self.key_entries.items():
            val = entry.get().strip()
            if val:
                os.environ[var_name] = val

        # Save ground truth before running
        TRANSCRIPTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRANSCRIPTS_FILE, "w") as f:
            json.dump(gt, f, indent=2)

        self._running = True
        self.run_btn.configure(state="disabled")
        self.progress.start(15)

        # Clear log
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")

        self._log(f"Starting evaluation with {len(selected)} provider(s), "
                  f"{len(audio_files)} file(s)...")

        def _worker():
            try:
                # Import here to avoid heavy imports at GUI startup
                import sys
                sys.path.insert(0, str(BASE_DIR))
                from evaluate import run_evaluation

                results = run_evaluation(
                    selected, audio_files, gt, RESULTS_DIR,
                    on_progress=self._log,
                )
                self.after(0, lambda: self._on_evaluation_done(results))
            except Exception as e:
                self._log(f"ERROR: {e}")
                self.after(0, self._on_evaluation_failed)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _on_evaluation_done(self, results):
        self._running = False
        self.run_btn.configure(state="normal")
        self.progress.stop()
        self._log("Evaluation complete!")
        self._last_results = results
        self._populate_results(results)
        self.notebook.select(2)  # Switch to Results tab

    def _on_evaluation_failed(self):
        self._running = False
        self.run_btn.configure(state="normal")
        self.progress.stop()

    # ------------------------------------------------------------------ #
    #  Tab 3 — Results                                                    #
    # ------------------------------------------------------------------ #
    def _build_results_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Results")

        # Summary table
        sum_frame = ttk.LabelFrame(tab, text="Summary (by provider)", padding=4)
        sum_frame.pack(fill="x", padx=8, pady=(8, 4))

        sum_cols = ("provider", "avg_wer", "avg_cer", "avg_sim", "avg_time")
        self.summary_tree = ttk.Treeview(sum_frame, columns=sum_cols,
                                         show="headings", height=5)
        self.summary_tree.heading("provider", text="Provider")
        self.summary_tree.heading("avg_wer", text="Avg WER")
        self.summary_tree.heading("avg_cer", text="Avg CER")
        self.summary_tree.heading("avg_sim", text="Avg Semantic Sim")
        self.summary_tree.heading("avg_time", text="Avg Time (s)")
        for c in sum_cols:
            self.summary_tree.column(c, width=140, anchor="center")
        self.summary_tree.column("provider", anchor="w")
        self.summary_tree.pack(fill="x")

        # Detail table
        det_frame = ttk.LabelFrame(tab, text="Per-clip Detail", padding=4)
        det_frame.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        det_cols = ("file", "provider", "transcript", "wer", "cer", "sim")
        self.detail_tree = ttk.Treeview(det_frame, columns=det_cols,
                                        show="headings", height=10)
        self.detail_tree.heading("file", text="File")
        self.detail_tree.heading("provider", text="Provider")
        self.detail_tree.heading("transcript", text="Transcript")
        self.detail_tree.heading("wer", text="WER")
        self.detail_tree.heading("cer", text="CER")
        self.detail_tree.heading("sim", text="Sim")
        self.detail_tree.column("file", width=150)
        self.detail_tree.column("provider", width=120)
        self.detail_tree.column("transcript", width=280)
        self.detail_tree.column("wer", width=70, anchor="center")
        self.detail_tree.column("cer", width=70, anchor="center")
        self.detail_tree.column("sim", width=70, anchor="center")
        self.detail_tree.pack(fill="both", expand=True)

        det_scroll = ttk.Scrollbar(det_frame, orient="vertical",
                                   command=self.detail_tree.yview)
        self.detail_tree.configure(yscrollcommand=det_scroll.set)
        det_scroll.pack(side="right", fill="y")

        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(btn_frame, text="Open Charts", command=self._open_charts).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(btn_frame, text="Open Report", command=self._open_report).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(btn_frame, text="Generate Report", command=self._generate_report).pack(
            side="left"
        )

    def _populate_results(self, results: dict):
        """Fill summary and detail treeviews from results dict."""
        # Clear existing
        for iid in self.summary_tree.get_children():
            self.summary_tree.delete(iid)
        for iid in self.detail_tree.get_children():
            self.detail_tree.delete(iid)

        # Build summary rows, sorted by avg WER
        summaries = []
        for pname, pdata in results.items():
            m = pdata.get("metrics", {})
            t = pdata.get("transcripts", {})
            if not m:
                continue
            n = len(m)
            avg_wer = sum(v["wer"] for v in m.values()) / n
            avg_cer = sum(v["cer"] for v in m.values()) / n
            avg_sim = sum(v["semantic_similarity"] for v in m.values()) / n
            avg_time = sum(t[f]["time_s"] for f in t if "time_s" in t[f]) / n
            summaries.append((pname, avg_wer, avg_cer, avg_sim, avg_time))

        summaries.sort(key=lambda x: x[1])  # sort by WER
        for row in summaries:
            self.summary_tree.insert("", "end", values=(
                row[0], f"{row[1]:.3f}", f"{row[2]:.3f}",
                f"{row[3]:.3f}", f"{row[4]:.2f}",
            ))

        # Detail rows
        for pname, pdata in results.items():
            m = pdata.get("metrics", {})
            t = pdata.get("transcripts", {})
            for fname in sorted(m.keys()):
                metrics = m[fname]
                transcript = t.get(fname, {}).get("transcript", "")
                # Truncate long transcripts for display
                display = transcript[:120] + "..." if len(transcript) > 120 else transcript
                self.detail_tree.insert("", "end", values=(
                    fname, pname, display,
                    f"{metrics['wer']:.3f}",
                    f"{metrics['cer']:.3f}",
                    f"{metrics['semantic_similarity']:.3f}",
                ))

    def _open_charts(self):
        chart = RESULTS_DIR / "comparison_chart.png"
        if chart.exists():
            _open_file(chart)
        else:
            messagebox.showinfo("Not found", "Run 'Generate Report' first to create charts.")

    def _open_report(self):
        report = RESULTS_DIR / "report.md"
        if report.exists():
            _open_file(report)
        else:
            messagebox.showinfo("Not found", "Run 'Generate Report' first.")

    def _generate_report(self):
        """Generate charts and markdown report from saved results."""
        combined = RESULTS_DIR / "combined_results.json"
        if not combined.exists():
            messagebox.showwarning("No results", "Run an evaluation first.")
            return
        try:
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from report import load_results, build_dataframe, generate_summary_table
            from report import plot_bar_chart, plot_per_clip, write_text_report

            results = load_results()
            df = build_dataframe(results)
            summary = generate_summary_table(df)
            RESULTS_DIR.mkdir(exist_ok=True)
            plot_bar_chart(summary, RESULTS_DIR / "comparison_chart.png")
            plot_per_clip(df, RESULTS_DIR / "per_clip_wer.png")
            write_text_report(summary, df, RESULTS_DIR / "report.md")
            messagebox.showinfo("Done", "Report and charts generated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report:\n{e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
