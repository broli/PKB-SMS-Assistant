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

class GenerateReplyWorker(BaseWorker):
    reply_generated = Signal(str, str) # reply, source ('Free', 'Ollama', 'PAID')

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

        if free_key:
            reply = gemini_ai.generate_reply(
                free_key, self.history, self.tone, self.intent,
                receiver_name=self.receiver, custom_prompt=custom_prompt
            )
            if not reply.startswith("Error"):
                self.reply_generated.emit(reply, "Free")
                self.finished.emit()
                return
        else:
            self.error.emit("Free Gemini API key is missing.")
            self.finished.emit()
            return

        if self.use_paid:
            self.status.emit("Free key failed, checking Ollama...")
            if ollama_ai.is_ollama_available():
                self.status.emit("Ollama found, generating...")
                reply = ollama_ai.generate_reply(
                    self.history, self.tone, self.intent,
                    receiver_name=self.receiver, custom_prompt=custom_prompt
                )
                if not reply.startswith("Error"):
                    self.reply_generated.emit(reply, "Ollama")
                    self.finished.emit()
                    return

            if not paid_key:
                self.error.emit("Ollama unavailable and Paid Gemini key is missing.")
                self.finished.emit()
                return
            else:
                self.status.emit("Ollama unavailable/failed, trying paid key...")
                reply = gemini_ai.generate_reply(
                    paid_key, self.history, self.tone, self.intent,
                    receiver_name=self.receiver, custom_prompt=custom_prompt
                )
                if not reply.startswith("Error"):
                    self.reply_generated.emit(reply, "PAID")
                    self.finished.emit()
                    return

        self.error.emit("Failed to generate reply.")
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
