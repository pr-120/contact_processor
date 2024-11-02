import unittest

from googleapiclient.discovery import build

from src.authentication import authenticate_to_api
from src.contacts import search_contact
from src.email import MAIL_SCOPES


class TestContacts(unittest.TestCase):

    def test_search_contact(self):

        creds = authenticate_to_api(MAIL_SCOPES)
        service = build("gmail", "v1", credentials=creds)

        # use term that is referenced to a contact
        search_term = "patrikrosenkranz@gmail.com"

        search_contact(service, search_term)


