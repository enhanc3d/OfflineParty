import os

def display_options(id_name_service_mapping):
    for i, (artist_service, _) in enumerate(id_name_service_mapping.items(), start=1):
        # Use title() to capitalize each word in the string
        print(f"{i}. {artist_service.title()}")
    print(f"{len(id_name_service_mapping) + 1}. Download all\n")

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

def find_and_return_entries(data_list, target_name):
    target_name = target_name.lower()
    potential_matches = []
    
    for item in data_list:
        name = item.get('name', '').capitalize()
        service = item.get('service', '').capitalize()
        if name.lower() == target_name:
            artist_service = f"{name} ({service})"
            potential_matches.append((artist_service, item))
    
    if not potential_matches:
        print(f"No matching entries found for {target_name.capitalize()}")
        return None

    print(f"Multiple creators found for {target_name.capitalize()}:\n")
    for i, (artist_service, _) in enumerate(potential_matches, start=1):
        print(f"{i}. {artist_service}")
    print(f"{len(potential_matches) + 1}. Download all\n")

    choice_list = collect_choices({k: v for k, v in potential_matches})

    if len(choice_list) == 1 and choice_list[0] == len(potential_matches) + 1:
        print("Returning all entries...")
        return potential_matches

    selected_entry = potential_matches[choice_list[0] - 1][1]  # Extract the dictionary from the tuple
    return selected_entry

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
    selected_entries = find_and_return_entries(data_list, target_name)

    if selected_entries:
        print(selected_entries)
    else:
        print("No matching entries found")
