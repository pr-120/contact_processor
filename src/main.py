from contact_processor.src.query_contacts import get_contacts_from_contact_group, add_canton_info_to_contact, \
    modify_contact_groups


def main():
    # invalid_addresses = get_invalid_mail_addresses()
    # delete_contacts(invalid_addresses)
    people_in_contact_group = get_contacts_from_contact_group("Email_Gemeinden2025")
    canton_dict = add_canton_info_to_contact(people_in_contact_group)
    modify_contact_groups(canton_dict)


if __name__ == "__main__":
    main()
