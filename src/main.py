from googleapiclient.http import BatchHttpRequest

from contacts import delete_contacts
from email import get_invalid_mail_addresses


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


if __name__ == "__main__":
    invalid_addresses = get_invalid_mail_addresses()
    delete_contacts(invalid_addresses)
