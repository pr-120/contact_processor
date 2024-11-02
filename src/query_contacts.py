import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.authentication import authenticate_to_api
from src.batch import create_batch_request

CONTACT_SCOPES = ["https://www.googleapis.com/auth/contacts"]


def search_contact(service, search_term):
    """
    Search specific contact
    """

    try:
        result = (service.people().
                  searchContacts(query=search_term, readMask="names,emailAddresses")
                  .execute())

        return result
    except HttpError as err:
        print(err)


def delete_contacts(search_terms: list):
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

        response = []

        nr_of_search_terms_per_batch = 10
        for count in range(0, len(search_terms), nr_of_search_terms_per_batch):

            batch_of_search_terms = search_terms[count:count + nr_of_search_terms_per_batch]
            batch = create_batch_request("people", response)

            # find names of contacts with email addresses
            for search_term in batch_of_search_terms:
                batch.add(service.people().searchContacts(query=search_term, readMask="names,emailAddresses"))

            batch.execute()

            # needed to match quota limit
            time.sleep(10)

        resource_names_of_contacts_to_be_deleted = [el["response"]["results"][0]["person"]["resourceName"] for el in response if el["response"] != {}]

        for count in range(0, len(resource_names_of_contacts_to_be_deleted), nr_of_search_terms_per_batch):

            resource_name_batch = resource_names_of_contacts_to_be_deleted[count:count + nr_of_search_terms_per_batch]
            batch = create_batch_request("people", [])

            for resource_name in resource_name_batch:
                batch.add(service.people().deleteContact(resourceName=resource_name))

            batch.execute()

            time.sleep(10)

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
