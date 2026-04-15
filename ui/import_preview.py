import customtkinter as ctk
from modules import contact_book

class ImportPreviewWindow(ctk.CTkToplevel):
    def __init__(self, parent, plan, on_confirm):
        super().__init__(parent)
        self.title("Import Preview & Confirmation")
        self.geometry("500x600")
        
        self.plan = plan
        self.on_confirm = on_confirm
        
        # Modal setup
        self.attributes('-topmost', 1)
        self.grab_set()
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ── Header ──────────────────────────────────────────────────────────
        self.header = ctk.CTkLabel(
            self, text="📋 Contact Import Summary",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.header.grid(row=0, column=0, pady=20)

        # ── Stats Frame ──────────────────────────────────────────────────────
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.stats_frame.grid_columnconfigure(0, weight=1)

        new_count = len(plan.get("new", {}))
        upd_count = len(plan.get("update", {}))
        pre_count = len(plan.get("preserve", {}))
        total     = plan.get("total_scanned", 0)

        ctk.CTkLabel(self.stats_frame, text=f"Total lines scanned: {total}", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        
        # New
        new_lbl = ctk.CTkLabel(self.stats_frame, text=f"✨ New contacts to add: {new_count}", text_color="#2da44e")
        new_lbl.pack(anchor="w", padx=20)
        
        # Updates
        upd_lbl = ctk.CTkLabel(self.stats_frame, text=f"🔄 Names to update (no nickname): {upd_count}", text_color="#f1c40f")
        upd_lbl.pack(anchor="w", padx=20)
        
        # Preserved
        pre_lbl = ctk.CTkLabel(self.stats_frame, text=f"🛡️ Preserved (existing nickname): {pre_count}", text_color="gray")
        pre_lbl.pack(anchor="w", padx=20)

        # Scrollable list for detail
        self.detail_list = ctk.CTkScrollableFrame(self.stats_frame, height=250)
        self.detail_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Populate small sample or full list
        self._populate_details()

        # ── Footer Buttons ──────────────────────────────────────────────────
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=20)
        self.btn_frame.grid_columnconfigure(0, weight=1)
        self.btn_frame.grid_columnconfigure(1, weight=1)

        self.cancel_btn = ctk.CTkButton(
            self.btn_frame, text="Cancel", fg_color="#c0392b", hover_color="#a93226",
            command=self.destroy
        )
        self.cancel_btn.grid(row=0, column=0, padx=(0, 5))

        self.confirm_btn = ctk.CTkButton(
            self.btn_frame, text="Confirm & Import", fg_color="#2da44e", hover_color="#2c974b",
            command=self._do_confirm
        )
        self.confirm_btn.grid(row=0, column=1, padx=(5, 0))

    def _populate_details(self):
        # Sample of new
        if self.plan["new"]:
            ctk.CTkLabel(self.detail_list, text="--- NEW ENTRIES ---", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            for p, n in list(self.plan["new"].items())[:20]:
                ctk.CTkLabel(self.detail_list, text=f"+ {n} ({p})", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5)
            if len(self.plan["new"]) > 20:
                ctk.CTkLabel(self.detail_list, text=f"... and {len(self.plan['new'])-20} more", font=ctk.CTkFont(size=9, slant="italic")).pack(anchor="w", padx=5)

        # Sample of updates
        if self.plan["update"]:
            ctk.CTkLabel(self.detail_list, text="\n--- UPDATING NAMES ---", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
            for p, d in list(self.plan["update"].items())[:20]:
                ctk.CTkLabel(self.detail_list, text=f"~ {p}: {d['old'] or 'None'} -> {d['new']}", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=5)

    def _do_confirm(self):
        success = contact_book.apply_import_plan(self.plan)
        if self.on_confirm:
            self.on_confirm(success)
        self.destroy()
