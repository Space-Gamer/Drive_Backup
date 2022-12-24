import os
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import HttpError
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

creds = None

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

try:
    service = build('drive', 'v3', credentials=creds)

    # Check if MWTS folder exists in Google Drive
    response = service.files().list(
        q="name='MWTS' and mimeType='application/vnd.google-apps.folder'",
        spaces='drive',
    ).execute()

    # If MWTS folder does not exist, create it
    if not response['files']:
        file_metadata = {
            'name': 'MWTS',
            'mimeType': 'application/vnd.google-apps.folder'
        }

        file = service.files().create(body=file_metadata, fields='id').execute()

        folder_id = file.get('id')
    # If MWTS folder exists, get its ID
    else:
        folder_id = response['files'][0]['id']

    # Upload file to MWTS folder from local directory 'data'
    for file in os.listdir('data'):

        # Check if file already exists
        response = service.files().list(
            q="name='{}' and '{}' in parents".format(file, folder_id),
            spaces='drive',
        ).execute()

        # Uploading new file
        file_metadata = {
            'name': file,
            'parents': [folder_id]
        }
        media = MediaFileUpload('data/' + file)
        new_file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f'Backed up file: {file}')

        # Delete old file
        if response['files']:
            old_file_id = response['files'][0]['id']
            service.files().delete(fileId=old_file_id).execute()

except HttpError as e:
    print("Error: ", e)
