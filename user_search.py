# user_search.py

import os
import re
import requests
import get_favorites

def fetch_creator_data():
    # Fetching creator data from kemono and coomer using the new API endpoint
    kemono_data = requests.get("https://kemono.su/api/v1/creators.txt").json()
    coomer_data = requests.get("https://coomer.su/api/v1/creators.txt").json()
    return kemono_data + coomer_data

def find_and_return_entries(data_list, input_username):
    # Check if input_username is a URL
    url_pattern = r"https://(?P<cookie_domain>\w+\.su)/(?P<service>\w+)/(user|server)/(?P<artist_id>\w+)(\?o=0)?"
    match = re.match(url_pattern, input_username)

    if match:
        artist_id = match.group("artist_id")
        service = match.group("service")
        for item in data_list:
            if item.get("id") == artist_id and item.get("service") == service:
                return [item]

    input_username = input_username.strip().lower()
    potential_matches = []

    for item in data_list:
        name = item.get('name', '').strip().lower()
        service = item.get('service', '').capitalize()
        if name == input_username:
            artist_service = f"{name.capitalize()} ({service})"
            potential_matches.append((artist_service, item))

    if not potential_matches:
        print(f"No matching entries found for {input_username.capitalize()}")
        return None

    if len(potential_matches) == 1:
        artist_service, entry = potential_matches[0]
        return [entry]

    print(f"Multiple creators found for {input_username.capitalize()}:\n")
    display_options(dict(potential_matches))

    choice_list = collect_choices(dict(potential_matches))

    if len(choice_list) == 1 and choice_list[0] == len(potential_matches) + 1:
        return [entry[1] for entry in potential_matches]

    return [potential_matches[i - 1][1] for i in choice_list]
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

def main(input_username):
    combined_data = fetch_creator_data()
    matched_entries = find_and_return_entries(combined_data, input_username)

    while not matched_entries:
        choice = input(f"No matching entries found for {input_username.capitalize()}.\n"
                       f"Did you spell the URL or username correctly?\n"
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

    username = matched_entries[0].get('name', '').strip().lower()
    json_file_path = matched_entries[0]
    return all_urls, username, json_file_path
