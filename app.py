from flask import Flask, request, jsonify, redirect, url_for
from flask_cors import CORS
import os
import json
import pathlib

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

app = Flask(__name__)
CORS(app)

# Scopes Gmail pour envoyer des emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# Emplacement de credentials et token
BASE_DIR = pathlib.Path(__file__).parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# Email où tu veux recevoir les messages
TO_EMAIL = os.environ.get("TO_EMAIL", "metellusjunior56@gmail.com")

# Fonction pour récupérer un service Gmail valide
def get_gmail_service():
    creds = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
            creds = flow.run_local_server(port=0)  # Ceci va ouvrir un navigateur pour autoriser
        # Sauvegarde du token pour la prochaine fois
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    service = build('gmail', 'v1', credentials=creds)
    return service

# Fonction pour créer le message MIME
def create_message(sender, to, subject, message_text):
    from email.mime.text import MIMEText
    import base64
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes())
    return {'raw': raw.decode()}

# Endpoint pour recevoir le formulaire et envoyer un mail
@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.get_json()
    name = data.get('name', '')
    user_email = data.get('email', '')
    phone = data.get('phone', '')
    subject = data.get('subject', 'Pas de sujet')
    message = data.get('message', '')

    body = f"""
Nom: {name}
Email: {user_email}
Téléphone: {phone}
Sujet: {subject}
Message:
{message}
"""

    try:
        service = get_gmail_service()
        message_obj = create_message(sender=TO_EMAIL, to=TO_EMAIL, subject=f"Nouveau message : {subject}", message_text=body)
        service.users().messages().send(userId='me', body=message_obj).execute()
        return jsonify({'status': 'success', 'message': 'Email envoyé !'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)), debug=True)
