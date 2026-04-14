import customtkinter as ctk
import threading
from modules import config_manager
from modules.gemini_ai import DEFAULT_PROMPT
from modules.auth_handler import start_oauth_flow
from ui.utils import add_context_menu

class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Settings - API Keys & Prompts")
        self.geometry("600x650")
        
        # Attempt to make it modal and stay on top
        self.attributes('-topmost', 1)
        self.grab_set()
        
        self.config = config_manager.load_config()
        
        # Main Scrollable Frame
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        self.title_label = ctk.CTkLabel(self.scroll_frame, text="Configure Assistant Settings", font=ctk.CTkFont(size=18, weight="bold"))
        self.title_label.pack(pady=15)
        
        # GoTo OAuth Login
        self.login_frame = ctk.CTkFrame(self.scroll_frame)
        self.login_frame.pack(fill="x", padx=20, pady=5)
        
        has_token = bool(self.config.get("access_token"))
        status_text = "Status: Logged In" if has_token else "Status: Not Logged In"
        self.login_status = ctk.CTkLabel(self.login_frame, text=status_text)
        self.login_status.pack(side="left", padx=10, pady=10)
        
        self.login_button = ctk.CTkButton(self.login_frame, text="Login with GoTo", command=self.do_login)
        self.login_button.pack(side="right", padx=10, pady=10)
        
        # GoTo Phone Number
        self.phone_var = ctk.StringVar(value=self.config.get("goto_phone", ""))
        self.phone_label = ctk.CTkLabel(self.scroll_frame, text="GoTo Account Phone Number (From):")
        self.phone_label.pack(anchor="w", padx=20, pady=(10,0))
        self.phone_entry = ctk.CTkEntry(self.scroll_frame, textvariable=self.phone_var, width=500, placeholder_text="+1234567890")
        self.phone_entry.pack(padx=20, pady=5)
        add_context_menu(self.phone_entry)
        
        # Gemini API Key
        self.gemini_var = ctk.StringVar(value=self.config.get("gemini_api_key", ""))
        self.gemini_label = ctk.CTkLabel(self.scroll_frame, text="Gemini API Key:")
        self.gemini_label.pack(anchor="w", padx=20, pady=(10,0))
        self.gemini_entry = ctk.CTkEntry(self.scroll_frame, textvariable=self.gemini_var, show="*", width=500)
        self.gemini_entry.pack(padx=20, pady=5)
        add_context_menu(self.gemini_entry)
        
        # AI Custom Prompt
        self.prompt_label = ctk.CTkLabel(self.scroll_frame, text="Custom AI System Prompt:")
        self.prompt_label.pack(anchor="w", padx=20, pady=(15,0))
        
        self.prompt_text = ctk.CTkTextbox(self.scroll_frame, height=200, width=500)
        self.prompt_text.pack(padx=20, pady=10)
        
        current_prompt = self.config.get("custom_prompt") or DEFAULT_PROMPT
        self.prompt_text.insert("0.0", current_prompt)
        add_context_menu(self.prompt_text)
        
        self.reset_button = ctk.CTkButton(self.scroll_frame, text="Reset to Default Prompt", command=self.reset_prompt, fg_color="#34495e", hover_color="#2c3e50")
        self.reset_button.pack(padx=20, pady=5)
        
        # Save Button
        self.save_button = ctk.CTkButton(self, text="Save Settings", command=self.save_settings)
        self.save_button.pack(pady=20)
        
    def reset_prompt(self):
        self.prompt_text.delete("0.0", "end")
        self.prompt_text.insert("0.0", DEFAULT_PROMPT)

    def do_login(self):
        self.login_button.configure(state="disabled", text="Waiting in browser...")
        # Start OAuth flow in a background thread so UI doesn't freeze
        def login_thread():
            success = start_oauth_flow()
            # update UI
            self.after(0, self.on_login_complete, success)
        threading.Thread(target=login_thread, daemon=True).start()

    def on_login_complete(self, success):
        if not self.winfo_exists():
            return
        self.login_button.configure(state="normal", text="Login with GoTo")
        if success:
            self.login_status.configure(text="Status: Logged In", text_color="green")
            # Reload config since auth handler saved the new tokens
            self.config = config_manager.load_config()
        else:
            self.login_status.configure(text="Status: Login Failed", text_color="red")
            
    def save_settings(self):
        new_config = {
            "access_token": self.config.get("access_token", ""),
            "refresh_token": self.config.get("refresh_token", ""),
            "goto_phone": self.phone_var.get(),
            "gemini_api_key": self.gemini_var.get(),
            "custom_prompt": self.prompt_text.get("0.0", "end").strip()
        }
        config_manager.save_config(new_config)
        self.destroy()
