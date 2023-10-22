import browser_cookie3
import requests
import time
import json
import sys
import os
from tqdm import tqdm


def safe_print(text):
    try:
        # Try to print the text as UTF-8
        sys.stdout.buffer.write(text.encode('utf-8'))
        sys.stdout.buffer.write(b'\n')
    except UnicodeEncodeError:
        # Handle characters that cannot be encoded
        for char in text:
            try:
                sys.stdout.buffer.write(char.encode('utf-8'))
            except UnicodeEncodeError:
                sys.stdout.buffer.write(b'?')  # Replace unencodable characters with a placeholder
        sys.stdout.buffer.write(b'\n')


def create_config(directory):
    """
    Creates the Config folder if it doesn't exist and ensures
    that 'kemono_favorites.json' and 'coomer_favorites.json' files
    exist inside the folder with empty arrays [] as content.
    """
    # Create the directory if it doesn't exist
    os.makedirs(directory, exist_ok=True)

    # Check if 'kemono_favorites.json' exists, and create it with an empty array if not
    kemono_file_path = os.path.join(directory, 'kemono_favorites.json')
    if not os.path.exists(kemono_file_path):
        with open(kemono_file_path, 'w', encoding='utf-8') as kemono_file:
            json.dump([], kemono_file)

    # Check if 'coomer_favorites.json' exists, and create it with an empty array if not
    coomer_file_path = os.path.join(directory, 'coomer_favorites.json')
    if not os.path.exists(coomer_file_path):
        with open(coomer_file_path, 'w', encoding='utf-8') as coomer_file:
            json.dump([], coomer_file)


def check_updates_for_non_favorites(json_file_path):

    # Define the list to be returned
    api_url_list = []
    json_dicts = []  # List to store JSON dictionaries

    try:
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            json_data = json.load(json_file)

        for entry in json_data:
            faved_seq = entry.get("faved_seq")
            artist_id = entry.get("id")
            artist_name = entry.get("name")
            service = entry.get("service")
            old_date = entry.get("updated")

            if faved_seq == "UNKNOWN":
                if artist_id.isdigit() and service != "fansly":
                    cookie_domain = "kemono.su"
                else:
                    cookie_domain = "coomer.su"

                api_base_url = f'https://{cookie_domain}/api/v1/{service}/user/{artist_id}'
                if service.lower() == "discord":
                    api_url_list.append(api_base_url)
                    json_dicts.append(entry)
                    continue

                try:
                    response = requests.get(api_base_url)
                    response.raise_for_status()
                    website_data = response.json()

                    # Assuming website_data is a list of dictionaries
                    if website_data:
                        # Extracting the "published" key from the first item in the list
                        published_date = website_data[0].get("published")

                        # Update the "updated" field in the entry with the new published_date
                        entry["updated"] = published_date

                        # Append the JSON dictionary to the list
                        json_dicts.append(entry)

                        if old_date != published_date:
                            api_url_list = get_all_page_urls(cookie_domain, service, artist_id, api_url_list)

                    else:
                        return None, None  # No data found on the website

                except requests.exceptions.RequestException as e:
                    print(f"Error fetching data from website: {e}")

    except FileNotFoundError:
        print(f"JSON file not found: {json_file_path}")

    # Return both the list of unupdated URLs and the list of JSON dictionaries
    return api_url_list, json_dicts


def load_old_favorites_data(json_file):
    """
    Loads the existing JSON files for coomer or kemono, if they exist.
    This is needed to understand if there are new posts
    from our favorite creators.
    """
    old_favorites_data = {}
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            old_favorites_data = json.load(f)
    except FileNotFoundError:
        print("JSON file not found. It will be created after fetching data.")
    return old_favorites_data


def fetch_json_data_from_option(option):
    """
    Fetches the JSON data from the given option ("kemono" or "coomer")
    """
    if option == "kemono":
        primary_cookie_domain = "kemono.su"
        fallback_cookie_domain = "kemono.su"
        JSON_url = 'https://kemono.su/api/v1/account/favorites?type=artist'
        JSON_fallback_url = 'https://kemono.su/api/v1/account/favorites?type=artist'
    elif option == "coomer":
        primary_cookie_domain = "coomer.su"
        fallback_cookie_domain = "coomer.su"
        JSON_url = 'https://coomer.su/api/v1/account/favorites?type=artist'
        JSON_fallback_url = 'https://coomer.su/api/v1/account/favorites?type=artist'
    else:
        print(f"Invalid option: {option}")
        return None

    for cookie_domain, favorites_json_url in [
        (primary_cookie_domain, JSON_url),
        (fallback_cookie_domain, JSON_fallback_url),
    ]:
        cj = browser_cookie3.load()
        session_id_cookie = next(
            (
                cookie.value
                for cookie in cj
                if cookie_domain in cookie.domain and cookie.name == 'session'
            ),
            None,
        )
        if session_id_cookie is None:
            print("Failed to fetch session ID cookie.")
            continue

        headers = {'Authorization': session_id_cookie}
        retry_attempts = 3
        retry_delay = 10

        for attempt in range(1, retry_attempts + 1):
            try:
                session = requests.Session()
                session.cookies.set('session',
                                    session_id_cookie,
                                    domain=cookie_domain)
                favorites_response = session.get(favorites_json_url,
                                                 headers=headers)
                favorites_response.raise_for_status()
                return_value = favorites_response.json()

                # Debugging line
                # print(f"Number of return values: {len(return_value)}")

                return return_value
            except requests.exceptions.RequestException as e:
                print(e)
                print(f"Server error, retrying in {retry_delay} seconds")
                time.sleep(retry_delay)
                retry_delay *= 3

                if attempt == retry_attempts:
                    print("Couldn't connect to the server, try again later.")
                    continue

    print("Failed to fetch favorite artists from primary and fallback URLs.")
    return None


def fetch_favorite_artists(option):
    """
    Requests the list of favorite creators from the APIs
    and extracts some useful data based on the specified option.
    """
    create_config('Config')

    if option not in ["kemono", "coomer"]:
        print(f"Invalid option: {option}")
        return [], [], []

    json_file = 'Config/kemono_favorites.json' if option == "kemono" else 'Config/coomer_favorites.json'
    old_favorites_data = load_old_favorites_data(json_file)
    old_favorites = {artist['id']: artist for artist in old_favorites_data}

    favorites_data = fetch_json_data_from_option(option)

    if not favorites_data:
        return [], []

    api_url_list = []

    for artist in tqdm(favorites_data, desc="Processing artists"):
        artist_id = artist['id']  # Extracts ID
        new_posts = False
        if artist_id in old_favorites:
            old_updated = old_favorites[artist_id]['updated']
            updated = artist['updated']

            new_posts = old_updated != updated  # If the date of the post is different, we understand there are new posts
        else:
            new_posts = True

        if new_posts:
            service = artist['service']
            cookie_domain = "kemono.su" if option == "kemono" else "coomer.su"
            get_all_page_urls(cookie_domain,
                              service,
                              artist_id,
                              api_url_list)

    non_favorites_api_url_list, non_favorite_json_data = check_updates_for_non_favorites(json_file)
    all_api_urls = api_url_list + non_favorites_api_url_list
    favorites_data.extend(non_favorite_json_data)
    return all_api_urls, favorites_data


def get_all_page_urls(cookie_domain, service, artist_id, api_url_list):
    """
    Get all API page URLs for a specific artist.
    """
    api_base_url = f'https://{cookie_domain}/api/v1/{service}/user/{artist_id}'
    
    if service.lower() == "discord":
        api_url_list.append(api_base_url)
        return api_url_list
    
    offset = 0
    while True:
        api_url = f'{api_base_url}?o={offset}'
        response = requests.get(api_url)
        if response.status_code != 200 or not response.json():
            break

        api_url_list.append(api_url)
        offset += 50

    return api_url_list


def main(option):
    """
    Main function to fetch favorite artists.
    """
    api_pages_all_artists, favorites_data = fetch_favorite_artists(option)
    # debug -- print(api_pages_all_artists)
    return api_pages_all_artists, favorites_data


if __name__ == "__main__":
    api_pages_all_artists = main("coomer")
    # DEBUG
    # for api_page in api_pages_all_artists:
    #     print(api_page)
