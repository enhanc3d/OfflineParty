import os
import sys
import re
import requests
import string
import datetime
import subprocess
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse, urlunparse


def clear_console():
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)


def sanitize_string(s):
    # Remove any leading/trailing spaces
    s = s.strip()

    # Remove invalid characters using regex
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', s)

    # Remove trailing periods and whitespaces
    s = s.rstrip('. ')

    # Replace unsupported characters with an underscore
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c if c in valid_chars else '_' for c in s)

    # Limit the maximum length of the string to 255 characters
    s = s[:255]

    return s  # Returns the sanitized string


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


def get_artist_info(soup: BeautifulSoup, artist_page: str) -> dict:

    def get_artist_name(artist_page):
        response = requests.get(artist_page)
        soup = BeautifulSoup(response.text, 'html.parser')
        artist_name = soup.select_one('span[itemprop="name"]')
        if artist_name:
            return sanitize_string(artist_name.get_text(strip=True))
        return None

    artist_name = get_artist_name(artist_page)
    number_of_posts = get_total_posts_count(soup)
    artist_platform_element = soup.select_one('meta[name="service"]')
    artist_platform = artist_platform_element.get('content') if artist_platform_element else None

    artist_info = {
        'artist_name': artist_name,
        'number_of_posts': number_of_posts,
        'artist_platform': artist_platform,
    }

    return artist_info


def download(url: str, filename: str, folder):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_string(unquote(filename))

    # Replace unsupported characters with an underscore
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c if c in valid_chars else '_' for c in filename)

    if os.path.exists(os.path.join(folder, filename)):
        print(f'File {filename} already exists in {folder}, skipping')
        return filename

    # Encode the filename using URL encoding
    filename_encoded = filename.encode('utf-8', errors='ignore').decode('utf-8')
    filename_encoded = filename_encoded.replace('/', '-')  # Replace slashes with hyphens for compatibility
    filename_encoded = filename_encoded[:255]  # Truncate the filename to a reasonable length
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
    os.makedirs(folder, exist_ok=True)  # Ensure the folder is created before anything else

    media_tags = soup.select('div.post__files > div.post__thumbnail > a.fileThumb') # Images
    for tag in media_tags:
        media_url = tag.get('href')
        media_name = tag.get('download') or media_url.split('/')[-1].split('?')[0]
        media_name = sanitize_string(unquote(media_name))
        try:
            print(f'Downloading {media_name}')
            download(media_url, media_name, folder)
        except Exception as e:
            print(f'Error occurred while downloading {media_name}: {str(e)}')
            write_error_to_file(folder, media_name, url, str(e))

    download_tags = soup.select('ul.post__attachments > li.post__attachment > a.post__attachment-link') # Attached files
    for tag in download_tags:
        download_url = tag.get('href')
        download_name = tag.get('download') or download_url.split('/')[-1].split('?')[0]
        download_name = sanitize_string(unquote(download_name))
        try:
            print(f'Downloading {download_name}')
            download(download_url, download_name, folder)
        except Exception as error:
            write_error_to_file(folder, download_name, url, str(error))

    # Content text from the posts gets saved to a .txt file

    content_div = soup.select_one('div.post__content')
    if content_div:
        content_text = ""
        for element in content_div:
            if element.name == 'a' and element.get('href'):
                # Extract text and URL of hyperlink
                link_text = element.get_text(strip=True)
                link_url = element.get('href')
                content_text += f"{link_text} --> {link_url}\n"
            else:
                content_text += str(element) + '\n'
        txt_filename = "content.txt"
        with open(os.path.join(folder, txt_filename), 'w', encoding='utf-8') as f:
            f.write(content_text)


# Function to save latest post data to a JSON file
def save_latest_post_data(artist: str, id: int, date: str, directory: str):
    data = {'post_id': id, 'date': date, 'directory': directory}
    all_data = {}

    # If the JSON file already exists, load its current contents
    if os.path.exists('latest_post_data.json'):
        with open('latest_post_data.json', 'r') as json_file:
            all_data = json.load(json_file)
    # If this artist is not in the JSON file, add an empty list
    if artist not in all_data:
        all_data[artist] = []
    # Append the new post data
    all_data[artist].append(data)

    # Save the new JSON data
    with open('latest_post_data.json', 'w') as json_file:
        json.dump(all_data, json_file, indent=4)  # Added indent argument


# Function to load latest post data from a JSON file
def load_latest_post_data(artist: str):
    data = {}

    # If the JSON file does not exist, return None values
    if not os.path.exists("latest_post_data.json"):
        return None, None, None

    with open("latest_post_data.json", 'r') as f:
        data = json.load(f)

    # If the artist is not in the JSON file, return None values
    if artist not in data:
        return None, None, None

    # Get the last post for this artist
    last_post = data[artist][-1]
    return last_post.get('post_id', None), last_post.get('date', None), last_post.get('directory', None)


def scrape_artist_page(artist_page):

    parsed_url = urlparse(artist_page)
    artist_page = urlunparse(parsed_url._replace(query=''))

    print(f'Scraping artist page {artist_page}')
    response = requests.get(artist_page)
    soup = BeautifulSoup(response.text, 'html.parser')

    artist_info = get_artist_info(soup, artist_page)

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

    # Load the saved latest post data
    latest_post_id, latest_post_date, latest_post_dir = load_latest_post_data(artist_name)

    new_post_urls = []
    for url in post_urls:
        # Extract the post ID from the URL
        post_id_match = re.search(r'(\d+)$', url)
        if post_id_match is not None:
            post_id = int(post_id_match.group(1))
        else:
            print(f'No valid post ID found in URL {url}. Skipping this URL.')
            continue

        # If the post is newer than the latest saved post, fetch its media
        if not latest_post_id or post_id > latest_post_id:
            new_post_urls.append(url)
        elif post_id <= latest_post_id:
            print("Stopping downloads - this post has been downloaded previously.")
            break

    number_of_new_posts = len(new_post_urls)
    if number_of_new_posts != 0:
        print(f'{number_of_new_posts} new posts will be downloaded. Proceed? (Y/N): ')
        user_input = 'y'  # input().strip().lower()
        if user_input != 'y':
            print('Download cancelled.')
            return
    else:
        print("No new posts to download!")
        return

    # Bool flag to check if it is the first post
    first_post = True

    for i, post_url in enumerate(new_post_urls):
        if i > 0:
            clear_console()
        try:
            fetch_post_media(post_url, artist_name)
            # Get new soup object for each post
            response = requests.get(post_url)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract post date and title to form directory name
            post_title = sanitize_string(soup.select_one('h1.post__title > span').get_text(strip=True))
            post_date = soup.select_one('div.post__published > time').get('datetime').split()[0]
            post_directory = os.path.join("Artists", artist_name, f'{post_date}_{post_title}')

            # Extract the post ID from the URL
            post_id_match = re.search(r'(\d+)$', post_url)
            if post_id_match is not None:
                post_id = int(post_id_match.group(1))
            else:
                print(f'No valid post ID found in URL {post_url}. Skipping this URL.')
                continue

            if first_post:
                # Save the latest post data
                save_latest_post_data(artist_name, post_id, post_date, post_directory)
                first_post = False
        except Exception as e:
            print(f"Exception occurred while fetching media for post {post_url}: {e}")
            break

        print(f'Finished downloading post {i+1} of {number_of_new_posts}.')

    print('Finished scraping artist page.')


if __name__ == '__main__':
    artist_page = 'https://kemono.party/fanbox/user/41738951'
    scrape_artist_page(artist_page)
