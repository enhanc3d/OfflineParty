import os
import re
import requests
import get_favorites


def fetch_creator_data():
    # Fetching creator data from kemono and coomer using the new API endpoint
    kemono_data = requests.get("https://kemono.su/api/v1/creators.txt").json()
    coomer_data = requests.get("https://coomer.su/api/v1/creators.txt").json()

    return kemono_data + coomer_data


def display_options(id_name_service_mapping):
    for i, (artist_service, _) in enumerate(id_name_service_mapping.items(), start=1):
        # Use title() to capitalize each word in the string
        print(f"{i}. {artist_service.title()}")
    print(f"{len(id_name_service_mapping) + 1}. Download all\n")


def collect_choices(id_name_service_mapping):
    while True:
        choices = input("Which one(s) do you want to choose? (Separated by commas)\nChoice: ")
        try:
            # Parse choices and remove duplicates
            choice_list = list({int(choice.strip()) for choice in choices.split(',')})

            if invalid_choices := [
                choice
                for choice in choice_list
                if choice < 1 or choice > len(id_name_service_mapping) + 1
            ]:
                print(f"Invalid choice(s): {', '.join(map(str, invalid_choices))}. Please choose valid options.")
                display_options(id_name_service_mapping)  # Display the options again
                continue

            # Check for invalid combination: both specific options and "Download All"
            if len(id_name_service_mapping) + 1 in choice_list and len(choice_list) > 1:
                print("Invalid combination. Please select either specific options or 'Download All'.")
                display_options(id_name_service_mapping)  # Display the options again
                continue

            return choice_list
        except ValueError:
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console
            print("Invalid input. Please enter valid numeric choices separated by commas.")
            display_options(id_name_service_mapping)  # Display the options again
            continue


def get_list_of_user_urls(found_user_data, all_urls):
    for entry in found_user_data:
        artist_id = entry.get("id")
        if artist_id.isdigit():
            domain = "kemono.su"
        else:
            domain = "coomer.su"
        service = entry.get("service")
        user_url = f"https://{domain}/api/{service}/user/{artist_id}"
        post_pages = get_favorites.get_all_page_urls(domain, service, artist_id, [user_url])
        post_pages.pop(0)
    all_urls.extend(post_pages)
    return all_urls


def find_and_return_entries(data_list, input_username):
    # Check if input_username is a URL
    # Modified regex to account for discord/server URLs
    url_pattern = r"https://(?P<cookie_domain>\w+\.su)/(?P<service>\w+)/(user|server)/(?P<artist_id>\w+)(\?o=0)?"
    match = re.match(url_pattern, input_username)
    
    if match:
        artist_id = match.group("artist_id")
        service = match.group("service")
        
        # Filter the data list to get the corresponding user or server entry
        for item in data_list:
            if item.get("id") == artist_id and item.get("service") == service:
                return [item]
                
    # If not a URL, proceed with the original logic
    input_username = input_username.strip().lower()
    potential_matches = []

    for item in data_list:
        name = item.get('name', '').strip().lower()
        service = item.get('service', '').capitalize()
        if name == input_username:
            artist_service = f"{name.capitalize()} ({service})"
            potential_matches.append((artist_service, item))

    # If no matches found
    if not potential_matches:
        print(f"No matching entries found for {input_username.capitalize()}")
        return None

    # If only one match found
    if len(potential_matches) == 1:
        artist_service, entry = potential_matches[0]
        return [entry]

    # If multiple matches found
    print(f"Multiple creators found for {input_username.capitalize()}:\n")
    display_options(dict(potential_matches))

    choice_list = collect_choices(dict(potential_matches))

    # If the choice is "Download all", return all the matches
    if len(choice_list) == 1 and choice_list[0] == len(potential_matches) + 1:
        return [entry[1] for entry in potential_matches]

    # For specific choices, return selected entries
    return [potential_matches[i - 1][1] for i in choice_list]


def main(input_username):
    combined_data = fetch_creator_data()
    matched_entries = find_and_return_entries(combined_data, input_username)

    # Example URL and username for demonstration
    example_url = "https://kemono.su/patreon/user/19627910"
    example_username = "otakugirl90"

    while not matched_entries:
        choice = input(f"No matching entries found for {input_username.capitalize()}.\n"
                       f"Did you spell the URL or username correctly?\n"
                       f"Example URL: {example_url}\n"
                       f"Example Username: {example_username}\n"
                       "Would you like to try again? (yes/no): ").strip().lower()

        if choice == 'yes':
            input_username = input("Please enter the correct URL or username: ")
            matched_entries = find_and_return_entries(combined_data, input_username)
        else:
            print("Exiting the program.")
            return None, None, None

    all_urls = []
    for entry in matched_entries:
        all_urls.extend(get_list_of_user_urls([entry], []))

    # Extract username and json_file_path (entry) from the first matched entry
    username = matched_entries[0].get('name', '').strip().lower()
    json_file_path = matched_entries[0]
    return all_urls, username, json_file_path



# Example function call for demonstration purposes
# main("https://kemono.su/gumroad/user/3452671279253")
# main("kamuo")
