import os.path
import re
from audioop import error

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest

# If modifying these scopes, delete the file token.json.
CONTACT_SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]
MAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def search_contact(service, search_term):
    """
    Search specific contact
    """

    try:
        result = (service.people().searchContacts(query=search_term, readMask="names,emailAddresses").execute())

        return result
    except HttpError as err:
        print(err)


def delete_contactss(search_terms: list):
    """
    deletes the contacts which are found with search terms
    :search_terms: list of strings which are used to find specific contacts
    :return: None
    """
    creds = authenticate_to_api(CONTACT_SCOPES)

    try:
        service = build("people", "v1", credentials=creds)

        # warm up cache
        search_contact(service, "")

        contact_names_to_be_deleted = []

        # find names of contacts with email addresses
        for search_term in search_terms:
            contact_names_to_be_deleted.append(search_contact(service, search_term))

        batch_delete(service, contact_names_to_be_deleted)

        """# Call the People API
        print("List 10 connection names")
        results = (
            service.get()
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
                print(mail)"""


    except HttpError as err:
        print(err)


def get_invalid_mail_addresses():
    """
    returns mail addresses of folder with invalid addresses
    :return invalid_mails: List of invalid mail addresses in string format
    """

    creds = authenticate_to_api(MAIL_SCOPES)
    addresses_to_be_deleted = []

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()

        # get id of label which we want to remove from rest of mails
        specific_label = [label for label in results["labels"] if label.get("name") == "falsch addressiert"][0]

        # get all mails which are labeled with specific_label
        invalid_addresses = service.users().messages().list(userId="me", labelIds=[specific_label.get("id")]).execute()

        print("Nr. of 429 Errors: ", sum([1 for response in invalid_addresses if "error" in response]))

        messages = get_messages_from_invalid_addresses(invalid_addresses["messages"], creds)

        addresses_to_be_deleted = match_addresses_that_can_be_deleted(messages)

        if not specific_label:
            print("No labels found.")
            return
        else:
            print("Labels:")
            print(specific_label)

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")

    return addresses_to_be_deleted


def match_addresses_that_can_be_deleted(messages):
    """
    finds addresses that can be deleted from messages
    :messages: list of messages that contain an invalid address in text
    :return: list of invalid addresses that can be deleted
    """
    invalid_addresses = []

    try:

        for message in messages:
            content_of_message = message["response"]["snippet"]

            # match an email address in message content
            email_to_be_deleted = re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', content_of_message)

            if email_to_be_deleted:
                invalid_addresses.append(email_to_be_deleted.group())
    except error:
        pass

    return invalid_addresses


def get_messages_from_invalid_addresses(invalid_emails: list, creds):
    """
    returns the message objects from message IDs given in invalid_emails
    :invalid_emails: list of invalid email address objects
    """
    results = []
    service = build("gmail", "v1", credentials=creds)

    def callback(request_id, response, exception):
        if exception:
            print(f"An error occurred for request {request_id}: {exception}")
            results.append({"id": request_id, "error": exception})
        else:
            print(f"Message ID {request_id}: {response['snippet']}")
            results.append({"id": request_id, "response": response})

    # batch emails in groups to ensure no 429 errors are thrown serverside
    nr_of_emails_per_batch = 10
    for count in range(0, len(invalid_emails), 10):

        batch_of_emails = invalid_emails[count:count + nr_of_emails_per_batch]
        batch = BatchHttpRequest(batch_uri="https://gmail.googleapis.com/batch", callback=callback)

        for invalid_email in batch_of_emails:
            batch.add(service.users().messages().get(userId="me", id=invalid_email["id"]))

        batch.execute()

    return results


def batch_delete(service, contact_names_to_be_deleted: list):
    """
    deletes contacts that are provided in list
    :param service: google API service object
    :param contact_names_to_be_deleted: list of names of contacts to be deleted
    :return: None
    """

    def callback(request_id, response, exception):
        if exception:
            print(f"An error occurred for request {request_id}: {exception}")
        else:
            print(f"Message ID {request_id}: {response['snippet']}")

    batch = BatchHttpRequest(batch_uri="https://gmail.googleapis.com/batch", callback=callback)

    for contact_name in contact_names_to_be_deleted:
        batch.add(service.people().deleteContact(contact_name).execute())

    batch.execute()


def authenticate_to_api(scope: list[str]):
    """
    Authenticate to access google Cloud
    :param scope: list containing single string of link for needed API scope
    :return: credentials needed to use APIs
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
    invalid_addresses = get_invalid_mail_addresses()
    delete_contactss(invalid_addresses)
