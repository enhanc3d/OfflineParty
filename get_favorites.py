
import requests
import time
import browser_cookie3
import json


def fetch_favorite_artists(option):
    # sourcery skip: extract-method, inline-variable, move-assign
    if option == "kemono":
        primary_cookie_domain = "kemono.party"
        fallback_cookie_domain = "kemono.su"
        JSON_url = 'https://kemono.party/api/v1/account/favorites'
        JSON_fallback_url = 'https://kemono.su/api/v1/account/favorites'
        json_file = 'kemono_favorites.json'
    elif option == "coomer":
        primary_cookie_domain = "coomer.party"
        fallback_cookie_domain = "coomer.su"
        JSON_url = 'https://coomer.party/api/v1/account/favorites'
        JSON_fallback_url = 'https://coomer.su/api/v1/account/favorites'
        json_file = 'coomer_favorites.json'
    else:
        print(f"Invalid option: {option}")
        return []

    old_favorites_data = {}
    try:
        with open(json_file, 'r') as f:
            old_favorites_data = json.load(f)
    except FileNotFoundError:
        print("JSON file not found. It will be created after fetching data.")

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
            with open(json_file, 'w') as f:
                json.dump(favorites_data, f, indent=4)

            artist_list = []
            api_url_list = []

            for artist in favorites_data:
                service = artist['service']
                artist_id = artist['id']
                updated = artist['updated']

                new_posts = False
                if artist_id in old_favorites:
                    old_updated = old_favorites[artist_id]['updated']
                    new_posts = old_updated != updated
                else:
                    new_posts = True

                if new_posts:
                    api_base_url = f'https://{cookie_domain}/api/{service}/user/{artist_id}'
                    offset = 0
                    while True:
                        api_url = f'{api_base_url}?o={offset}'
                        response = session.get(api_url, headers=headers)
                        if response.status_code == 200 and response.json():
                            api_url_list.append(api_url)
                            offset += 50
                        else:
                            break

            return artist_list, api_url_list

    print("Failed to fetch favorite artists from primary and fallback URLs.")
    return []


def main(option):
    _, api_pages_all_artists = fetch_favorite_artists(option)

    return api_pages_all_artists


if __name__ == "__main__":
    api_pages_all_artists = main("kemono")
    # DEBUG
    # for api_page in api_pages_all_artists:
    #     print(api_page)
