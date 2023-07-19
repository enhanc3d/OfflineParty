import requests
import time
import browser_cookie3
import json
from bs4 import BeautifulSoup
from tqdm import tqdm
from urllib.parse import urljoin, urlparse, urlunparse

def fetch_favorite_artists(option):
    if option == "kemono":
        primary_cookie_domain = "kemono.party"
        fallback_cookie_domain = "kemono.su"
        primary_favorites_json_url = 'https://kemono.party/api/v1/account/favorites'
        fallback_favorites_json_url = 'https://kemono.su/api/v1/account/favorites'
        json_file = 'kemono_favorites.json'
    elif option == "coomer":
        primary_cookie_domain = "coomer.party"
        fallback_cookie_domain = "coomer.su"
        primary_favorites_json_url = 'https://coomer.party/api/v1/account/favorites'
        fallback_favorites_json_url = 'https://coomer.su/api/v1/account/favorites'
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

    old_favorites_dict = {artist['id']: artist for artist in old_favorites_data}

    for cookie_domain, favorites_json_url in [
        (primary_cookie_domain, primary_favorites_json_url),
        (fallback_cookie_domain, fallback_favorites_json_url),
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
                session.cookies.set('session', session_id_cookie, domain=cookie_domain)
                favorites_response = session.get(favorites_json_url, headers=headers)
                favorites_response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                print(e)
                print(f"Error trying to connect to the server, retrying in {retry_delay} seconds")
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
                if artist_id in old_favorites_dict:
                    old_updated = old_favorites_dict[artist_id]['updated']
                    new_posts = old_updated != updated
                else:
                    new_posts = True

                if new_posts:
                    artist_list.append(f'https://{cookie_domain}/{service}/user/{artist_id}')
                    api_url_list.append(f'https://{cookie_domain}/api/{service}/user/{artist_id}?o=0')

            return artist_list, api_url_list

    print("Failed to fetch favorite artists from both primary and fallback URLs.")
    return []


def make_soup(page):
    response = requests.get(page)
    return BeautifulSoup(response.text, 'html.parser')


def get_next_page(artist_page):
    soup = make_soup(artist_page)
    if soup is None:
        return None

    next_link = soup.find('a', class_='next')

    if next_link is not None:
        href = next_link.get('href')
        return urljoin(artist_page, href)
    return None


def get_all_pages(artist_url):
    artist_pages = [artist_url]
    next_page = get_next_page(artist_url)
    while next_page is not None:
        artist_pages.append(next_page)
        next_page = get_next_page(next_page)
    return artist_pages


def add_api_header(pages):
    api_pages = []
    for page in pages:
        url_parts = list(urlparse(page))
        url_parts[2] = f"/api{url_parts[2]}"
        api_pages.append(urlunparse(url_parts))
    return api_pages


def main(option):
    favorite_artists, _ = fetch_favorite_artists(option)

    api_pages_all_artists = []
    for artist_url in tqdm(favorite_artists, desc="Processing artists..."):
        all_pages = get_all_pages(artist_url)
        api_pages = add_api_header(all_pages)
        api_pages_all_artists.extend(api_pages)

    return api_pages_all_artists


if __name__ == "__main__":
    api_pages_all_artists = main()
    for api_page in api_pages_all_artists:
        print(api_page)
