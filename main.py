import os
import re
import requests
import datetime
import json
import signal
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from pathvalidate import sanitize_filename
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

metadata_filename = "metadata.json"


def clear_console(artist_name):
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"Downloading posts from '{artist_name}'\n")


def make_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def load_metadata(artist_folder):
    """Load the metadata file for the specified artist.
       If no metadata file exists, create an empty one."""
    metadata_file_path = os.path.join(artist_folder, metadata_filename)
    if not os.path.exists(metadata_file_path):
        return {}
    with open(metadata_file_path, 'r') as f:
        return json.load(f)


def save_metadata(artist_folder, metadata):
    """Save the metadata for the specified artist."""
    metadata_file_path = os.path.join(artist_folder, metadata_filename)
    with open(metadata_file_path, 'w') as f:
        json.dump(metadata, f, indent=4)


def format_content(content: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    formatted_content = ''
    for element in soup:
        if element.name == 'p':
            text = element.get_text().strip()
            if text:
                formatted_content += text + '\n\n'
        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = element.get_text().strip()
            if text:
                formatted_content += f'{text}\n{"-" * len(text)}\n\n'
        elif element.name in ['ul', 'ol']:
            list_items = element.find_all('li')
            for idx, li in enumerate(list_items, start=1):
                text = li.get_text().strip()
                if text:
                    formatted_content += f'{idx}. {text}\n'
            formatted_content += '\n'
        elif element.name == 'a':
            text = element.get_text().strip()
            href = element.get('href')
            if text and href:
                formatted_content += f'{text}: {href}\n\n'
        elif element.name == 'img':
            src = element.get('src')
            if src:
                formatted_content += f'Image: {src}\n\n'
        else:
            text = element.get_text().strip()
            if text:
                formatted_content += f'{text}\n\n'
    return formatted_content.strip()


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
            post_count_match = re.search(r'(\d+)$', post_count_text)
            if post_count_match:
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
    media_tags = soup.select('div.post__files > div.post__thumbnail > a.fileThumb')  # Images
    download_tags = soup.select('ul.post__attachments > li.post__attachment > a.post__attachment-link')  # Attached files

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
    global stop_requested

    soup = make_soup(url)
    post_info = get_post_info(soup, url)

    post_title = post_info['post_title']
    post_date = post_info['post_date']

    folder_name = f'{post_date}_{post_title}'
    folder_name = sanitize_filename(folder_name)[:150]  # Truncate the folder name to fit within path length limitations
    folder = os.path.join("Artists", artist_folder, folder_name)

    os.makedirs(folder, exist_ok=True)  # Ensure the folder is created before anything else

    media_tags = post_info['media_tags']
    download_tags = post_info['download_tags']

    # Create a ThreadPoolExecutor to manage the download tasks
    with ThreadPoolExecutor() as executor:
        # Download media files
        for media_tag in media_tags:
            media_url = urljoin(url, media_tag.get('href'))
            media_name = media_tag.get('download')
            if media_name is None:
                media_name = media_url.split('/')[-1].split('?')[0]  # fallback to old method

            media_name = sanitize_filename(unquote(media_name))

            # Truncate filename if it exceeds the maximum allowed length
            max_filename_length = 180  # Adjust this value based on your requirements
            if len(media_name) > max_filename_length:
                media_name = media_name[:max_filename_length]

            try:
                executor.submit(download, media_url, media_name, folder)
            except Exception as e:
                print(f'Error occurred while downloading {media_name}: {str(e)}')
                write_error_to_file(folder, media_name, url, str(e))

        # Download attached files
        for download_tag in download_tags:
            download_url = urljoin(url, download_tag.get('href'))
            download_name = download_tag.get('download')
            if download_name is None:
                download_name = download_url.split('/')[-1].split('?')[0]  # fallback to old method

            download_name = sanitize_filename(unquote(download_name))

            # Truncate filename if it exceeds the maximum allowed length
            max_filename_length = 255  # Adjust this value based on your requirements
            if len(download_name) > max_filename_length:
                download_name = download_name[:max_filename_length]

            try:
                executor.submit(download, download_url, download_name, folder)
            except Exception as error:
                write_error_to_file(folder, download_name, url, str(error))

        # Download files from the Files section
        files_section = soup.find('div', class_='post__files')
        if files_section:
            for a_tag in files_section.find_all('a', class_='fileThumb'):
                file_url = urljoin(url, a_tag.get('href'))
                file_name = a_tag.get('download')

                # Sanitize the file name
                file_name = sanitize_filename(unquote(file_name))

                # Truncate filename if it exceeds the maximum allowed length
                max_filename_length = 255  # Adjust this value based on your requirements
                if len(file_name) > max_filename_length:
                    file_name = file_name[:max_filename_length]

                try:
                    executor.submit(download, file_url, file_name, folder)
                except Exception as error:
                    write_error_to_file(folder, file_name, url, str(error))

    # Create content.txt if post content exists
    content_text = post_info['post_content']
    if content_text:
        formatted_content = format_content(content_text)
        if formatted_content:
            txt_filename = "content.txt"
            with open(os.path.join(folder, txt_filename), 'w', encoding='utf-8') as f:
                f.write(formatted_content)


def download(url: str, filename: str, folder: str):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        file_path = os.path.join(folder, filename)
        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
        print(f"Downloaded {filename} from {url}")
    else:
        raise Exception(f"Failed to download {filename} from {url}")


def scrape_artist_page(artist_page):
    stop_requested = False

    def handle_interrupt(signum, frame):
        nonlocal stop_requested
        stop_requested = True
        print("\nInterrupt received. Will stop after the current file is downloaded.")

    signal.signal(signal.SIGINT, handle_interrupt)

    # Load metadata before starting the scraping process
    soup = make_soup(artist_page)
    artist_info = get_artist_info(soup, artist_page)
    artist_name = artist_info['artist_name']
    artist_folder = sanitize_filename(artist_name)
    artist_folder_path = os.path.join("Artists", artist_folder)
    os.makedirs(artist_folder_path, exist_ok=True)

    # Load metadata
    metadata = load_metadata(artist_folder_path)

    # Calculate number of posts to download
    total_posts = artist_info['number_of_posts']
    posts_to_download = total_posts - len(metadata)

    # If there are posts to download, print a prompt and wait for user input
    if posts_to_download > 0:
        proceed = input(f"{posts_to_download} posts will be downloaded, continue? (Y/N): ")
        if proceed.lower() != 'y':
            return
    else:
        print("No posts to download!")
        return

    while True:
        post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]
        total_posts = len(post_urls)
        progress_bar = tqdm(total=posts_to_download)  # Initiate progress bar with total posts count

        for index, post_url in enumerate(post_urls, start=1):
            post_id_match = re.search(r'(\d+)$', post_url)
            if post_id_match is None:
                print(f'No valid post ID found in URL {post_url}. Skipping this URL.')
                continue
            post_id = post_id_match.group(0)

            # Check if the post is already in the metadata
            if post_id in metadata:
                print(f"Post {post_id} already downloaded. Skipping.")
                progress_bar.update(1)  # Update progress bar even if skipping a post
                continue

            # Otherwise, process the post
            try:
                fetch_post_media(post_url, artist_folder)
                clear_console(artist_name)  # Clear console after downloading post
                metadata[post_id] = True  # Add the post ID to the metadata

                if stop_requested:
                    print("Download stopped by user.")
                    save_metadata(artist_folder_path, metadata)
                    return
            except Exception as e:
                print(f"Exception occurred while fetching media for post {post_url}: {e}")

            progress_bar.update(1)  # Update progress bar after processing a post
            progress_bar.set_postfix_str(f"Downloading post {len(metadata)}/{posts_to_download}")

        # Save metadata after each page
        save_metadata(artist_folder_path, metadata)

        # Handle next page
        next_page = get_next_page(artist_page)
        if next_page:
            artist_page = next_page
            soup = make_soup(artist_page)
            # Get the new post URLs for the next page
            post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]
            progress_bar.total += len(post_urls)  # Update the total count of posts
        else:
            break

        # Close and recreate the progress bar with the updated total count
        progress_bar.close()
        progress_bar = tqdm(total=posts_to_download)
        progress_bar.set_postfix_str(f"Downloading post {len(metadata)}/{posts_to_download}")

    progress_bar.close()
    clear_console(artist_name)
    print(f"Done! Files saved in {artist_folder_path}")


if __name__ == '__main__':
    artist_page = 'https://kemono.party/patreon/user/8497568'
    scrape_artist_page(artist_page)
