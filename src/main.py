from src.query_contacts import delete_contacts
from src.query_emails import get_invalid_mail_addresses


def main():
    invalid_addresses = get_invalid_mail_addresses()
    delete_contacts(invalid_addresses)


if __name__ == "__main__":
    main()
