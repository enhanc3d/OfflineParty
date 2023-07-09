import json
import os
from bs4 import BeautifulSoup
import re
import requests
from pathvalidate import sanitize_filename


def get_artist_info(soup: BeautifulSoup, artist_page: str) -> dict:

    def get_artist_name(artist_page):
        soup = make_soup(artist_page)
        artist_name_meta = soup.select_one('meta[name="artist_name"]')
        if artist_name_meta and 'content' in artist_name_meta.attrs:
            return artist_name_meta['content']
        return None

    def get_number_of_posts(soup: BeautifulSoup) -> int:
        post_count_element = soup.select_one('div.paginator > small')
        if post_count_element:
            post_count_text = post_count_element.get_text(strip=True)
            post_count_match = re.search(r'(\d+)$', post_count_text)
            if post_count_match:
                return int(post_count_match.group())

        articles = soup.select('article.post-card, article.post-card--preview')
        return len(articles) if articles else None

    def make_soup(url):
        response = requests.get(url)
        return BeautifulSoup(response.text, 'html.parser')

    artist_name = sanitize_filename(get_artist_name(artist_page))
    number_of_posts = get_number_of_posts(soup)
    artist_platform_element = soup.select_one('meta[name="service"]')
    artist_platform = artist_platform_element.get('content') if artist_platform_element else None

    artist_info = {
        'artist_name': artist_name,
        'number_of_posts': number_of_posts,
        'artist_platform': artist_platform,
    }

    return artist_info


def get_total_artist_info(urls):
    total_artist_info = {}

    for url in urls:
        response = requests.get(url)
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        artist_info = get_artist_info(soup, url)
        total_artist_info[url] = artist_info

    return total_artist_info


# Example usage
urls = ['https://kemono.party/patreon/user/25715696', 'https://kemono.party/patreon/user/73150554', 'https://kemono.party/patreon/user/45409739', 'https://kemono.party/fanbox/user/2253649']
total_artist_info = get_total_artist_info(urls)

output_folder = "Artists"
os.makedirs(output_folder, exist_ok=True)

output_file = os.path.join(output_folder, "artist_info.json")
with open(output_file, 'w') as file:
    json.dump(total_artist_info, file, indent=4)

print(f"Artist information saved to: {output_file}")
