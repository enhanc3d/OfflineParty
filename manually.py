import os
import sys
import re
import requests
import string
import datetime
import subprocess
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

def clear_console():
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)


def sanitize_string(s: str) -> str:
    s = s.strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', s)
    s = s.rstrip('. ')
    s = s[:255]
    return s


def get_total_posts_count(soup: BeautifulSoup) -> int:
    post_count_element = soup.select_one('div.paginator > small')
    if post_count_element:
        post_count_text = post_count_element.get_text(strip=True)
        post_count_match = re.search(r'\d+$', post_count_text)
        if post_count_match:
            return int(post_count_match.group())
    articles = soup.select('article.post-card, article.post-card--preview')
    if articles:
        return len(articles)
    return None


def write_error_to_file(folder: str, filename: str, url: str, error: str):
    error_filename = "scraping_errors.txt"
    error_message = f"[{datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}] Error occurred while scraping {filename} from {url}: {error}\n:"
    with open(os.path.join(".", error_filename), 'a', encoding='utf-8') as f:
        f.write(error_message)


def get_artist_info(soup: BeautifulSoup) -> dict:
    artist_name_element = soup.select_one('meta[name="artist_name"]')
    artist_name = artist_name_element.get('content') if artist_name_element else None
    number_of_posts = get_total_posts_count(soup)
    artist_platform_element = soup.select_one('meta[name="service"]')
    artist_platform = artist_platform_element.get('content') if artist_platform_element else None

    artist_info = {
        'artist_name': artist_name,
        'number_of_posts': number_of_posts,
        'artist_platform': artist_platform,
    }

    return artist_info


def download(url: str, filename: str, folder: str):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_string(unquote(filename))
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c if c in valid_chars else '_' for c in filename)
    if os.path.exists(os.path.join(folder, filename)):
        print(f'File {filename} already exists in {folder}, skipping')
        return filename
    filename_encoded = filename.encode('utf-8', errors='ignore').decode('utf-8')
    filename_encoded = filename_encoded.replace('/', '-')
    filename_encoded = filename_encoded[:255]
    print(f'Saving {filename_encoded} to {folder}')
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(folder, filename_encoded), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def fetch_post_media(url: str, artist_folder: str):
    print(f'Downloading media from {url}')
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    post_title = sanitize_string(soup.select_one('h1.post__title > span').get_text(strip=True))
    post_date = soup.select_one('div.post__published > time').get('datetime').split()[0]

    folder = os.path.join("Artists", artist_folder, f'{post_date}_{post_title}')
    os.makedirs(folder, exist_ok=True)

    media_tags = soup.select('div.post__files > div.post__thumbnail > a.fileThumb')
    for index, tag in enumerate(media_tags, start=1):
        media_url = tag.get('href')
        media_name = tag.get('download') or media_url.split('/')[-1].split('?')[0]
        media_name = sanitize_string(unquote(media_name))
        try:
            print(f'Downloading {media_name}')
            download(media_url, media_name, folder)
        except Exception as e:
            print(f'Error occurred while downloading {media_name}: {str(e)}')
            write_error_to_file(folder, media_name, url, str(e))

    download_tags = soup.select('ul.post__attachments > li.post__attachment > a.post__attachment-link')
    for tag in download_tags:
        download_url = tag.get('href')
        download_name = tag.get('download') or download_url.split('/')[-1].split('?')[0]
        download_name = sanitize_string(unquote(download_name))
        try:
            print(f'Downloading {download_name}')
            download(download_url, download_name, folder)
        except Exception as error:
            write_error_to_file(folder, download_name, url, str(error))

    content_div = soup.select_one('div.post__content')
    if content_div:
        content_text = ""
        for element in content_div:
            if element.name == 'a' and element.get('href'):
                link_text = element.get_text(strip=True)
                link_url = element.get('href')
                content_text += f"{link_text} --> {link_url}\n"
            else:
                content_text += str(element) + '\n'
        txt_filename = "content.txt"
        with open(os.path.join(folder, txt_filename), 'w', encoding='utf-8') as f:
            f.write(content_text)


def scrape_artist_page(artist_page: str):
    print(f'Scraping artist page {artist_page}')
    response = requests.get(artist_page)
    soup = BeautifulSoup(response.text, 'html.parser')

    artist_info = get_artist_info(soup)

    artist_name = artist_info['artist_name']
    if artist_name:
        print(f'Creating folder for artist: {artist_name.encode(sys.stdout.encoding, errors="replace").decode()}')
    else:
        print('Artist name not found. Skipping artist page.')
        return

    post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]

    total_posts_count = artist_info['number_of_posts']

    if total_posts_count == 0:
        print('No posts found for this artist.')
        return

    number_of_posts = artist_info['number_of_posts']
    print(f'{number_of_posts} posts will be downloaded. Proceed? (Y/N): ')
    user_input = input().strip().lower()

    if user_input != 'y':
        print('Download cancelled.')
        return

    for i, post_url in enumerate(post_urls):
        if i > 0:
            clear_console()
        try:
            fetch_post_media(post_url, artist_name)
        except Exception as error:
            write_error_to_file(os.path.join("Artists", artist_name), post_url, "", str(error))


def scrape_website(artist_page: str):
    print(f'Starting to scrape from {artist_page}')
    scrape_artist_page(artist_page)
    print('Finished!')


scrape_website('https://kemono.party/fanbox/user/8139991')
