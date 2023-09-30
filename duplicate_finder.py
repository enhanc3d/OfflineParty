import os

def display_options(id_name_service_mapping):
    for i, artist_service in enumerate(id_name_service_mapping, start=1):
        # Use title() to capitalize each word in the string
        print(f"{i}. {artist_service.title()}")
    print(f"{i+1}. Download all\n")

def collect_choices(id_name_service_mapping):
    while True:
        choices = input("Which one(s) do you want to choose? (Separated by commas) ")
        try:
            choice_list = [int(choice.strip()) for choice in choices.split(',')]
            invalid_choices = [choice for choice in choice_list if choice < 1 or choice > len(id_name_service_mapping) + 1]
            if invalid_choices:
                print(f"Invalid choice(s): {', '.join(map(str, invalid_choices))}. Please choose valid options.")
                continue
            return choice_list
        except ValueError:
            print("Invalid input. Please enter valid numeric choices separated by commas.")

def find_and_download_entries(data_list, target_name):
    target_name = target_name.lower()
    id_name_service_mapping = {}
    for item in data_list:
        name = item.get('name').capitalize()
        service = item.get('service').capitalize()
        if name.lower() == target_name:
            id_value = item.get('id')
            artist_service = f"{name} ({service})"
            if artist_service not in id_name_service_mapping:
                id_name_service_mapping[artist_service] = []
            id_name_service_mapping[artist_service].append(id_value)

    if not id_name_service_mapping:
        print(f"No matching entries found for {target_name.capitalize()}")
        return None

    print(f"Multiple creators found for {target_name.capitalize()}:\n")
    display_options(id_name_service_mapping)
    choice_list = collect_choices(id_name_service_mapping)

    id_to_name_relation = {}
    for choice in choice_list:
        if choice == len(id_name_service_mapping) + 1:
            print("Downloading all...")
            for artist_service, ids in id_name_service_mapping.items():
                for id_value in ids:
                    id_to_name_relation[id_value] = artist_service.split(" (")[0]
        else:
            artist_service = list(id_name_service_mapping.keys())[choice - 1]
            ids = id_name_service_mapping[artist_service]
            print(f"Downloading {artist_service}...")
            for id_value in ids:
                id_to_name_relation[id_value] = artist_service.split(" (")[0]

    return id_to_name_relation

if __name__ == "__main__":
    data_list = [
        {
            'faved_seq': 12438757,
            'id': '19627910',
            'indexed': 'Sun, 23 Aug 2020 16:03:21 GMT',
            'last_imported': 'Tue, 26 Sep 2023 14:46:02 GMT',
            'name': 'Kamuo',
            'service': 'patreon',
            'updated': 'Sun, 24 Sep 2023 05:17:18 GMT'
        },
        {
            "faved_seq": 24961280,
            "id": "3452671279253",
            "indexed": "Thu, 03 Feb 2022 14:44:29 GMT",
            "last_imported": "Sat, 28 May 2022 03:24:08 GMT",
            "name": "Kamuo",
            "service": "gumroad",
            "updated": "Thu, 17 Feb 2022 15:49:17 GMT"
        }
    ]
    
    target_name = input("Enter the username: ").capitalize()
    id_to_name_relation = refactored_find_and_download_entries(data_list, target_name)

    if id_to_name_relation:
        print(id_to_name_relation)
    else:
        print("No matching entries found")
