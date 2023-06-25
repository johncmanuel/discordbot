import os

from firebase_admin import credentials, initialize_app


class FirebaseAuth:
    """ Authenticates with Google Firebase and other Google-related services """

    def __init__(self) -> None:
        self._cred = credentials.Certificate({
            'type': "service_account",
            'token_uri': "https://oauth2.googleapis.com/token",
            'project_id': os.getenv('FIREBASE_PROJECT_ID'),
            'client_email': os.getenv('FIREBASE_CLIENT_EMAIL'),
            # Fix: https://github.com/firebase/firebase-admin-python/issues/188#issuecomment-410350471
            'private_key': os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n')
        })
        self.firebase = initialize_app(self._cred, {
            'databaseURL': os.getenv('FIREBASE_DB_URL'),
            'storageBucket': f"{os.getenv('FIREBASE_STORAGE_NAME')}.appspot.com"
        })
