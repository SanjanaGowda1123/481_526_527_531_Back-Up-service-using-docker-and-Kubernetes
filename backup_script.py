import os
import logging
import os
import logging
import time  # Add this line to import the time module
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
# Path to the folder you want to backup, adjusted for Docker
FOLDER_PATH = "/app/data"  # Adjusted path for Docker container

# ID of the destination folder in Google Drive
DRIVE_FOLDER_ID = "171zgXUDygi2MZjnUJy1etSvDXyM0l9jv"

# Scope for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to authenticate and create a Drive service instance
def authenticate():
    # Load credentials from the JSON file
    credentials = None
    if os.path.exists('/app/token.json'):  # Adjusted path for Docker container
        credentials = Credentials.from_authorized_user_file('/app/token.json')

    # If there are no (valid) credentials available, let the user log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/app/credentials.json', scopes=SCOPES)  # Adjusted path for Docker container
            credentials = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open('/app/token.json', 'w') as token:  # Adjusted path for Docker container
            token.write(credentials.to_json())

    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

def upload_file(drive_service, file_path, folder_id):
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [folder_id]
    }
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        logger.info(f'File uploaded: {file.get("id")}')
    except Exception as e:
        logger.error(f'Error uploading file: {file_path}, Error: {str(e)}')

if __name__ == "__main__":
    # Authenticate with Google Drive API
    drive_service = authenticate()
    
    # Get the list of files in the folder
    files_in_folder = os.listdir(FOLDER_PATH)

    # Upload each file to Google Drive
    for filename in files_in_folder:
        file_path = os.path.join(FOLDER_PATH, filename)
        if os.path.isfile(file_path):
            upload_file(drive_service, file_path, DRIVE_FOLDER_ID)

    # Continuously monitor the folder for changes and upload any new files
    while True:
        new_files = os.listdir(FOLDER_PATH)
        for filename in new_files:
            file_path = os.path.join(FOLDER_PATH, filename)
            if os.path.isfile(file_path) and filename not in files_in_folder:
                upload_file(drive_service, file_path, DRIVE_FOLDER_ID)
                files_in_folder.append(filename)
        # Wait for a short interval before checking for changes again
        #time.sleep(500)  # Adjust as needed
