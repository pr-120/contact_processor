import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
CONTACT_SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]
MAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_contacts():
    """
    Shows basic usage of the People API.
    Prints the name of the first 10 connections.
    """
    creds = authenticate_to_api(CONTACT_SCOPES)

    try:
        service = build("people", "v1", credentials=creds)

        # Call the People API
        print("List 10 connection names")
        results = (
            service.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=1000,
                personFields="names,emailAddresses",
            )
            .execute()
        )
        connections = results.get("connections", [])

        for person in connections:
            mails = person.get("emailAddresses", [])
            if mails:
                mail = mails[0].get("value")
                print(mail)
    except HttpError as err:
        print(err)


def get_invalid_mails():
    """
    returns mail addresses of folder with invalid addresses
    :return invalid_mails: List of invalid mail addresses in string format
    """

    creds = authenticate_to_api(MAIL_SCOPES)

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return
        print("Labels:")
        for label in labels:
            print(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def authenticate_to_api(scope: list[str]):
    """
    Authenticate to access google Cloud
    :scope: list containing single string of link for needed API scope
    :return creds: credentials needed to use APIs
    """

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", scope)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", scope
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


if __name__ == "__main__":
    get_invalid_mails()
