from contact_processor.src.authentication import authenticate_to_api

session_storage = {}


def set_value(key, value):
    session_storage[key] = value


def get_value(key):
    return session_storage[key]


def get_credentials():
    MAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly"
    CONTACT_SCOPES = "https://www.googleapis.com/auth/contacts"

    if "credentials" not in session_storage:
        credentials = authenticate_to_api([MAIL_SCOPES, CONTACT_SCOPES])
        session_storage["credentials"] = credentials

    return session_storage["credentials"]
