import requests
import time
import browser_cookie3
import json
import os
from tqdm import tqdm


def create_directory(directory):
    """
    Creates the Config folder where JSON files are stored if
    it doesn't exist.
    """
    os.makedirs(directory, exist_ok=True)


def load_old_favorites_data(json_file):
    """
    Loads the existing JSON files for coomer or kemono, if they exist.
    This is needed to understand if there are new posts
    from our favorite creators.
    """
    old_favorites_data = {}
    try:
        with open(json_file, 'r') as f:
            old_favorites_data = json.load(f)
    except FileNotFoundError:
        print("JSON file not found. It will be created after fetching data.")
    return old_favorites_data


def fetch_favorite_artists(option):
    """
    Requests the list of favorite creators from the APIs
    and extracts some useful data based on the specified option.
    """
    create_directory('Config')

    if option == "kemono":
        primary_cookie_domain = "kemono.party"
        fallback_cookie_domain = "kemono.su"
        JSON_url = 'https://kemono.party/api/v1/account/favorites'
        JSON_fallback_url = 'https://kemono.su/api/v1/account/favorites'
        json_file = 'Config/kemono_favorites.json'
    elif option == "coomer":
        primary_cookie_domain = "coomer.party"
        fallback_cookie_domain = "coomer.su"
        JSON_url = 'https://coomer.party/api/v1/account/favorites'
        JSON_fallback_url = 'https://coomer.su/api/v1/account/favorites'
        json_file = 'Config/coomer_favorites.json'
    else:
        print(f"Invalid option: {option}")
        return [], [], []

    old_favorites_data = load_old_favorites_data(json_file)
    old_favorites = {artist['id']: artist for artist in old_favorites_data}

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
                break
            except requests.exceptions.RequestException as e:
                print(e)
                print(f"Server error, retrying in {retry_delay} seconds")
                time.sleep(retry_delay)
                retry_delay *= 3

                if attempt == retry_attempts:
                    print("Couldn't connect to the server, try again later.")
                    continue

        if favorites_response.status_code == 200:
            favorites_data = favorites_response.json()

            artist_list = []
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
                    get_all_page_urls(cookie_domain,
                                      service,
                                      artist_id,
                                      session,
                                      headers,
                                      api_url_list)
            return artist_list, api_url_list, favorites_data
        """
        Returns the list of artists, with 
        """

    print("Failed to fetch favorite artists from primary and fallback URLs.")
    return [], [], []


def get_all_page_urls(cookie_domain, service, artist_id, session, headers, api_url_list):
    """
    Get all API page URLs for a specific artist.
    """
    api_base_url = f'https://{cookie_domain}/api/{service}/user/{artist_id}'
    offset = 0
    while True:
        api_url = f'{api_base_url}?o={offset}'
        response = session.get(api_url, headers=headers)
        if response.status_code != 200 or not response.json():
            break

        api_url_list.append(api_url)
        offset += 50
    
    return api_url_list  # Move the return statement here, outside the loop


def main(option):
    """
    Main function to fetch favorite artists.
    """
    artist_list, api_pages_all_artists, favorites_data = fetch_favorite_artists(option)
    # debug -- print(api_pages_all_artists)
    return [], api_pages_all_artists, favorites_data


if __name__ == "__main__":
    api_pages_all_artists = main("coomer")
    # DEBUG
    # for api_page in api_pages_all_artists:
    #     print(api_page)
