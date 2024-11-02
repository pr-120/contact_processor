import unittest

from googleapiclient.discovery import build

from src.authentication import authenticate_to_api
from src.query_contacts import search_contact, CONTACT_SCOPES


class TestContacts(unittest.TestCase):

    def test_search_contact(self):
        creds = authenticate_to_api(CONTACT_SCOPES)
        service = build("people", "v1", credentials=creds)

        # use term that is referenced to a contact
        search_term = "patrikrosenkranz@gmail.com"

        result = search_contact(service, search_term)

        self.assertIsNotNone(result)
