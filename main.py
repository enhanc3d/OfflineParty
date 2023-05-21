import os
import sys
import re
import requests
import string
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from urllib.parse import unquote


def sanitize_string(s):
    # Remove any leading/trailing spaces
    s = s.strip()

    # Remove invalid characters using regex
    s = re.sub(r'[<>:"/\\|?*\x00-\x1F]', '', s)

    # Remove trailing periods and whitespaces
    s = s.rstrip('. ')

    # Limit the maximum length of the string to 255 characters
    s = s[:255]

    return s  # Add this line to return the sanitized string


def download_file(url, filename, folder):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_string(unquote(filename))

    # Replace unsupported characters with an underscore
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c if c in valid_chars else '_' for c in filename)

    if os.path.exists(os.path.join(folder, filename)):
        print(f'File {filename} already exists in {folder}, skipping download.')
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


def download_media(url, artist_folder, total_posts):
    print(f'Downloading media from {url}')
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    post_title = sanitize_string(soup.select_one('h1.post__title > span').get_text(strip=True))
    post_date = soup.select_one('div.post__published > time').get('datetime').split()[0]
    folder = os.path.join("Artists", artist_folder, f'{post_date}_{post_title}')
    os.makedirs(folder, exist_ok=True)  # Ensure the folder is created before anything else

    media_tags = soup.select('div.post__files > div.post__thumbnail > a.fileThumb')
    for index, tag in enumerate(media_tags, start=1):
        media_url = tag.get('href')
        media_name = tag.get('download') or media_url.split('/')[-1].split('?')[0]
        media_name = sanitize_string(unquote(media_name))
        try:
            percentage = int((index / total_posts) * 100)
            print(f'Downloading {media_name} ({index} of {total_posts} -- {percentage}%)')
            download_file(media_url, media_name, folder)
        except Exception as e:
            print(f'Error occurred while downloading {media_name}: {str(e)}')
            write_error_to_file(folder, media_name, url)

    download_tags = soup.select('ul.post__attachments > li.post__attachment > a.post__attachment-link')
    for tag in download_tags:
        download_url = tag.get('href')
        download_name = tag.get('download') or download_url.split('/')[-1].split('?')[0]
        download_name = sanitize_string(unquote(download_name))
        try:
            print(f'Downloading {download_name}')
            download_file(download_url, download_name, folder)
        except Exception as e:
            print(f'Error occurred while downloading {download_name}: {str(e)}')
            write_error_to_file(folder, download_name, url)

    # Get all content and save to a .txt file
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


def write_error_to_file(folder, filename, url):
    error_filename = "scraping_errors.txt"
    error_message = f"[{datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}] Error occurred while scraping: {filename} from {url}\n"
    with open(os.path.join(".", error_filename), 'a', encoding='utf-8') as f:
        f.write(error_message)


def write_latest_downloaded_post(artist_page, post_page):
    latest_downloaded_posts_file = "latest_downloaded_posts.txt"
    artist_name = get_artist_name(artist_page)
    timestamp = get_post_timestamp(post_page)
    if artist_name and timestamp:
        with open(latest_downloaded_posts_file, 'a', encoding='utf-8') as f:
            f.write(f"{artist_name},{timestamp}\n")


def get_artist_name(artist_page):
    response = requests.get(artist_page)
    soup = BeautifulSoup(response.text, 'html.parser')
    artist_name = soup.select_one('span[itemprop="name"]')
    if artist_name:
        return sanitize_string(artist_name.get_text(strip=True))
    return None


def get_post_timestamp(post_page):
    response = requests.get(post_page)
    soup = BeautifulSoup(response.text, 'html.parser')
    post_timestamp = soup.find('meta', attrs={'name': 'published'})
    if post_timestamp:
        return post_timestamp.get('content')
    return None


def get_total_posts_count(soup):
    post_count_element = soup.select_one('div.paginator > small')
    if post_count_element:
        post_count_text = post_count_element.get_text(strip=True)
        post_count_match = re.search(r'\d+$', post_count_text)
        if post_count_match:
            return int(post_count_match.group())

    # Fallback: Count the number of article elements
    articles = soup.select('article.post-card, article.post-card--preview')
    if articles:
        print(f'Counted {len(articles)} article elements:')
        for article in articles:
            print(str(article)[:100])  # print a portion of each element
        return len(articles)

    # If neither method found a count, return None or an appropriate value
    return None


def get_latest_downloaded_post_count(artist_name):
    latest_downloaded_posts_file = "latest_downloaded_posts.txt"
    with open(latest_downloaded_posts_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in reversed(lines):
            line = line.strip()
            if line.startswith(artist_name):
                post_count_match = re.search(r'\d+$', line)
                if post_count_match:
                    return int(post_count_match.group())
    return 0


def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')


def update_latest_downloaded_post_count(artist_name, downloaded_post_count):
    latest_downloaded_posts_file = "latest_downloaded_posts.txt"
    with open(latest_downloaded_posts_file, 'a', encoding='utf-8') as f:
        f.write(f"{artist_name},{downloaded_post_count}\n")


def scrape_artist_page(artist_page):
    print(f'Scraping artist page {artist_page}')
    response = requests.get(artist_page)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Get artist name
    artist_name = get_artist_name(artist_page)
    if artist_name:
        print(f'Creating folder for artist: {artist_name.encode(sys.stdout.encoding, errors="replace").decode()}')
    else:
        print('Artist name not found. Skipping artist page.')
        return

    post_pages = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]

    latest_downloaded_post_count = get_latest_downloaded_post_count(artist_name)
    
    total_posts_count = len(post_pages)  # Simply use the length of post_pages

    if total_posts_count == 0:
        print('No posts found for this artist. Skipping artist page.')
        return

    new_posts_count = total_posts_count - latest_downloaded_post_count

    print(f'{new_posts_count} new posts will be downloaded. Proceed? (Y/N): ')
    user_input = input().strip().lower()

    if user_input != 'y':
        print('Download cancelled.')
        return

    downloaded_post_count = 0  # Add a counter for downloaded posts
    for i, post_page in enumerate(post_pages):
        if i > 0:
            clear_console()  # Clear console after the first post
        try:
            download_media(post_page, artist_name, new_posts_count)
            write_latest_downloaded_post(artist_page, post_page)
            downloaded_post_count += 1  # Increase counter when a post is successfully downloaded
        except Exception as e:
            print(f'Error occurred while scraping post {post_page}: {str(e)}')
            write_error_to_file(os.path.join("Artists", artist_name), post_page)

    # Update the total downloaded post count in the file after scraping all posts
    update_latest_downloaded_post_count(artist_name, downloaded_post_count)



def scrape_website(base_url):
    print(f'Starting to scrape from {base_url}')
    # if base_url is an artist page, directly scrape this page
    if 'user' in base_url:
        scrape_artist_page(base_url)
    else:
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # You might have to adjust this depending on how to find artist pages
        artist_pages = [urljoin(base_url, tag.get('href')) for tag in soup.select('div.artist-card > a')]
        for artist_page in artist_pages:
            scrape_artist_page(artist_page)
    print('Finished!')


# To run
scrape_website('https://kemono.party/fanbox/user/8139991')
