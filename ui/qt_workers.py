from PySide6.QtCore import Signal
from modules import goto_api, gemini_ai, contact_book, ollama_ai, config_manager, rate_limiter
from ui.thread_manager import BaseWorker

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
    reply_generated = Signal(str, str) # reply, source ('Free', 'Ollama', 'PAID')
    waterfall_status = Signal(str)

    def __init__(self, history, intent, tone, receiver, use_paid):
        super().__init__()
        self.history = history
        self.intent = intent
        self.tone = tone
        self.receiver = receiver
        self.use_paid = use_paid

    def _do_work(self):
        config = config_manager.load_config()
        free_key = config.get("gemini_api_key")
        paid_key = config.get("gemini_api_key_paid")
        custom_prompt = config.get("custom_prompt")

        def try_models(key, source_name):
            self.status.emit(f"Fetching models for {source_name} key...")
            models = gemini_ai.get_sorted_models(key)
            if not models:
                self.waterfall_status.emit(f"No valid models found for {source_name} key.\n")
                return None
            
            for m in models:
                self.waterfall_status.emit(f"Attempting {m} ({source_name})...\n")
                reply = gemini_ai.generate_reply(
                    key, self.history, self.tone, self.intent,
                    receiver_name=self.receiver, custom_prompt=custom_prompt, model=m
                )
                if not reply.startswith("Error"):
                    self.waterfall_status.emit(f"Success with {m}!\n")
                    return reply
                self.waterfall_status.emit(f"Failed ({m}). Reason: {reply[:80]}...\n")
            return None

        if free_key:
            reply = try_models(free_key, "Free")
            if reply:
                self.reply_generated.emit(reply, "Free")
                self.finished.emit()
                return
        else:
            self.waterfall_status.emit("Free Gemini API key is missing.\n")

        if self.use_paid:
            self.status.emit("Free key failed/missing, checking Ollama...")
            self.waterfall_status.emit("Free models failed/missing. Checking local Ollama...\n")
            
            if ollama_ai.is_ollama_available():
                self.status.emit("Ollama found, generating...")
                self.waterfall_status.emit("Attempting local Ollama...\n")
                reply = ollama_ai.generate_reply(
                    self.history, self.tone, self.intent,
                    receiver_name=self.receiver, custom_prompt=custom_prompt
                )
                if not reply.startswith("Error"):
                    self.waterfall_status.emit("Success with Ollama!\n")
                    self.reply_generated.emit(reply, "Ollama")
                    self.finished.emit()
                    return
                self.waterfall_status.emit(f"Ollama failed. Reason: {reply[:80]}...\n")

            if not paid_key:
                self.waterfall_status.emit("Ollama unavailable and Paid Gemini key is missing.\n")
            else:
                self.status.emit("Ollama unavailable/failed, trying paid key...")
                self.waterfall_status.emit("Trying Paid Gemini key models...\n")
                
                reply = try_models(paid_key, "PAID")
                if reply:
                    self.reply_generated.emit(reply, "PAID")
                    self.finished.emit()
                    return

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
