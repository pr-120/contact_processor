import json
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from contact_processor.log.folder_paths import credentials_folder, root_folder


def authenticate_to_api(scope: list[str]):
    """
    Authenticate to access google Cloud
    :param scope: list containing single string of link for needed API scope
    :return: credentials needed to use APIs
    """

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(credentials_folder + "/token.json"):

        # only use token if it has the same scope as requested
        with open(credentials_folder + "/token.json") as token:
            data = json.load(token)
            if all(el in data["scopes"] for el in scope):
                creds = Credentials.from_authorized_user_file(credentials_folder + "/token.json", scope)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_folder + "/credentials.json", scope
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(credentials_folder + "/token.json", "w") as token:
            token.write(creds.to_json())

    return creds
