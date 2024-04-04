import os

CONFIG = {
    "telegram_token": 'token...',
    "dialogflow": {
        "credentials_path": os.path.dirname(__file__) + '/application_credentials.json',
        "project_id": ''
    }
}