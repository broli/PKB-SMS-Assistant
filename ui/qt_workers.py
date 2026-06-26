from PySide6.QtCore import Signal, QMetaObject, Qt, QCoreApplication, QObject, Slot
from modules import goto_api, gemini_ai, contact_book, ollama_ai, config_manager, rate_limiter
from ui.thread_manager import BaseWorker

class _AuthInvoker(QObject):
    def __init__(self):
        super().__init__()
        self.success = False

    @Slot()
    def run_dialog(self):
        try:
            import corporate_secrets
            from ui.auth_window import MSAuthWindow
            from modules import config_manager
            
            # Note: corporate_secrets should have AUTH_DOWNLOAD_URL and DECRYPTION_KEY
            auth_url = getattr(corporate_secrets, 'AUTH_DOWNLOAD_URL', None)
            dec_key = getattr(corporate_secrets, 'DECRYPTION_KEY', None)
            
            if not auth_url or not dec_key:
                import logging
                logging.error("Missing AUTH_DOWNLOAD_URL or DECRYPTION_KEY in corporate_secrets.py")
                return
                
            dialog = MSAuthWindow(auth_url, dec_key)
            
            def on_config(config_data):
                if "gemini_api_key" in config_data:
                    config_manager.set_runtime_override("gemini_api_key", config_data["gemini_api_key"])
                if "m365_client_id" in config_data:
                    config_manager.set_runtime_override("m365_client_id", config_data["m365_client_id"])
                if "m365_tenant_id" in config_data:
                    config_manager.set_runtime_override("m365_tenant_id", config_data["m365_tenant_id"])
                self.success = True
                
            dialog.config_retrieved.connect(on_config)
            dialog.exec()
            
            # Safely schedule deletion of QWebEngine components to prevent memory corruption
            if hasattr(dialog, 'browser'):
                if dialog.browser.page():
                    dialog.browser.page().deleteLater()
                dialog.browser.deleteLater()
            if hasattr(dialog, 'profile'):
                dialog.profile.deleteLater()
            dialog.deleteLater()
        except Exception as e:
            import logging
            logging.error(f"Failed to show auth dialog: {e}")

def trigger_auth_on_main_thread():
    """
    Safely pauses the background worker and executes the MS Auth dialog on the main UI thread.
    Returns True if authentication was successful and secrets were loaded into memory.
    """
    app = QCoreApplication.instance()
    if not app:
        return False
        
    invoker = _AuthInvoker()
    invoker.moveToThread(app.thread())
    QMetaObject.invokeMethod(invoker, "run_dialog", Qt.BlockingQueuedConnection)
    return invoker.success


class FetchRecentChatsWorker(BaseWorker):
    data_fetched = Signal(dict)

    def __init__(self):
        super().__init__()

    def _do_work(self):
        gapi = goto_api.GoToAPI()
        result = gapi.get_recent_conversations()
        self.data_fetched.emit(result)
        self.finished.emit() # Signal thread to quit

class FetchSMSWorker(BaseWorker):
    data_fetched = Signal(list)

    def __init__(self, phone):
        super().__init__()
        self.phone = phone

    def _do_work(self):
        gapi = goto_api.GoToAPI()
        messages = gapi.get_sms_history(self.phone)
        self.data_fetched.emit(messages)
        self.finished.emit() # Signal thread to quit

class CheckGeminiKeyWorker(BaseWorker):
    models_fetched = Signal(list)

    def __init__(self, api_key):
        super().__init__()
        self.api_key = api_key

    def _do_work(self):
        if not self.api_key:
            self.error.emit("API key is empty.")
            return
            
        models = gemini_ai.get_sorted_models(self.api_key)
        if not models:
            self.error.emit("Key invalid or no supported models found.")
        else:
            self.models_fetched.emit(models)
        self.finished.emit()

class GenerateReplyWorker(BaseWorker):
    reply_generated = Signal(str, str) # reply, source ('Gemini', 'Ollama')
    waterfall_status = Signal(str)

    def __init__(self, history, intent, tone, receiver):
        super().__init__()
        self.history = history
        self.intent = intent
        self.tone = tone
        self.receiver = receiver

    def _do_work(self):
        config = config_manager.load_config()
        api_key = config.get("gemini_api_key")
        
        if not api_key:
            self.status.emit("Gemini key missing. Triggering auth callback...")
            if trigger_auth_on_main_thread():
                api_key = config_manager._RUNTIME_OVERRIDES.get("gemini_api_key", "")
                
        custom_prompt = config.get("custom_prompt")

        def try_models(key):
            self.status.emit(f"Fetching Gemini models...")
            models = gemini_ai.get_sorted_models(key)
            if not models:
                self.waterfall_status.emit(f"No valid models found for Gemini key.\n")
                return None
            
            for m in models:
                self.waterfall_status.emit(f"Attempting {m}...\n")
                reply = gemini_ai.generate_reply(
                    key, self.history, self.tone, self.intent,
                    receiver_name=self.receiver, custom_prompt=custom_prompt, model=m
                )
                if reply and not reply.startswith("Error"):
                    self.waterfall_status.emit(f"Success with {m}!\n")
                    return reply
                reason = reply[:80] if reply else "No reply"
                self.waterfall_status.emit(f"Failed ({m}). Reason: {reason}...\n")
            return None

        if api_key:
            reply = try_models(api_key)
            if reply:
                self.reply_generated.emit(reply, "Gemini")
                self.finished.emit()
                return
        else:
            self.waterfall_status.emit("Gemini API key is missing.\n")

        self.status.emit("Gemini key failed/missing, checking Ollama...")
        self.waterfall_status.emit("Gemini models failed/missing. Checking local Ollama...\n")
        
        if ollama_ai.is_ollama_available():
            self.status.emit("Ollama found, generating...")
            self.waterfall_status.emit("Attempting local Ollama...\n")
            reply = ollama_ai.generate_reply(
                self.history, self.tone, self.intent,
                receiver_name=self.receiver, custom_prompt=custom_prompt
            )
            if reply and not reply.startswith("Error"):
                self.waterfall_status.emit("Success with Ollama!\n")
                self.reply_generated.emit(reply, "Ollama")
                self.finished.emit()
                return
            reason = reply[:80] if reply else "No reply"
            self.waterfall_status.emit(f"Ollama failed. Reason: {reason}...\n")
        else:
            self.waterfall_status.emit("Ollama unavailable.\n")

        self.error.emit("Failed to generate reply using any available models.")
        self.finished.emit()

class SendSMSWorker(BaseWorker):
    sms_sent = Signal(bool)

    def __init__(self, phone, message):
        super().__init__()
        self.phone = phone
        self.message = message

    def _do_work(self):
        gapi = goto_api.GoToAPI()
        res = gapi.send_sms(self.phone, self.message)
        self.sms_sent.emit(res)
        self.finished.emit()

class OAuthLoginWorker(BaseWorker):
    login_complete = Signal(bool)

    def __init__(self):
        super().__init__()

    def _do_work(self):
        from modules.auth_handler import start_oauth_flow
        success = start_oauth_flow()
        self.login_complete.emit(success)
        self.finished.emit()

class AnalyzeIntentWorker(BaseWorker):
    intent_analyzed = Signal(str, dict)

    def __init__(self, api_key, message, contact_name, phone, timezone="Local"):
        super().__init__()
        self.api_key = api_key
        self.message = message
        self.contact_name = contact_name
        self.phone = phone
        self.timezone = timezone

    def _do_work(self):
        from modules.intent_analyzer import analyze_sms_intent
        
        if not self.api_key:
            self.status.emit("Gemini key missing. Triggering auth callback...")
            if trigger_auth_on_main_thread():
                self.api_key = config_manager._RUNTIME_OVERRIDES.get("gemini_api_key", "")
        
        self.status.emit("AI analyzing commitment...")
        intent_data = analyze_sms_intent(self.api_key, self.message, self.contact_name, timezone=self.timezone)
        intent_data["_timezone"] = self.timezone
        
        self.intent_analyzed.emit(self.phone, intent_data)
        self.finished.emit()

class AnalyzeChatHistoryWorker(BaseWorker):
    intent_analyzed = Signal(str, dict)

    def __init__(self, api_key, chat_history, contact_name, phone, timezone="Local"):
        super().__init__()
        self.api_key = api_key
        self.chat_history = chat_history
        self.contact_name = contact_name
        self.phone = phone
        self.timezone = timezone

    def _do_work(self):
        from modules.intent_analyzer import analyze_chat_history_intent
        
        if not self.api_key:
            self.status.emit("Gemini key missing. Triggering auth callback...")
            if trigger_auth_on_main_thread():
                self.api_key = config_manager._RUNTIME_OVERRIDES.get("gemini_api_key", "")
        
        self.status.emit("AI scanning history for commitments...")
        intent_data = analyze_chat_history_intent(self.api_key, self.chat_history, self.contact_name, timezone=self.timezone)
        intent_data["_timezone"] = self.timezone
        
        self.intent_analyzed.emit(self.phone, intent_data)
        self.finished.emit()

class SyncCalendarWorker(BaseWorker):
    sync_complete = Signal(bool, str)

    def __init__(self, intent_data):
        super().__init__()
        self.intent_data = intent_data

    def _do_work(self):
        from modules.calendar_sync import EvolutionProvider, M365Provider
        from modules import config_manager
        from datetime import datetime

        self.status.emit("Syncing to calendar...")
        config = config_manager.load_config()
        provider_name = config.get("calendar_provider", "Microsoft 365")
        
        if provider_name == "Microsoft 365":
            client_id = config.get("m365_client_id", "")
            tenant_id = config.get("m365_tenant_id", "")
            provider = M365Provider(client_id, tenant_id, auth_callback=trigger_auth_on_main_thread)
        else:
            provider = EvolutionProvider()
        
        try:
            summary = self.intent_data.get("summary", "New Action from SMS")
            
            if self.intent_data.get("type") == "event":
                start_str = self.intent_data.get("start_time")
                end_str = self.intent_data.get("end_time")
                
                start_time = datetime.fromisoformat(start_str) if start_str else datetime.now()
                end_time = datetime.fromisoformat(end_str) if end_str else None
                
                success = provider.add_event(summary, start_time, end_time, self.intent_data.get("_timezone", "Local"))
                msg = f"Event added: {summary}"
            else:
                due_str = self.intent_data.get("due_date")
                due_date = datetime.fromisoformat(due_str) if due_str else None
                
                success = provider.add_task(summary, due_date, self.intent_data.get("_timezone", "Local"))
                msg = f"Task added: {summary}"

            self.sync_complete.emit(success, msg if success else "Failed to add to calendar.")
        except Exception as e:
            self.sync_complete.emit(False, str(e))
            
        self.finished.emit()
