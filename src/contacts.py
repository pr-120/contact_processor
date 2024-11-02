from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from authentication import authenticate_to_api

CONTACT_SCOPES = ["https://www.googleapis.com/auth/contacts.readonly"]


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
