"""app.py – Auto Subtitle Tool  (controller + upload page)"""

import tkinter as tk
from tkinter import ttk, filedialog
import os

# ── colour palette ────────────────────────────────────────────────────────────
BG       = "#0a0a0a"
PANEL    = "#111111"
ACCENT   = "#ffffff"
ACCENT2  = "#cccccc"
TEXT     = "#f0f0f0"
SUBTEXT  = "#666666"
ENTRY_BG = "#1a1a1a"
DIVIDER  = "#222222"
GREEN    = "#22c55e"

# ── subtitle preset definitions ───────────────────────────────────────────────
PRESETS = [
    {"name": "มาตรฐาน",    "font": "Tahoma", "size": 32, "color": "#ffffff", "deco": "outline", "anim": "none"},
    {"name": "ริบบอน",     "font": "Tahoma", "size": 28, "color": "#ffffff", "deco": "box",     "anim": "fade_in"},
    {"name": "หัวมอล",     "font": "Tahoma", "size": 34, "color": "#facc15", "deco": "shadow",  "anim": "none"},
    {"name": "ซีออนเขียว", "font": "Tahoma", "size": 30, "color": "#22c55e", "deco": "outline", "anim": "fade_in"},
    {"name": "ดาร์กโมด",   "font": "Tahoma", "size": 28, "color": "#f0f0f0", "deco": "box",     "anim": "slide_up"},
    {"name": "ป๊อปโซน",    "font": "Tahoma", "size": 34, "color": "#ff4444", "deco": "shadow",  "anim": "pop"},
    {"name": "พาสเทล",     "font": "Tahoma", "size": 30, "color": "#c084fc", "deco": "outline", "anim": "fade_in"},
    {"name": "คลาสสิก",    "font": "Tahoma", "size": 32, "color": "#ffd700", "deco": "outline", "anim": "none"},
]


# ── main controller ───────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Auto Subtitle")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=BG)
        self._page = None
        self._show_upload()

    def _show_upload(self):
        self._swap(UploadPage, on_start=self._on_start)
        self.geometry("1100x700")

    def _on_start(self, video_path, preset_idx, model):
        from editor_page import EditorPage
        self.geometry("1640x860")
        self._swap(EditorPage,
                   video_path=video_path,
                   preset=PRESETS[preset_idx],
                   model=model,
                   on_back=self._show_upload)

    def _swap(self, PageClass, **kw):
        if self._page:
            self._page.destroy()
        self._page = PageClass(self, **kw)
        self._page.pack(fill="both", expand=True)


# ── upload page ───────────────────────────────────────────────────────────────
class UploadPage(tk.Frame):
    def __init__(self, master, on_start):
        super().__init__(master, bg=BG)
        self._on_start = on_start
        self._video_path = None
        self._preset_idx = 0
        self._model_var = tk.StringVar(value="base")
        self._wpl_var = tk.IntVar(value=0)
        self._build()

    # ── layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # header
        hdr = tk.Frame(self, bg=PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Auto Subtitle", font=("Segoe UI", 15, "bold"),
                 bg=PANEL, fg=TEXT).pack(side="left", padx=20, pady=12)
        tk.Label(hdr, text="/ อัปโหลดวิดีโอ แล้ว AI จะถอดเสียงและใส่ซับให้อัตโนมัติ",
                 font=("Segoe UI", 9), bg=PANEL, fg=SUBTEXT).pack(side="left", pady=15)

        # body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))

        right = tk.Frame(body, bg=PANEL)
        right.pack(side="left", fill="y", ipadx=0)
        right.configure(width=360)
        right.pack_propagate(False)

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, parent):
        # project name
        tk.Label(parent, text="ชื่อโปรเจกต์", font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        self._name_e = tk.Entry(parent, bg=ENTRY_BG, fg=TEXT, insertbackground=TEXT,
                                relief="flat", font=("Segoe UI", 10))
        self._name_e.insert(0, "เช่น คลิปสอนทำอาหาร EP.1")
        self._name_e.pack(fill="x", ipady=6, pady=(4, 14))

        # drop zone
        tk.Label(parent, text="อัปโหลดวิดีโอ", font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        self._drop = tk.Canvas(parent, height=220, bg=ENTRY_BG,
                               highlightthickness=1, highlightbackground=DIVIDER,
                               cursor="hand2")
        self._drop.pack(fill="x", pady=(4, 6))
        self._draw_drop(None)
        self._drop.bind("<Button-1>", lambda e: self._browse())

        self._file_lbl = tk.Label(parent, text="", bg=BG, fg=SUBTEXT,
                                  font=("Segoe UI", 9))
        self._file_lbl.pack(anchor="w")

        # start button
        self._start_btn = tk.Button(parent, text="กรุณาเลือกวิดีโอก่อน",
                                    bg=DIVIDER, fg=SUBTEXT,
                                    font=("Segoe UI", 10, "bold"),
                                    relief="flat", cursor="hand2", pady=10,
                                    state="disabled", command=self._start)
        self._start_btn.pack(fill="x", pady=14)

    def _build_right(self, parent):
        # scrollable settings
        cv = tk.Canvas(parent, bg=PANEL, highlightthickness=0)
        sb = ttk.Scrollbar(parent, orient="vertical", command=cv.yview)
        frm = tk.Frame(cv, bg=PANEL)
        frm.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=frm, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        cv.pack(fill="both", expand=True)
        cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(-1 * (e.delta // 120), "units"))

        P = dict(padx=14, pady=3)
        tk.Label(frm, text="AI SETTINGS", font=("Segoe UI", 10, "bold"),
                 bg=PANEL, fg=TEXT).pack(anchor="w", padx=14, pady=(14, 8))

        # whisper model
        tk.Label(frm, text="โมเดล Whisper", font=("Segoe UI", 8),
                 bg=PANEL, fg=SUBTEXT).pack(anchor="w", padx=14)
        mf = tk.Frame(frm, bg=PANEL)
        mf.pack(fill="x", **P)
        self._model_btns = {}
        def _sel_m(v):
            if v == "custom":
                d = filedialog.askdirectory(title="เลือกโฟลเดอร์โมเดล (Hugging Face)")
                if not d: return
                self._model_var.set(d)
                v = "custom"
            else:
                self._model_var.set(v)
            
            for k, b in self._model_btns.items():
                b.configure(bg=ACCENT if k == v else ENTRY_BG,
                            fg=BG if k == v else TEXT)

        for m in ["tiny", "base", "small", "medium", "custom"]:
            b = tk.Button(mf, text=m, font=("Segoe UI", 8),
                          bg=ACCENT if m == "base" else ENTRY_BG,
                          fg=BG if m == "base" else TEXT,
                          relief="flat", padx=8, pady=4, command=lambda v=m: _sel_m(v))
            b.pack(side="left", padx=2)
            self._model_btns[m] = b

        # style presets
        tk.Label(frm, text="สไตล์ซับไตเติล", font=("Segoe UI", 9, "bold"),
                 bg=PANEL, fg=TEXT).pack(anchor="w", padx=14, pady=(14, 6))
        grid = tk.Frame(frm, bg=PANEL)
        grid.pack(fill="x", padx=14)
        self._pcvs = []
        for i, p in enumerate(PRESETS):
            c = tk.Canvas(grid, width=148, height=72, bg="#161616",
                          highlightthickness=1,
                          highlightbackground=ACCENT if i == 0 else DIVIDER,
                          cursor="hand2")
            c.grid(row=i // 2, column=i % 2, padx=3, pady=3)
            c.create_text(74, 30, text="ตัวอย่าง", font=("Tahoma", 12, "bold"),
                          fill=p["color"])
            c.create_text(74, 58, text=p["name"], font=("Segoe UI", 8),
                          fill=SUBTEXT)
            c.bind("<Button-1>", lambda e, idx=i: self._sel_preset(idx))
            self._pcvs.append(c)

        # words per line
        tk.Label(frm, text="จำนวนซับต่อหน้า", font=("Segoe UI", 9, "bold"),
                 bg=PANEL, fg=TEXT).pack(anchor="w", padx=14, pady=(14, 4))
        wf = tk.Frame(frm, bg=PANEL)
        wf.pack(fill="x", padx=14, pady=(0, 14))
        for lbl, val in [("ไม่แบ่ง", 0), ("1 คำ", 1), ("2 คำ", 2), ("3 คำ", 3), ("4 คำ", 4)]:
            tk.Radiobutton(wf, text=lbl, variable=self._wpl_var, value=val,
                           bg=PANEL, fg=TEXT, selectcolor=ENTRY_BG,
                           activebackground=PANEL, activeforeground=TEXT,
                           font=("Segoe UI", 8)).pack(side="left", padx=3)

    # ── helpers ───────────────────────────────────────────────────────────────
    def _draw_drop(self, path):
        c = self._drop
        c.delete("all")
        w = c.winfo_width() or 560
        h = c.winfo_height() or 220
        if path:
            name = os.path.basename(path)
            c.create_text(w // 2, h // 2 - 12, text="✅  " + name,
                          fill=GREEN, font=("Segoe UI", 11, "bold"))
            c.create_text(w // 2, h // 2 + 18, text="คลิกเพื่อเปลี่ยนไฟล์",
                          fill=SUBTEXT, font=("Segoe UI", 9))
        else:
            c.create_text(w // 2, h // 2 - 16, text="⬆",
                          fill=SUBTEXT, font=("Segoe UI", 28))
            c.create_text(w // 2, h // 2 + 14, text="Drag & Drop  หรือ คลิกเพื่อเลือกไฟล์",
                          fill=SUBTEXT, font=("Segoe UI", 10))
            c.create_text(w // 2, h // 2 + 36, text="MP4, MOV, AVI, MKV",
                          fill=DIVIDER, font=("Segoe UI", 8))

    def _browse(self):
        p = filedialog.askopenfilename(
            filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv *.webm"), ("All", "*.*")])
        if p:
            self._video_path = p
            self._draw_drop(p)
            size_mb = os.path.getsize(p) / 1e6
            self._file_lbl.configure(text=f"{os.path.basename(p)}  ({size_mb:.1f} MB)")
            self._start_btn.configure(text="▶  เริ่มถอดเสียงและใส่ซับ",
                                      bg=ACCENT, fg=BG, state="normal")

    def _sel_preset(self, idx):
        for i, c in enumerate(self._pcvs):
            c.configure(highlightbackground=ACCENT if i == idx else DIVIDER)
        self._preset_idx = idx

    def _start(self):
        if self._video_path:
            self._on_start(self._video_path, self._preset_idx,
                           self._model_var.get())


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
