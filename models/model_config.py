from models.database import db
from cryptography.fernet import Fernet
import json

class ModelConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)  # openai, azure, doubao
    api_key = db.Column(db.String(500), nullable=False)
    api_base = db.Column(db.String(200))
    model_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='inactive')  # active, inactive
    parameters = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def __init__(self, name, model_type, api_key, model_name, api_base=None, parameters=None):
        self.name = name
        self.model_type = model_type
        self.api_key = self._encrypt_api_key(api_key)
        self.model_name = model_name
        self.api_base = api_base
        self.parameters = json.dumps(parameters) if parameters else None

    def _encrypt_api_key(self, api_key):
        key = Fernet.generate_key()
        f = Fernet(key)
        encrypted_key = f.encrypt(api_key.encode())
        return f"{key.decode()}:{encrypted_key.decode()}"

    def get_api_key(self):
        key_part, encrypted_key = self.api_key.split(':')
        f = Fernet(key_part.encode())
        return f.decrypt(encrypted_key.encode()).decode()

    def get_parameters(self):
        return json.loads(self.parameters) if self.parameters else {}