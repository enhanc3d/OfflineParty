import os
import re
import requests
import string
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from pathvalidate import sanitize_filename
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


def clear_console(artist_name):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Downloading posts from '{artist_name}'\n")


def make_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def get_next_page(artist_page):
    response = requests.get(artist_page)
    soup = BeautifulSoup(response.content, 'html.parser')
    next_link = soup.find('a', class_='next')

    if next_link is not None:
        href = next_link.get('href')
        next_url = urljoin(artist_page, href)
        print(next_url, "= next URL")
        return next_url

    return None


# ERROR OUTPUT


def write_error_to_file(folder: str, filename: str, url: str, error: str):
    error_filename = "scraping_errors.txt"
    error_message = f"[{datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}] Error occurred while scraping {filename} from {url}: {error}\n"
    file_path = os.path.join(folder, error_filename)

    os.makedirs(folder, exist_ok=True)  # Create the folder if it doesn't exist

    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(error_message)


# DATA GATHERING


def get_artist_info(soup: BeautifulSoup, artist_page: str) -> dict:

    def get_artist_name(artist_page):
        soup = make_soup(artist_page)
        artist_name_meta = soup.select_one('meta[name="artist_name"]')
        if artist_name_meta and 'content' in artist_name_meta.attrs:
            return sanitize_filename(artist_name_meta['content'])
        return None

    def get_number_of_posts(soup: BeautifulSoup) -> int:
        post_count_element = soup.select_one('div.paginator > small')
        if post_count_element:
            post_count_text = post_count_element.get_text(strip=True)
            post_count_match = re.search(r'\d+$', post_count_text)
            if post_count_match:
                # print(f'{int(post_count_match.group())} articles found')
                return int(post_count_match.group())
        articles = soup.select('article.post-card, article.post-card--preview')
        if articles:
            return len(articles)
        return None

    artist_name = get_artist_name(artist_page)
    number_of_posts = get_number_of_posts(soup)
    artist_platform_element = soup.select_one('meta[name="service"]')
    artist_platform = artist_platform_element.get('content') if artist_platform_element else None

    artist_info = {
        'artist_name': artist_name,
        'number_of_posts': number_of_posts,
        'artist_platform': artist_platform,
        'number_of_posts': number_of_posts,
    }

    return artist_info


def get_post_info(soup: BeautifulSoup, url: str) -> dict:
    """Gather information from a post."""

    # Gather the post title
    post_title = soup.select_one('h1.post__title > span')
    post_title = sanitize_filename(post_title.get_text(strip=True)) if post_title else None

    # Gather the post date
    post_date = soup.select_one('div.post__published > time')
    post_date = post_date.get('datetime').split()[0] if post_date else None

    # Gather the post content
    content_div = soup.select_one('div.post__content')
    content_text = ""
    if content_div:
        for element in content_div:
            if element.name == 'a' and element.get('href'):
                # Extract text and URL of hyperlink
                link_text = element.get_text(strip=True)
                link_url = element.get('href')
                content_text += f"{link_text} --> {link_url}\n"
            else:
                content_text += str(element) + '\n'

    # Gather media associated with the post
    media_tags = soup.select('div.post__files > div.post__thumbnail > a.fileThumb') # Images
    download_tags = soup.select('ul.post__attachments > li.post__attachment > a.post__attachment-link') # Attached files

    # Extract the post ID from the URL
    post_id_match = re.search(r'(\d+)$', url)
    post_id = int(post_id_match.group(1)) if post_id_match else None

    post_info = {
        'post_title': post_title,
        'post_date': post_date,
        'post_content': content_text,
        'media_tags': media_tags,
        'download_tags': download_tags,
        'post_id': post_id,
    }

    return post_info


def fetch_post_media(url: str, artist_folder: str):

    soup = make_soup(url)
    post_info = get_post_info(soup, url)

    post_title = post_info['post_title']
    post_date = post_info['post_date']

    folder = os.path.join("Artists", artist_folder, f'{post_date}_{post_title}')
    os.makedirs(folder, exist_ok=True)  # Ensure the folder is created before anything else

    media_tags = post_info['media_tags']
    download_tags = post_info['download_tags']

    # Create a ThreadPoolExecutor to manage the download tasks
    with ThreadPoolExecutor() as executor:
        # Download media files
        for media_tag in media_tags:
            media_url = urljoin(url, media_tag.get('href'))
            media_name = media_url.split('/')[-1].split('?')[0]
            media_name = sanitize_filename(unquote(media_name))
            try:
                executor.submit(download, media_url, media_name, folder)
            except Exception as e:
                print(f'Error occurred while downloading {media_name}: {str(e)}')
                write_error_to_file(folder, media_name, url, str(e))

        # Download attached files
        for download_tag in download_tags:
            download_url = urljoin(url, download_tag.get('href'))
            download_name = download_url.split('/')[-1].split('?')[0]
            download_name = sanitize_filename(unquote(download_name))
            try:
                executor.submit(download, download_url, download_name, folder)
            except Exception as error:
                write_error_to_file(folder, download_name, url, str(error))

    # Content text from the posts gets saved to a .txt file
    content_text = post_info['post_content']
    txt_filename = "content.txt"
    with open(os.path.join(folder, txt_filename), 'w', encoding='utf-8') as f:
        f.write(content_text)




def download(url: str, filename: str, folder):
    os.makedirs(folder, exist_ok=True)
    filename = sanitize_filename(unquote(filename))

    # Replace unsupported characters with an underscore
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    filename = ''.join(c if c in valid_chars else '_' for c in filename)

    if os.path.exists(os.path.join(folder, filename)):
        print(f'File {filename} already exists in {folder}, skipping')
        return filename

    # print(f'Saving {filename} to {folder}')
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(folder, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def scrape_artist_page(artist_page):
    while True:
        soup = make_soup(artist_page)
        artist_info = get_artist_info(soup, artist_page)

        artist_name = artist_info['artist_name']
        artist_folder = sanitize_filename(artist_name)
        artist_folder_path = os.path.join("Artists", artist_folder)
        os.makedirs(artist_folder_path, exist_ok=True)
        
        print(f"Downloading posts from {artist_name}")  # Print the artist name here

        post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]
        total_posts = len(post_urls)
        progress_bar = tqdm(total=total_posts)

        for index, post_url in enumerate(post_urls, start=1):
            post_id_match = re.search(r'(\d+)$', post_url)
            if post_id_match is None:
                print(f'No valid post ID found in URL {post_url}. Skipping this URL.')
                continue
            try:
                fetch_post_media(post_url, artist_folder)
                clear_console(artist_name)  # Pass artist_name to clear_console() here
            except Exception as e:
                print(f"Exception occurred while fetching media for post {post_url}: {e}")

            progress_bar.update(1)  # Increment progress bar
            progress_bar.set_postfix_str(f"Downloading post {index}/{total_posts}")

        progress_bar.close()  # Close progress bar

        next_page = get_next_page(artist_page)
        if next_page:
            artist_page = next_page
        else:
            break
    print(f"Done! Files saved in {artist_folder_path}")


if __name__ == '__main__':
    artist_page = 'https://kemono.party/fanbox/user/41738951'
    scrape_artist_page(artist_page)