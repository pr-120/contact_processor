import re
from audioop import error

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest

from authentication import authenticate_to_api

MAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


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
