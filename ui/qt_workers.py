from PySide6.QtCore import QThread, Signal
from modules import goto_api, gemini_ai, contact_book, ollama_ai, config_manager, rate_limiter

class FetchRecentChatsWorker(QThread):
    finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            gapi = goto_api.GoToAPI()
            result = gapi.get_recent_conversations()
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({"error": str(e)})

class FetchSMSWorker(QThread):
    finished = Signal(list)

    def __init__(self, phone, parent=None):
        super().__init__(parent)
        self.phone = phone

    def run(self):
        try:
            gapi = goto_api.GoToAPI()
            messages = gapi.get_sms_history(self.phone)
            self.finished.emit(messages)
        except Exception as e:
            self.finished.emit([{"body": f"Error: {str(e)}", "is_user": False}])

class GenerateReplyWorker(QThread):
    finished = Signal(str, str) # reply, source ('Free', 'Ollama', 'PAID', 'Error')
    status_update = Signal(str)

    def __init__(self, history, intent, tone, receiver, use_paid, parent=None):
        super().__init__(parent)
        self.history = history
        self.intent = intent
        self.tone = tone
        self.receiver = receiver
        self.use_paid = use_paid

    def run(self):
        try:
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
                    self.finished.emit(reply, "Free")
                    return
            else:
                reply = "Error: Free Gemini API key is missing."

            if self.use_paid:
                self.status_update.emit("Free key failed, checking Ollama...")
                if ollama_ai.is_ollama_available():
                    self.status_update.emit("Ollama found, generating...")
                    reply = ollama_ai.generate_reply(
                        self.history, self.tone, self.intent,
                        receiver_name=self.receiver, custom_prompt=custom_prompt
                    )
                    if not reply.startswith("Error"):
                        self.finished.emit(reply, "Ollama")
                        return

                if not paid_key:
                    self.finished.emit("Error: Ollama unavailable and Paid Gemini key is missing.", "Error")
                    return
                else:
                    self.status_update.emit("Ollama unavailable/failed, trying paid key...")
                    reply = gemini_ai.generate_reply(
                        paid_key, self.history, self.tone, self.intent,
                        receiver_name=self.receiver, custom_prompt=custom_prompt
                    )
                    if not reply.startswith("Error"):
                        self.finished.emit(reply, "PAID")
                        return

            self.finished.emit(reply, "Error")

        except Exception as e:
            self.finished.emit(f"Error: {str(e)}", "Error")

class SendSMSWorker(QThread):
    finished = Signal(bool)

    def __init__(self, phone, message, parent=None):
        super().__init__(parent)
        self.phone = phone
        self.message = message

    def run(self):
        try:
            gapi = goto_api.GoToAPI()
            res = gapi.send_sms(self.phone, self.message)
            self.finished.emit(res)
        except Exception:
            self.finished.emit(False)

class OAuthLoginWorker(QThread):
    finished = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        from modules.auth_handler import start_oauth_flow
        success = start_oauth_flow()
        self.finished.emit(success)
