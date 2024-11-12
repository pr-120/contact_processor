import time

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from batch import create_batch_request
from contact_processor.log.folder_paths import data_folder
from contact_processor.src.session_storage import get_credentials


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
    creds = get_credentials()

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

        resource_names_of_contacts_to_be_deleted = [el["response"]["results"][0]["person"]["resourceName"] for el in
                                                    response if el["response"] != {}]

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


def get_contacts_from_contact_group(name_of_contact_group: str) -> list[str]:
    """
    returns all contacts of specified contact group
    :param name_of_contact_group: string of name of wanted contact group
    :return: list of resourceNames as strings
    """

    creds = get_credentials()

    service = build("people", "v1", credentials=creds)

    # Oder wenn Sie die vollständige resourceName haben wollen, müssen Sie erst alle Gruppen auflisten
    results = service.contactGroups().list().execute()
    contact_groups = results.get('contactGroups', [])

    # Finden Sie Ihre Gruppe
    group_resource_name = None
    for group in contact_groups:
        if group.get('formattedName') == name_of_contact_group:
            group_resource_name = group.get('resourceName')
            break

    # query for specific contact group
    if group_resource_name:
        response = service.contactGroups().get(
            resourceName=group_resource_name,
            maxMembers=1000
        ).execute()

    return response.get("memberResourceNames")


def add_canton_info_to_contact(list_of_contacts: list[str]) -> dict:
    """
    collect the municipalities for each canton
    :param list_of_contacts: list of resource names of municipality contacts
    :return: dictionary with key of name of canton and value of another dictionary,
     containing the resourceNames of the municipality contacts
    """

    creds = get_credentials()

    service = build("people", "v1", credentials=creds)

    results = []

    # get all information to each contact
    requests_per_batch = 10
    for count in range(0, len(list_of_contacts), requests_per_batch):

        resource_name_batch = list_of_contacts[count:count + requests_per_batch]
        batch = create_batch_request("people", results)

        for resource_name in resource_name_batch:
            batch.add(service.people().get(resourceName=resource_name, personFields="names"))

        batch.execute()
        time.sleep(5)

    # {name_of_canton : {names of municipalities in canton, resourceNames of these municipalities}}
    cantons = {
        "zurich": {"municipalities": [], "contacts": []},
        "st_gallen": {"municipalities": [], "contacts": []},
        "thurgau": {"municipalities": [], "contacts": []}
    }

    # read the municipality name lists contained in 'data' folder
    for key in cantons:
        with open(data_folder + "/municipalities_" + key, "r", encoding="utf-8") as f:
            cantons[key]["municipalities"] = [line.strip() for line in f.readlines()]

    # add municipality to the canton it is in
    for municipality in results:
        for key in cantons:
            name_of_municipality = municipality["response"]["names"][0]["displayName"]
            if name_of_municipality in cantons[key]["municipalities"]:
                cantons[key]["contacts"].append(municipality["response"]["resourceName"])

    return cantons


def modify_contact_groups(canton_data: dict):
    """
    add municipality contacts to the contact group of specific canton
    :param canton_data: dictionary that maps the cantons to their specific municipalities and contacts
    :return: None, contacts are adjusted directly in the cloud
    """

    credentials = get_credentials()

    service = build("people", "v1", credentials=credentials)

    contact_groups = service.contactGroups().list().execute()
    canton_to_group_dict = {el["name"]: el for el in contact_groups["contactGroups"]}

    # check if contact group exists for each canton
    for canton_name in canton_data:

        # create a new contact group if it doesn't exist
        if canton_name not in canton_to_group_dict:
            response = service.contactGroups().create(body={"contactGroup": {"name": canton_name, }}).execute()
            canton_to_group_dict[canton_name] = response

        specified_group = canton_to_group_dict[canton_name]

        # add contacts to canton contact groups
        result = (service.contactGroups().members().modify(
            resourceName=specified_group["resourceName"],
            body={
                "resourceNamesToAdd": canton_data[canton_name]["contacts"]
            }).execute())

    return
