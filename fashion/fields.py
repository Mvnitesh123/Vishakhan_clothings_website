import base64
from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet

# Derive a secure 32-byte key from settings.SECRET_KEY if not explicitly defined
key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
if not key:
    secret = settings.SECRET_KEY.encode('utf-8')
    if len(secret) < 32:
        secret = secret.ljust(32, b'0')
    key = base64.urlsafe_b64encode(secret[:32]).decode('utf-8')

fernet = Fernet(key.encode('utf-8'))

def encrypt_value(value: str) -> str:
    if not value or not isinstance(value, str):
        return value
    return fernet.encrypt(value.encode('utf-8')).decode('utf-8')

def decrypt_value(value: str) -> str:
    if not value or not isinstance(value, str):
        return value
    # Check if it looks like a Fernet token (usually starts with gAAAA)
    if not value.startswith('gAAAA'):
        return value
    try:
        return fernet.decrypt(value.encode('utf-8')).decode('utf-8')
    except Exception:
        # Fallback to plaintext if decryption fails (useful for legacy data)
        return value

class EncryptedCharField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = kwargs.get('max_length', 500)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        return decrypt_value(super().to_python(value))

class EncryptedTextField(models.TextField):
    def get_prep_value(self, value):
        value = super().get_prep_value(value)
        return encrypt_value(value)

    def from_db_value(self, value, expression, connection):
        return decrypt_value(value)

    def to_python(self, value):
        if value is None:
            return value
        return decrypt_value(super().to_python(value))
