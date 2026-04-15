import customtkinter as ctk
import os
import threading
from tkinter import filedialog, messagebox
from ui.settings_window import SettingsWindow
from ui.utils import add_context_menu, resource_path
from modules import config_manager, rate_limiter, goto_api, gemini_ai, contact_book



class MainWindow(ctk.CTk):
    def __init__(self, version=""):
        super().__init__()
        title = f"GoTo SMS AI Assistant v{version}" if version else "GoTo SMS AI Assistant"
        self.title(title)
        self.geometry("1200x720")
        self.minsize(900, 600)

        # Set window icon
        try:
            icon_path = resource_path("app.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # ── Active contact state ───────────────────────────────────────────────
        self._active_phone = ""   # phone selected from recent-chats tower
        self._contacts     = contact_book.load_contacts()  # local name cache


        # ── Root grid: 1 header row + 1 main row + 1 status row ──────────────
        #    3 columns: [left tower] [chat history] [AI builder]
        self.grid_rowconfigure(0, weight=0)   # header
        self.grid_rowconfigure(1, weight=1)   # main content
        self.grid_rowconfigure(2, weight=0)   # status bar
        self.grid_columnconfigure(0, weight=2)  # left tower
        self.grid_columnconfigure(1, weight=3)  # middle: chat history
        self.grid_columnconfigure(2, weight=3)  # right: AI panel

        # ══════════════════════════════════════════════════════════════════════
        # HEADER
        # ══════════════════════════════════════════════════════════════════════
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=(10, 5))

        self.header_label = ctk.CTkLabel(
            self.header_frame,
            text="💬 GoTo SMS AI Assistant",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.pack(side="left", padx=10, pady=8)

        self.settings_btn = ctk.CTkButton(
            self.header_frame, text="⚙️ Settings",
            command=self.open_settings, width=100
        )
        self.settings_btn.pack(side="right", padx=10, pady=8)

        # ══════════════════════════════════════════════════════════════════════
        # LEFT TOWER — Recent Chats
        # ══════════════════════════════════════════════════════════════════════
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 5))
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        self.recent_header = ctk.CTkLabel(
            self.left_frame, text="Recent Chats",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.recent_header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))

        self.refresh_btn = ctk.CTkButton(
            self.left_frame, text="🔄 Refresh",
            command=self.fetch_recent_chats, height=28
        )
        self.refresh_btn.grid(row=0, column=0, sticky="e", padx=10, pady=(10, 2))

        # Scrollable list of conversations
        self.chat_list_frame = ctk.CTkScrollableFrame(self.left_frame)
        self.chat_list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(2, 5))
        self.chat_list_frame.grid_columnconfigure(0, weight=1)

        self._chat_row_widgets = []   # keep references to avoid GC

        # ══════════════════════════════════════════════════════════════════════
        # MIDDLE PANEL — Chat History
        # ══════════════════════════════════════════════════════════════════════
        self.mid_frame = ctk.CTkFrame(self)
        self.mid_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=(0, 5))
        self.mid_frame.grid_rowconfigure(1, weight=0)
        self.mid_frame.grid_columnconfigure(0, weight=1)

        # Contact identity bar
        self.contact_bar = ctk.CTkFrame(self.mid_frame, fg_color="transparent")
        self.contact_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.contact_bar.grid_columnconfigure(1, weight=1)

        self.active_contact_label = ctk.CTkLabel(
            self.contact_bar, text="No contact selected",
            font=ctk.CTkFont(size=12, weight="bold"), text_color="gray"
        )
        self.active_contact_label.grid(row=0, column=0, sticky="w")

        self.receiver_entry = ctk.CTkEntry(
            self.contact_bar, placeholder_text="Nickname (optional)",
            width=160
        )
        self.receiver_entry.grid(row=0, column=1, sticky="e", padx=(10, 0))
        add_context_menu(self.receiver_entry)

        # Action buttons row
        self.mid_btn_row = ctk.CTkFrame(self.mid_frame, fg_color="transparent")
        self.mid_btn_row.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 0))
        self.mid_btn_row.grid_columnconfigure(0, weight=1)
        self.mid_btn_row.grid_columnconfigure(1, weight=1)

        self.fetch_btn = ctk.CTkButton(
            self.mid_btn_row, text="📨 Load Chat",
            command=self.fetch_sms, height=34
        )
        self.fetch_btn.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self.export_btn = ctk.CTkButton(
            self.mid_btn_row, text="📥 Export",
            command=self.export_history,
            fg_color="#34495e", hover_color="#2c3e50", height=34
        )
        self.export_btn.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        # Chat history textbox
        self.history_text = ctk.CTkTextbox(self.mid_frame, wrap="word")
        self.history_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 10))
        self.mid_frame.grid_rowconfigure(2, weight=1)
        self.history_text.insert("0.0", "Select a contact from the left panel to load chat history...")
        self.history_text.configure(state="disabled")
        add_context_menu(self.history_text)

        # Colour tags
        inner_text = self.history_text._textbox
        inner_text.tag_config("user_label",   justify="right", foreground="#4caf50")
        inner_text.tag_config("user_body",    justify="right", foreground="#ffffff")
        inner_text.tag_config("client_label", justify="left",  foreground="#90caf9")
        inner_text.tag_config("client_body",  justify="left",  foreground="#dddddd")
        inner_text.tag_config("system_msg",   justify="center",foreground="#888888")

        # ══════════════════════════════════════════════════════════════════════
        # RIGHT PANEL — AI Builder (full height)
        # ══════════════════════════════════════════════════════════════════════
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=1, column=2, sticky="nsew", padx=(5, 10), pady=(0, 5))
        self.right_frame.grid_rowconfigure(2, weight=1)   # intent box grows
        self.right_frame.grid_rowconfigure(4, weight=2)   # draft box grows more
        self.right_frame.grid_columnconfigure(0, weight=1)

        # Tone
        self.tone_label = ctk.CTkLabel(self.right_frame, text="Desired Tone:")
        self.tone_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 0))

        self.tone_var = ctk.StringVar(value="Professional")
        self.tone_combo = ctk.CTkComboBox(
            self.right_frame,
            values=["Professional", "Casual", "Empathetic", "Direct", "Apologetic"],
            variable=self.tone_var
        )
        self.tone_combo.grid(row=1, column=0, sticky="ew", padx=10, pady=(2, 0))

        # Intent
        self.intent_label = ctk.CTkLabel(self.right_frame, text="What do you want to say?")
        self.intent_label.grid(row=2, column=0, sticky="w", padx=10, pady=(10, 0))

        self.intent_text = ctk.CTkTextbox(self.right_frame, wrap="word")
        self.intent_text.grid(row=2, column=0, sticky="nsew", padx=10, pady=(28, 0))
        add_context_menu(self.intent_text)

        # Generate button + Use Paid toggle
        self.gen_btn_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        self.gen_btn_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.gen_btn_frame.grid_columnconfigure(0, weight=1)

        self.generate_btn = ctk.CTkButton(
            self.gen_btn_frame, text="✨ Generate AI Reply",
            command=self.generate_reply
        )
        self.generate_btn.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        self.use_paid_var = ctk.BooleanVar(value=False)
        self.use_paid_switch = ctk.CTkSwitch(
            self.gen_btn_frame, text="Use Paid",
            variable=self.use_paid_var,
            font=ctk.CTkFont(size=12)
        )
        self.use_paid_switch.grid(row=0, column=1, sticky="e")

        # Draft reply
        self.draft_label = ctk.CTkLabel(self.right_frame, text="Draft Reply (Editable):")
        self.draft_label.grid(row=4, column=0, sticky="w", padx=10, pady=(4, 0))

        self.draft_text = ctk.CTkTextbox(self.right_frame, wrap="word")
        self.draft_text.grid(row=4, column=0, sticky="nsew", padx=10, pady=(22, 0))
        add_context_menu(self.draft_text)

        # Send button
        self.send_btn = ctk.CTkButton(
            self.right_frame, text="📤 Send SMS",
            command=self.send_sms,
            fg_color="#2da44e", hover_color="#2c974b"
        )
        self.send_btn.grid(row=5, column=0, sticky="ew", padx=10, pady=(6, 12))

        # ══════════════════════════════════════════════════════════════════════
        # STATUS BAR
        # ══════════════════════════════════════════════════════════════════════
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 6))
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w")

        self.cooldown_label = ctk.CTkLabel(
            self.status_frame, text="AI: 0s | GoTo: 0s",
            anchor="e", font=ctk.CTkFont(family="Consolas", size=12)
        )
        self.cooldown_label.grid(row=0, column=1, sticky="e")

        # Start cooldown monitor & auto-load recent chats
        self._update_cooldown_monitor()
        self.after(500, self.fetch_recent_chats)

    # ══════════════════════════════════════════════════════════════════════════
    # COOLDOWN MONITOR
    # ══════════════════════════════════════════════════════════════════════════
    def _update_cooldown_monitor(self):
        ai_cd   = rate_limiter.get_remaining_cooldown(key="last_ai_call",   cooldown_seconds=rate_limiter.AI_COOLDOWN_SECONDS)
        goto_cd = rate_limiter.get_remaining_cooldown(key="last_goto_pull", cooldown_seconds=rate_limiter.GOTO_COOLDOWN_SECONDS)
        self.cooldown_label.configure(text=f"AI: {ai_cd}s | GoTo: {goto_cd}s")
        color = "#f1c40f" if (ai_cd > 0 or goto_cd > 0) else "gray"
        self.cooldown_label.configure(text_color=color)
        self.after(1000, self._update_cooldown_monitor)

    def open_settings(self):
        SettingsWindow(self)

    # ══════════════════════════════════════════════════════════════════════════
    # RECENT CHATS TOWER
    # ══════════════════════════════════════════════════════════════════════════
    def fetch_recent_chats(self):
        self.refresh_btn.configure(state="disabled")
        self.status_label.configure(text="Loading recent chats...")

        def _fetch():
            gapi = goto_api.GoToAPI()
            result = gapi.get_recent_conversations()

            def _update_ui():
                if not self.winfo_exists():
                    return
                # Clear current list
                for w in self._chat_row_widgets:
                    if w.winfo_exists():
                        w.destroy()
                self._chat_row_widgets.clear()

                if "error" in result:
                    err_label = ctk.CTkLabel(
                        self.chat_list_frame,
                        text=result["error"],
                        text_color="red", wraplength=180
                    )
                    err_label.grid(row=0, column=0, padx=8, pady=4, sticky="w")
                    self._chat_row_widgets.append(err_label)
                    self.status_label.configure(text="Error loading recent chats.")
                else:
                    convos = result.get("conversations", [])
                    if not convos:
                        empty = ctk.CTkLabel(
                            self.chat_list_frame,
                            text="No recent conversations found.",
                            text_color="gray"
                        )
                        empty.grid(row=0, column=0, padx=8, pady=8, sticky="w")
                        self._chat_row_widgets.append(empty)

                    for idx, convo in enumerate(convos):
                        self._add_chat_row(idx, convo)

                    self.status_label.configure(text=f"Loaded {len(convos)} recent conversations.")

                self.refresh_btn.configure(state="normal")

            self.after(0, _update_ui)

        threading.Thread(target=_fetch, daemon=True).start()


    def _add_chat_row(self, row_idx, convo):
        """Creates one clickable row in the recent-chats tower."""
        phone      = convo.get("phone", "Unknown")
        unread     = convo.get("unread_count", 0)

        display    = contact_book.get_display_name(phone, self._contacts)
        badge      = f"  🔴 {unread}" if unread > 0 else ""
        label      = f"{display}{badge}"

        row_frame = ctk.CTkFrame(self.chat_list_frame, fg_color="transparent")
        row_frame.grid(row=row_idx * 2, column=0, sticky="ew", padx=4, pady=(4, 0))
        row_frame.grid_columnconfigure(0, weight=1)

        # Main clickable button (name / phone)
        btn = ctk.CTkButton(
            row_frame,
            text=label,
            command=lambda p=phone: self._select_contact(p),
            anchor="w",
            fg_color="transparent",
            hover_color=("gray75", "gray30"),
            text_color=("#1a1a1a", "#ffffff"),
            font=ctk.CTkFont(size=12, weight="bold" if unread > 0 else "normal"),
            height=34
        )
        btn.grid(row=0, column=0, sticky="ew")

        # Inline ✏️ nickname edit button
        edit_btn = ctk.CTkButton(
            row_frame, text="✏️", width=28, height=28,
            fg_color="transparent", hover_color=("gray80", "gray25"),
            command=lambda p=phone, rf=row_frame, rb=btn: self._open_nickname_editor(p, rf, rb)
        )
        edit_btn.grid(row=0, column=1, padx=(0, 4))

        sep = ctk.CTkFrame(self.chat_list_frame, height=1, fg_color=("gray80", "gray30"))
        sep.grid(row=row_idx * 2 + 1, column=0, sticky="ew", padx=4)

        self._chat_row_widgets.extend([row_frame, sep])


    def _open_nickname_editor(self, phone, row_frame, main_btn):
        """Inline nickname editor that overlays the contact row."""
        # Get current nickname
        cur = self._contacts.get(phone, {}).get("nickname", "")

        edit_frame = ctk.CTkFrame(self.chat_list_frame)
        edit_frame.grid(row=main_btn.grid_info().get("row", 0), column=0,
                        columnspan=2, sticky="ew", padx=4)
        edit_frame.grid_columnconfigure(0, weight=1)
        self._chat_row_widgets.append(edit_frame)

        entry = ctk.CTkEntry(edit_frame, placeholder_text="Enter nickname...", height=28)
        entry.insert(0, cur)
        entry.grid(row=0, column=0, sticky="ew", padx=(4, 2), pady=4)
        add_context_menu(entry)

        def _save():
            new_nick = entry.get().strip()
            self._contacts = contact_book.set_nickname(phone, new_nick, self._contacts)
            display = contact_book.get_display_name(phone, self._contacts)
            main_btn.configure(text=display + (f"  🔴" if "🔴" in main_btn.cget("text") else ""))
            edit_frame.destroy()

        def _cancel():
            edit_frame.destroy()

        save_b = ctk.CTkButton(edit_frame, text="✓", width=28, height=28,
                               fg_color="#2da44e", hover_color="#2c974b", command=_save)
        save_b.grid(row=0, column=1, padx=2, pady=4)

        cancel_b = ctk.CTkButton(edit_frame, text="✕", width=28, height=28,
                                 fg_color="#c0392b", hover_color="#a93226", command=_cancel)
        cancel_b.grid(row=0, column=2, padx=(0, 4), pady=4)

        entry.focus()


    def _select_contact(self, phone):
        """Called when user clicks a contact row — updates state and loads history."""
        self._active_phone = phone
        display = contact_book.get_display_name(phone, self._contacts)
        header  = display if display != phone else phone
        self.active_contact_label.configure(
            text=f"📱 {header}", text_color=("black", "white")
        )
        # Pre-fill the nickname/receiver field with the best known name
        self.receiver_entry.delete(0, "end")
        self.receiver_entry.insert(0, display if display != phone else "")
        self.fetch_sms()


    # ══════════════════════════════════════════════════════════════════════════
    # FETCH SMS HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    def fetch_sms(self):
        cooldown = rate_limiter.get_remaining_cooldown(key="last_goto_pull", cooldown_seconds=rate_limiter.GOTO_COOLDOWN_SECONDS)
        if cooldown > 0:
            return

        phone = self._active_phone
        if not phone:
            self.status_label.configure(text="Select a contact from the left panel first.")
            return

        self.status_label.configure(text="Fetching SMS history...")
        self.fetch_btn.configure(state="disabled")

        def _fetch():
            gapi = goto_api.GoToAPI()
            messages = gapi.get_sms_history(phone)

            def _update_ui():
                if not self.winfo_exists():
                    return
                    
                self.history_text.configure(state="normal")
                self.history_text.delete("0.0", "end")

                for msg in messages:
                    body    = msg.get("body", "")
                    is_user = msg.get("is_user", False)

                    if body.startswith("Error") or body.startswith("No chat"):
                        self.history_text.insert("end", f"{body}\n", "system_msg")
                    elif is_user:
                        self.history_text.insert("end", "Me\n", "user_label")
                        self.history_text.insert("end", f"{body}\n\n", "user_body")
                    else:
                        name = self.receiver_entry.get().strip() or "Contact"
                        self.history_text.insert("end", f"{name}\n", "client_label")
                        self.history_text.insert("end", f"{body}\n\n", "client_body")

                self.history_text.configure(state="disabled")
                self.history_text._textbox.see("end")

                ok = messages and "Error" not in messages[0].get("body", "")
                self.status_label.configure(text="History loaded." if ok else "Error or empty history.")
                self.fetch_btn.configure(state="normal")

            self.after(0, _update_ui)

        threading.Thread(target=_fetch, daemon=True).start()


    # ══════════════════════════════════════════════════════════════════════════
    # EXPORT CHAT HISTORY
    # ══════════════════════════════════════════════════════════════════════════
    def export_history(self):
        history = self.history_text.get("0.0", "end").strip()
        phone   = self._active_phone

        if not history or history.startswith("Select a contact"):
            messagebox.showwarning("Export Warning", "No chat history to export.")
            return
        if history.startswith("Error"):
            messagebox.showwarning("Export Warning", "Cannot export history containing error messages.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"SMS_History_{phone.replace('+', '')}.md" if phone else "SMS_History.md",
            title="Export Chat History"
        )
        if file_path:
            try:
                receiver_name = self.receiver_entry.get().strip() or "Contact"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("# SMS Chat History\n\n")
                    if phone:
                        f.write(f"**Contact:** {phone}\n\n")
                    f.write("---\n\n")
                    lines = history.split("\n")
                    for line in lines:
                        stripped = line.strip()
                        if stripped in ("Me", receiver_name):
                            pass
                        elif line.startswith(receiver_name + ":") or line.startswith("Receiver:") or line.startswith("Client:"):
                            f.write(f"- **{receiver_name}**: {line.split(':', 1)[-1].strip()}\n")
                        elif line.startswith("Me:") or line.startswith("You:"):
                            f.write(f"- **Me**: {line.split(':', 1)[-1].strip()}\n")
                        elif stripped:
                            f.write(f"{line}\n")
                self.status_label.configure(text=f"Exported to {file_path}")
                messagebox.showinfo("Export Successful", f"History exported to:\n{file_path}")
            except Exception as e:
                self.status_label.configure(text=f"Export failed: {e}")
                messagebox.showerror("Export Error", f"Failed to export: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # AI REPLY GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    def generate_reply(self):
        if rate_limiter.get_remaining_cooldown() > 0:
            return

        history = self.history_text.get("0.0", "end").strip()
        intent  = self.intent_text.get("0.0", "end").strip()
        tone    = self.tone_var.get()

        if not intent:
            self.status_label.configure(text="Error: Enter your intent first.")
            return

        self.status_label.configure(text="Drafting reply via Gemini...")
        self.generate_btn.configure(state="disabled")

        def _generate():
            config   = config_manager.load_config()
            receiver = self.receiver_entry.get().strip() or "Contact"
            # ... keys ...
            free_key = config.get("gemini_api_key")
            paid_key = config.get("gemini_api_key_paid")
            use_paid = self.use_paid_var.get()

            reply     = ""
            used_paid = False

            if free_key:
                reply = gemini_ai.generate_reply(
                    free_key, history, tone, intent,
                    receiver_name=receiver,
                    custom_prompt=config.get("custom_prompt")
                )
            else:
                reply = "Error: Free Gemini API key is missing."

            if (not free_key or reply.startswith("Error")) and use_paid:
                if not paid_key:
                    reply = "Error: Paid Gemini API key is missing (Toggle is ON)."
                else:
                    self.after(0, lambda: self.status_label.configure(text="Free key failed, trying paid key..."))
                    reply = gemini_ai.generate_reply(
                        paid_key, history, tone, intent,
                        receiver_name=receiver,
                        custom_prompt=config.get("custom_prompt")
                    )
                    used_paid = not reply.startswith("Error")

            def _update_ui():
                if not self.winfo_exists():
                    return
                self.draft_text.delete("0.0", "end")
                self.draft_text.insert("0.0", reply)

                if not reply.startswith("Error"):
                    rate_limiter.record_ai_call()
                    self.status_label.configure(
                        text="Reply generated (PAID)." if used_paid else "Reply generated (Free)."
                    )
                else:
                    self.status_label.configure(text=f"Generation failed: {reply[:60]}...")

                self.generate_btn.configure(state="normal")

            self.after(0, _update_ui)

        threading.Thread(target=_generate, daemon=True).start()


    # ══════════════════════════════════════════════════════════════════════════
    # SEND SMS
    # ══════════════════════════════════════════════════════════════════════════
    def send_sms(self):
        phone   = self._active_phone
        message = self.draft_text.get("0.0", "end").strip()

        if not phone or not message:
            self.status_label.configure(text="Error: No contact selected or draft is empty.")
            return

        self.status_label.configure(text=f"Sending SMS to {phone}...")
        self.send_btn.configure(state="disabled")

        def _send():
            gapi = goto_api.GoToAPI()
            res  = gapi.send_sms(phone, message)
            
            def _update_ui():
                if not self.winfo_exists():
                    return
                if res:
                    self.status_label.configure(text="SMS Sent Successfully!")
                    self.draft_text.delete("0.0", "end")
                    self.intent_text.delete("0.0", "end")
                else:
                    self.status_label.configure(text="Failed to send SMS.")
                self.send_btn.configure(state="normal")

            self.after(0, _update_ui)

        threading.Thread(target=_send, daemon=True).start()
