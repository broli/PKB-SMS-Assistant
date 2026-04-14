import customtkinter as ctk
import threading
from tkinter import filedialog, messagebox
from ui.settings_window import SettingsWindow
from ui.utils import add_context_menu
from modules import config_manager, rate_limiter, goto_api, gemini_ai

class MainWindow(ctk.CTk):
    def __init__(self, version=""):
        super().__init__()
        title = f"GoTo SMS AI Assistant v{version}" if version else "GoTo SMS AI Assistant"
        self.title(title)
        self.geometry("850x650")
        
        # Grid layout (2 columns)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        
        # Header
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        self.header_label = ctk.CTkLabel(self.header_frame, text="💬 GoTo SMS AI Assistant", font=ctk.CTkFont(size=20, weight="bold"))
        self.header_label.pack(side="left", padx=10, pady=10)
        self.settings_btn = ctk.CTkButton(self.header_frame, text="⚙️ Settings", command=self.open_settings, width=100)
        self.settings_btn.pack(side="right", padx=10, pady=10)
        
        # Left Column - Chat & Fetch
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=10, pady=(0, 10))
        
        self.phone_label = ctk.CTkLabel(self.left_frame, text="Contact Phone Number:")
        self.phone_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.phone_entry = ctk.CTkEntry(self.left_frame, placeholder_text="+1234567890")
        self.phone_entry.pack(fill="x", padx=10, pady=5)
        add_context_menu(self.phone_entry)
        
        self.receiver_label = ctk.CTkLabel(self.left_frame, text="Receiver Name (optional):")
        self.receiver_label.pack(anchor="w", padx=10, pady=(4, 0))
        self.receiver_entry = ctk.CTkEntry(self.left_frame, placeholder_text="e.g. Cathleen, Lead, Client...")
        self.receiver_entry.pack(fill="x", padx=10, pady=(2, 5))
        add_context_menu(self.receiver_entry)
        
        self.fetch_btn = ctk.CTkButton(self.left_frame, text="Fetch SMS History", command=self.fetch_sms)
        self.fetch_btn.pack(fill="x", padx=10, pady=5)
        
        self.export_btn = ctk.CTkButton(self.left_frame, text="📥 Export Chat History", command=self.export_history, fg_color="#34495e", hover_color="#2c3e50")
        self.export_btn.pack(fill="x", padx=10, pady=5)
        
        self.history_label = ctk.CTkLabel(self.left_frame, text="Chat History:")
        self.history_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.history_text = ctk.CTkTextbox(self.left_frame, wrap="word")
        self.history_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.history_text.insert("0.0", "Enter a phone number and click Fetch to see history...")
        self.history_text.configure(state="disabled")
        add_context_menu(self.history_text)
        
        # Configure chat tags via internal textbox
        # No background colors - rely on alignment + label color for distinction
        inner_text = self.history_text._textbox
        inner_text.tag_config("user_label",   justify="right",  foreground="#4caf50")  # Green for "You:"
        inner_text.tag_config("user_body",    justify="right",  foreground="#ffffff")  # White body, right
        inner_text.tag_config("client_label", justify="left",   foreground="#90caf9")  # Light blue for "Client:"
        inner_text.tag_config("client_body",  justify="left",   foreground="#dddddd")  # Light gray body, left
        inner_text.tag_config("system_msg",   justify="center", foreground="#888888")  # Gray for errors/info
        
        # Right Column - AI Generation & Send
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=1, column=1, rowspan=2, sticky="nsew", padx=(0, 10), pady=(0, 10))
        
        self.tone_label = ctk.CTkLabel(self.right_frame, text="Desired Tone:")
        self.tone_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.tone_var = ctk.StringVar(value="Professional")
        self.tone_combo = ctk.CTkComboBox(self.right_frame, values=["Professional", "Casual", "Empathetic", "Direct", "Apologetic"], variable=self.tone_var)
        self.tone_combo.pack(fill="x", padx=10, pady=5)
        
        self.intent_label = ctk.CTkLabel(self.right_frame, text="What do you want to say? (Intent):")
        self.intent_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.intent_text = ctk.CTkTextbox(self.right_frame, height=80, wrap="word")
        self.intent_text.pack(fill="x", padx=10, pady=5)
        add_context_menu(self.intent_text)
        
        self.generate_btn = ctk.CTkButton(self.right_frame, text="✨ Generate AI Reply", command=self.generate_reply)
        self.generate_btn.pack(fill="x", padx=10, pady=15)
        
        self.draft_label = ctk.CTkLabel(self.right_frame, text="Draft Reply (Editable):")
        self.draft_label.pack(anchor="w", padx=10, pady=(10, 0))
        self.draft_text = ctk.CTkTextbox(self.right_frame, wrap="word")
        self.draft_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        add_context_menu(self.draft_text)
        
        self.send_btn = ctk.CTkButton(self.right_frame, text="Send SMS", command=self.send_sms, fg_color="#2da44e", hover_color="#2c974b") # Green theme
        self.send_btn.pack(fill="x", padx=10, pady=(5, 10))
        
        # Status Bar Frame
        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self.status_frame, text="Ready", anchor="w")
        self.status_label.grid(row=0, column=0, sticky="w")
        
        self.cooldown_label = ctk.CTkLabel(self.status_frame, text="AI: 0s | GoTo: 0s", anchor="e", font=ctk.CTkFont(family="Consolas", size=12))
        self.cooldown_label.grid(row=0, column=1, sticky="e")

        # Start Cooldown Monitor
        self._update_cooldown_monitor()

    def _update_cooldown_monitor(self):
        """Background loop to update the cooldown label every second."""
        ai_cd = rate_limiter.get_remaining_cooldown(key="last_ai_call", cooldown_seconds=rate_limiter.AI_COOLDOWN_SECONDS)
        goto_cd = rate_limiter.get_remaining_cooldown(key="last_goto_pull", cooldown_seconds=rate_limiter.GOTO_COOLDOWN_SECONDS)
        
        self.cooldown_label.configure(text=f"AI: {ai_cd}s | GoTo: {goto_cd}s")
        
        # Color code the monitor if active
        if ai_cd > 0 or goto_cd > 0:
            self.cooldown_label.configure(text_color="#f1c40f") # Yellow
        else:
            self.cooldown_label.configure(text_color="gray")
            
        self.after(1000, self._update_cooldown_monitor)

    def open_settings(self):
        SettingsWindow(self)
        
    def fetch_sms(self):
        # Rate limit check for GoTo API (30 seconds)
        cooldown = rate_limiter.get_remaining_cooldown(key="last_goto_pull", cooldown_seconds=rate_limiter.GOTO_COOLDOWN_SECONDS)
        if cooldown > 0:
            # No longer setting status text here as it's in the monitor
            return

        phone = self.phone_entry.get().strip()
        if not phone:
            self.status_label.configure(text="Error: Enter a phone number first.")
            return
            
        self.status_label.configure(text="Fetching SMS history...")
        self.fetch_btn.configure(state="disabled")
        
        def _fetch():
            gapi = goto_api.GoToAPI()
            messages = gapi.get_sms_history(phone)
            
            self.history_text.configure(state="normal")
            self.history_text.delete("0.0", "end")
            
            for msg in messages:
                body = msg.get("body", "")
                is_user = msg.get("is_user", False)
                
                label = "You" if is_user else "Client"
                tag = "user_msg" if is_user else "client_msg"
                
                if body.startswith("Error") or body.startswith("No chat"):
                    self.history_text.insert("end", f"{body}\n", "system_msg")
                elif is_user:
                    self.history_text.insert("end", "Me\n", "user_label")
                    self.history_text.insert("end", f"{body}\n\n", "user_body")
                else:
                    receiver_name = self.receiver_entry.get().strip() or "Contact"
                    self.history_text.insert("end", f"{receiver_name}\n", "client_label")
                    self.history_text.insert("end", f"{body}\n\n", "client_body")
                
            self.history_text.configure(state="disabled")
            self.history_text._textbox.see("end")
            
            # Simple check if the first item was a success message
            if messages and "Error" not in messages[0].get("body", ""):
                self.status_label.configure(text="History loaded.")
            else:
                self.status_label.configure(text="Error or empty history.")
            self.fetch_btn.configure(state="normal")
            
        threading.Thread(target=_fetch, daemon=True).start()

    def export_history(self):
        history = self.history_text.get("0.0", "end").strip()
        phone = self.phone_entry.get().strip()
        
        if not history or history == "Enter a phone number and click Fetch to see history...":
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
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"# SMS Chat History\n\n")
                    if phone:
                        f.write(f"**Contact:** {phone}\n\n")
                    f.write("---\n\n")
                    
                    # Use receiver name in export if provided
                    receiver_name = self.receiver_entry.get().strip() or "Contact"
                    lines = history.split("\n")
                    for line in lines:
                        # Match either "Me" label lines or receiver name label lines
                        stripped = line.strip()
                        if stripped == "Me":
                            pass  # label-only line, skip
                        elif stripped == receiver_name:
                            pass  # label-only line, skip
                        elif line.startswith(receiver_name + ":") or line.startswith("Receiver:") or line.startswith("Client:"):
                            f.write(f"- **{receiver_name}**: {line.split(':', 1)[-1].strip()}\n")
                        elif line.startswith("Me:") or line.startswith("You:"):
                            f.write(f"- **Me**: {line.split(':', 1)[-1].strip()}\n")
                        elif stripped:
                            f.write(f"{line}\n")
                            
                self.status_label.configure(text=f"History exported to {file_path}")
                messagebox.showinfo("Export Successful", f"History exported successfully to:\n{file_path}")
            except Exception as e:
                self.status_label.configure(text=f"Export failed: {e}")
                messagebox.showerror("Export Error", f"Failed to export history: {e}")

    def generate_reply(self):
        cooldown = rate_limiter.get_remaining_cooldown()
        if cooldown > 0:
            return
            
        history = self.history_text.get("0.0", "end").strip()
        intent = self.intent_text.get("0.0", "end").strip()
        tone = self.tone_var.get()
        
        if not intent:
            self.status_label.configure(text="Error: Enter your intent first.")
            return
            
        self.status_label.configure(text="Drafting reply via Gemini...")
        self.generate_btn.configure(state="disabled")
        
        def _generate():
            config = config_manager.load_config()
            receiver_name = self.receiver_entry.get().strip() or "Contact"
            reply = gemini_ai.generate_reply(
                config.get("gemini_api_key"), 
                history, 
                tone, 
                intent,
                receiver_name=receiver_name,
                custom_prompt=config.get("custom_prompt")
            )
            
            self.draft_text.delete("0.0", "end")
            self.draft_text.insert("0.0", reply)
            
            if not reply.startswith("Error"):
                rate_limiter.record_ai_call()
                self.status_label.configure(text="Reply generated. Review before sending.")
            else:
                self.status_label.configure(text="Error generating reply.")
                
            self.generate_btn.configure(state="normal")

        threading.Thread(target=_generate, daemon=True).start()

    def send_sms(self):
        phone = self.phone_entry.get().strip()
        message = self.draft_text.get("0.0", "end").strip()
        
        if not phone or not message:
            self.status_label.configure(text="Error: Phone number or draft message is empty.")
            return
            
        self.status_label.configure(text=f"Sending SMS to {phone}...")
        self.send_btn.configure(state="disabled")
        
        def _send():
            gapi = goto_api.GoToAPI()
            res = gapi.send_sms(phone, message)
            
            if res:
                self.status_label.configure(text="SMS Sent Successfully!")
                self.draft_text.delete("0.0", "end")
                self.intent_text.delete("0.0", "end")
            else:
                self.status_label.configure(text="Failed to send SMS.")
                
            self.send_btn.configure(state="normal")
            
        threading.Thread(target=_send, daemon=True).start()
