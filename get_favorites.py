import os
import time
import json
import requests
import browser_cookie3
from tqdm import tqdm


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


def fetch_json_data(option):
    """
    Fetches the JSON data from the given option ("kemono" or "coomer")
    """
    if option == "kemono":
        cookie_domain = "kemono.su"
        JSON_url = 'https://kemono.su/api/v1/account/favorites?type=artist'
    elif option == "coomer":
        cookie_domain = "coomer.su"
        JSON_url = 'https://coomer.su/api/v1/account/favorites?type=artist'
    else:
        print(f"Invalid option: {option}")
        return None

    for cookie_domain, favorites_json_url in [(cookie_domain, JSON_url)]:
        browser_cookies = browser_cookie3.load()
        session_id_cookie = next(
            (
                cookie.value
                for cookie in browser_cookies
                if cookie_domain in cookie.domain and cookie.name == 'session'
            ),
            None
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

                # debug -- print(f"Number of return values: {len(return_value)}")

                return return_value
            except requests.exceptions.RequestException as e:
                print(e)
                print(f"Server error, retrying in {retry_delay} seconds")
                time.sleep(retry_delay)
                retry_delay *= 3

                if attempt == retry_attempts:
                    print("Couldn't connect to the server, try again later.")
                    continue

    print("Failed to fetch favorite users.")
    print("Make sure you are logged into %s website(s) and try again" % option)
    return None


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


def fetch_favorite_artists(option):
    create_config('Config')

    if option not in ["kemono", "coomer"]:
        print(f"Invalid option: {option}")
        return [], []

    json_file = f'Config/{option}_favorites.json'
    old_favorites_data = load_old_favorites_data(json_file)
    old_favorites = {artist['id']: artist for artist in old_favorites_data}

    favorites_data = fetch_json_data(option)

    if not favorites_data:
        return [], []

    api_url_list = []

    # Identify artists that are in old_favorites but not in the new favorites_data
    missing_from_favorites = {k: v for k, v in old_favorites.items() if k not in [artist['id'] for artist in favorites_data]}

    # Fetch all creators
    all_creators_url = f"https://{option}.su/api/v1/creators.txt"
    try:
        response = requests.get(all_creators_url)
        response.raise_for_status()
        all_creators_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from website: {e}")
        return [], []

    creators_dict = {creator['id']: creator for creator in all_creators_data}

    for creator in all_creators_data:
        if creator['id'] in missing_from_favorites:
            favorites_data.append(creator)

    # Check for new posts for all artists in favorites_data
    for artist in tqdm(favorites_data, desc="Processing artists"):
        new_posts = False
        artist_id = artist['id']

        if artist_id in old_favorites:
            old_updated = old_favorites[artist_id]['updated']
            updated = artist['updated'] if artist['updated'] else creators_dict.get(artist_id, {}).get('updated', None)
            new_posts = old_updated != updated
        else:
            new_posts = True

        if new_posts:
            service = artist['service']
            cookie_domain = f"{option}.su"
            get_all_page_urls(cookie_domain, service, artist_id, api_url_list)

    return api_url_list, favorites_data


def get_all_page_urls(cookie_domain, service, artist_id, api_url_list):
    """
    Get all API page URLs for a specific artist.
    """
    api_base_url = f'https://{cookie_domain}/api/v1/{service}/user/{artist_id}'
    
    if service.lower() == "discord":
        api_url_list.append(f'https://{cookie_domain}/api/v1/discord/channel/{artist_id}')
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
