"""Tkinter GUI for CP Speech Pronunciation Correction.

Two-tab interface:
  Tab 1 — Learn Patterns: Analyze WAV files to build discrepancy table.
  Tab 2 — Transcribe & Correct: Use learned patterns to correct new transcriptions.
"""

import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

BASE_DIR = Path(__file__).parent
ENV_FILE = BASE_DIR / ".env"


def _load_env():
    """Load .env file into os.environ."""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip().strip("\"'"))


class CorrectionApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CP Speech — Pronunciation Correction")
        self.geometry("950x700")
        self.minsize(850, 600)

        _load_env()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self._build_learn_tab()
        self._build_transcribe_tab()

        self._running = False

    # ------------------------------------------------------------------ #
    #  Tab 1 — Learn Patterns                                             #
    # ------------------------------------------------------------------ #
    def _build_learn_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Learn Patterns")

        # --- Audio files section ---
        file_frame = ttk.LabelFrame(tab, text="Audio Files", padding=8)
        file_frame.pack(fill="both", expand=True, padx=8, pady=(8, 4))

        btn_row = ttk.Frame(file_frame)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text="Add WAV Files", command=self._add_wav_files).pack(
            side="left"
        )
        ttk.Button(btn_row, text="Remove Selected", command=self._remove_selected_files).pack(
            side="left", padx=8
        )
        self.analyze_btn = ttk.Button(btn_row, text="Analyze", command=self._run_analysis)
        self.analyze_btn.pack(side="right")

        cols = ("filename", "correct_text", "raw_transcript", "status")
        self.file_tree = ttk.Treeview(file_frame, columns=cols, show="headings", height=6)
        self.file_tree.heading("filename", text="Filename")
        self.file_tree.heading("correct_text", text="Correct Text (double-click)")
        self.file_tree.heading("raw_transcript", text="Raw Transcript")
        self.file_tree.heading("status", text="Status")
        self.file_tree.column("filename", width=180)
        self.file_tree.column("correct_text", width=250)
        self.file_tree.column("raw_transcript", width=250)
        self.file_tree.column("status", width=100, anchor="center")
        self.file_tree.pack(fill="both", expand=True, pady=(6, 0))

        file_scroll = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=file_scroll.set)
        file_scroll.pack(side="right", fill="y")

        self.file_tree.bind("<Double-1>", self._edit_correct_text)

        # Progress bar + log
        prog_frame = ttk.Frame(tab)
        prog_frame.pack(fill="x", padx=8, pady=4)
        self.learn_progress = ttk.Progressbar(prog_frame, mode="indeterminate", length=300)
        self.learn_progress.pack(side="left", fill="x", expand=True)

        log_frame = ttk.LabelFrame(tab, text="Log", padding=4)
        log_frame.pack(fill="x", padx=8, pady=(0, 4))

        self.learn_log = tk.Text(log_frame, height=4, state="disabled", wrap="word",
                                 font=("Courier", 11))
        self.learn_log.pack(fill="x")

        # --- Discrepancy table section ---
        disc_frame = ttk.LabelFrame(tab, text="Learned Patterns", padding=8)
        disc_frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        disc_btn_row = ttk.Frame(disc_frame)
        disc_btn_row.pack(fill="x")
        ttk.Button(disc_btn_row, text="Remove Selected", command=self._remove_selected_pattern).pack(
            side="left"
        )
        ttk.Button(disc_btn_row, text="Save Patterns", command=self._save_patterns).pack(
            side="right"
        )

        dcols = ("spoken", "intended", "pattern_type", "notes")
        self.disc_tree = ttk.Treeview(disc_frame, columns=dcols, show="headings", height=5)
        self.disc_tree.heading("spoken", text="Spoken")
        self.disc_tree.heading("intended", text="Intended")
        self.disc_tree.heading("pattern_type", text="Pattern Type")
        self.disc_tree.heading("notes", text="Notes")
        self.disc_tree.column("spoken", width=150)
        self.disc_tree.column("intended", width=150)
        self.disc_tree.column("pattern_type", width=200)
        self.disc_tree.column("notes", width=250)
        self.disc_tree.pack(fill="both", expand=True, pady=(6, 0))

        disc_scroll = ttk.Scrollbar(disc_frame, orient="vertical", command=self.disc_tree.yview)
        self.disc_tree.configure(yscrollcommand=disc_scroll.set)
        disc_scroll.pack(side="right", fill="y")

        # Load existing patterns
        self._load_existing_patterns()

    # --- file list helpers ---

    # Store full paths for each treeview item
    _file_paths: dict[str, str] = {}

    def _add_wav_files(self):
        paths = filedialog.askopenfilenames(
            title="Select WAV files",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if not paths:
            return
        existing = {
            self.file_tree.set(iid, "filename")
            for iid in self.file_tree.get_children()
        }
        for p in paths:
            src = Path(p)
            if src.name not in existing:
                correct_text = src.stem.replace("_", " ").replace("-", " ")
                iid = self.file_tree.insert(
                    "", "end",
                    values=(src.name, correct_text, "", "pending"),
                )
                self._file_paths[iid] = str(src)
                existing.add(src.name)

    def _remove_selected_files(self):
        for iid in self.file_tree.selection():
            self._file_paths.pop(iid, None)
            self.file_tree.delete(iid)

    def _edit_correct_text(self, event):
        """Double-click to edit correct text in-place."""
        region = self.file_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.file_tree.identify_column(event.x)
        if col != "#2":  # Only edit correct_text column
            return
        iid = self.file_tree.identify_row(event.y)
        if not iid:
            return

        bbox = self.file_tree.bbox(iid, column="correct_text")
        if not bbox:
            return
        x, y, w, h = bbox

        current = self.file_tree.set(iid, "correct_text")
        entry = tk.Entry(self.file_tree, width=w // 7)
        entry.insert(0, current)
        entry.select_range(0, "end")
        entry.place(x=x, y=y, width=w, height=h)
        entry.focus_set()

        def _on_confirm(e=None):
            self.file_tree.set(iid, "correct_text", entry.get())
            entry.destroy()

        def _on_cancel(e=None):
            entry.destroy()

        entry.bind("<Return>", _on_confirm)
        entry.bind("<Escape>", _on_cancel)
        entry.bind("<FocusOut>", _on_confirm)

    # --- analysis ---

    def _log_learn(self, msg: str):
        """Thread-safe log to learn tab."""
        def _do():
            self.learn_log.configure(state="normal")
            self.learn_log.insert("end", msg + "\n")
            self.learn_log.see("end")
            self.learn_log.configure(state="disabled")
        self.after(0, _do)

    def _run_analysis(self):
        if self._running:
            return

        items = self.file_tree.get_children()
        if not items:
            messagebox.showwarning("No files", "Add WAV files first.")
            return

        self._running = True
        self.analyze_btn.configure(state="disabled")
        self.learn_progress.start(15)

        # Clear log
        self.learn_log.configure(state="normal")
        self.learn_log.delete("1.0", "end")
        self.learn_log.configure(state="disabled")

        # Collect work items
        work = []
        for iid in items:
            fname = self.file_tree.set(iid, "filename")
            correct = self.file_tree.set(iid, "correct_text")
            audio_path = self._file_paths.get(iid, "")
            if not audio_path:
                # Try data/raw fallback
                fallback = BASE_DIR / "data" / "raw" / fname
                if fallback.exists():
                    audio_path = str(fallback)
            work.append((iid, fname, correct, audio_path))

        def _worker():
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from speech_correction import analyze_discrepancies

            all_patterns = []
            for iid, fname, correct, audio_path in work:
                if not audio_path or not Path(audio_path).exists():
                    self._log_learn(f"SKIP {fname}: file not found")
                    self.after(0, lambda i=iid: self.file_tree.set(i, "status", "not found"))
                    continue

                self._log_learn(f"Analyzing {fname}...")
                self.after(0, lambda i=iid: self.file_tree.set(i, "status", "analyzing..."))

                try:
                    result = analyze_discrepancies(audio_path, correct)
                    raw = result["raw_transcript"]
                    patterns = result["patterns"]
                    all_patterns.extend(patterns)

                    self.after(0, lambda i=iid, r=raw: self.file_tree.set(i, "raw_transcript", r))
                    self.after(0, lambda i=iid: self.file_tree.set(i, "status", "done"))
                    self._log_learn(f"  {fname}: {len(patterns)} pattern(s) found")
                except Exception as e:
                    self._log_learn(f"  ERROR {fname}: {e}")
                    self.after(0, lambda i=iid: self.file_tree.set(i, "status", "error"))

            # Add new patterns to discrepancy treeview
            self.after(0, lambda: self._add_patterns_to_tree(all_patterns))
            self.after(0, self._on_analysis_done)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _add_patterns_to_tree(self, patterns: list[dict]):
        for p in patterns:
            self.disc_tree.insert("", "end", values=(
                p.get("spoken", ""),
                p.get("intended", ""),
                p.get("pattern_type", ""),
                p.get("notes", ""),
            ))

    def _on_analysis_done(self):
        self._running = False
        self.analyze_btn.configure(state="normal")
        self.learn_progress.stop()
        self._log_learn("Analysis complete.")

    # --- discrepancy table ---

    def _load_existing_patterns(self):
        from speech_correction import load_discrepancies
        data = load_discrepancies()
        for p in data.get("patterns", []):
            self.disc_tree.insert("", "end", values=(
                p.get("spoken", ""),
                p.get("intended", ""),
                p.get("pattern_type", ""),
                p.get("notes", ""),
            ))

    def _remove_selected_pattern(self):
        for iid in self.disc_tree.selection():
            self.disc_tree.delete(iid)

    def _save_patterns(self):
        from speech_correction import save_discrepancies

        patterns = []
        for iid in self.disc_tree.get_children():
            patterns.append({
                "spoken": self.disc_tree.set(iid, "spoken"),
                "intended": self.disc_tree.set(iid, "intended"),
                "pattern_type": self.disc_tree.set(iid, "pattern_type"),
                "notes": self.disc_tree.set(iid, "notes"),
            })

        data = {"patterns": patterns, "speaker_notes": ""}
        save_discrepancies(data)
        messagebox.showinfo("Saved", f"Saved {len(patterns)} pattern(s) to data/discrepancies.json")

    # ------------------------------------------------------------------ #
    #  Tab 2 — Transcribe & Correct                                       #
    # ------------------------------------------------------------------ #
    def _build_transcribe_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="Transcribe & Correct")

        # File selection
        file_frame = ttk.Frame(tab)
        file_frame.pack(fill="x", padx=8, pady=(8, 4))

        ttk.Button(file_frame, text="Select WAV File", command=self._select_transcribe_file).pack(
            side="left"
        )
        self.transcribe_file_label = ttk.Label(file_frame, text="No file selected")
        self.transcribe_file_label.pack(side="left", padx=12)

        self.transcribe_btn = ttk.Button(file_frame, text="Transcribe", command=self._run_transcribe)
        self.transcribe_btn.pack(side="right")

        self._transcribe_path: str | None = None

        # Progress
        self.trans_progress = ttk.Progressbar(tab, mode="indeterminate", length=300)
        self.trans_progress.pack(fill="x", padx=8, pady=4)

        # Results
        result_frame = ttk.LabelFrame(tab, text="Results", padding=12)
        result_frame.pack(fill="both", expand=True, padx=8, pady=(4, 8))

        ttk.Label(result_frame, text="Raw Whisper Transcript:", font=("TkDefaultFont", 12, "bold")).pack(
            anchor="w", pady=(0, 4)
        )
        self.raw_text = tk.Text(result_frame, height=5, wrap="word", state="disabled",
                                font=("Courier", 12))
        self.raw_text.pack(fill="x", pady=(0, 12))

        ttk.Label(result_frame, text="Corrected Transcript:", font=("TkDefaultFont", 12, "bold")).pack(
            anchor="w", pady=(0, 4)
        )
        self.corrected_text = tk.Text(result_frame, height=5, wrap="word", state="disabled",
                                      font=("Courier", 12))
        self.corrected_text.pack(fill="x", pady=(0, 8))

        # Pattern count info
        self.pattern_info_label = ttk.Label(result_frame, text="")
        self.pattern_info_label.pack(anchor="w")
        self._update_pattern_info()

    def _update_pattern_info(self):
        from speech_correction import load_discrepancies
        data = load_discrepancies()
        n = len(data.get("patterns", []))
        self.pattern_info_label.configure(
            text=f"Loaded {n} pronunciation pattern(s)" if n else "No patterns loaded — use Tab 1 to learn patterns first"
        )

    def _select_transcribe_file(self):
        path = filedialog.askopenfilename(
            title="Select WAV file",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
        )
        if path:
            self._transcribe_path = path
            self.transcribe_file_label.configure(text=Path(path).name)

    def _run_transcribe(self):
        if self._running:
            return
        if not self._transcribe_path:
            messagebox.showwarning("No file", "Select a WAV file first.")
            return

        self._running = True
        self.transcribe_btn.configure(state="disabled")
        self.trans_progress.start(15)

        # Clear results
        for widget in (self.raw_text, self.corrected_text):
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.configure(state="disabled")

        audio_path = self._transcribe_path

        def _worker():
            import sys
            sys.path.insert(0, str(BASE_DIR))
            from speech_correction import corrected_transcribe

            try:
                result = corrected_transcribe(audio_path)
                self.after(0, lambda: self._show_transcription(result))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror("Error", f"Transcription failed:\n{e}"))
                self.after(0, self._on_transcribe_done)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()

    def _show_transcription(self, result: dict):
        self.raw_text.configure(state="normal")
        self.raw_text.delete("1.0", "end")
        self.raw_text.insert("1.0", result.get("raw_transcript", ""))
        self.raw_text.configure(state="disabled")

        self.corrected_text.configure(state="normal")
        self.corrected_text.delete("1.0", "end")
        self.corrected_text.insert("1.0", result.get("corrected_transcript", ""))
        self.corrected_text.configure(state="disabled")

        self._update_pattern_info()
        self._on_transcribe_done()

    def _on_transcribe_done(self):
        self._running = False
        self.transcribe_btn.configure(state="normal")
        self.trans_progress.stop()


if __name__ == "__main__":
    app = CorrectionApp()
    app.mainloop()
