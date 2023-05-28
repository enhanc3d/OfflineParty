import os
import re
import requests
import json
import time
import browser_cookie3
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote
from pathvalidate import sanitize_filename
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

metadata_filename = "metadata.json"

stop_requested = False


def fetch_session_id_cookie():
    # Load cookies from the browser

    cj = browser_cookie3.load()

    # Create a requests session
    session = requests.Session()

    # Use the cookies in the session
    session.cookies = cj

    # Extract the session cookie from the response
    session_cookie = None
    for cookie in session.cookies:
        if "kemono.party" in cookie.domain and cookie.name == 'session':
            session_cookie = cookie.value
            break

    return session_cookie


def get_favorite_artists(session):
    print("Loading cookies from browser...")

    # Fetch the favorite artists JSON
    favorites_json_url = 'https://kemono.party/api/v1/account/favorites'
    headers = {'Authorization': fetch_session_id_cookie()}

    retry_attempts = 3  # Maximum number of retry attempts
    retry_delay = 10  # Initial retry delay in seconds

    for attempt in range(1, retry_attempts + 1):
        try:
            favorites_response = session.get(favorites_json_url, headers=headers)
            favorites_response.raise_for_status()
            print("Logged in!")
            break  # Connection successful, break out of the loop
        except requests.exceptions.RequestException as e:
            print(e)
            print(f"Error trying to connect to the server, retrying in {retry_delay} seconds")
            time.sleep(retry_delay)
            retry_delay *= 3  # Exponential backoff for retry delay

            if attempt == retry_attempts:
                print("Couldn't connect to the server, please try again later.")
                return []  # Return an empty list if connection fails

    # print(favorites_response)  # Uncomment to debug the response of the page

    if favorites_response.status_code == 200:
        # Parse the JSON response
        favorites_data = favorites_response.json()

        # Extract the artist usernames from the JSON
        artist_list = []

        for artist in favorites_data:
            service = artist['service']
            id = artist['id']
            artist_list.append(f'https://kemono.party/{service}/user/{id}')

        # # Output the artist list to a text file for debugging  # Uncomment for debugging

        # with open('artist_list.txt', 'w') as f:
        #     for artist in artist_list:
        #         f.write(f'{artist}\n')

        # print(artist_list)  # Uncomment for debugging
        return artist_list
    else:
        print("Failed to fetch favorites JSON.")
        print("Error message:", favorites_response.text)
        return []  # Return an empty list if there are no favorite artists


def clear_console(artist_name):
    os.system('cls' if os.name == 'nt' else 'clear')
    if artist_name:
        print(f"Downloading posts from '{artist_name}'\n")


def make_soup(url: str) -> BeautifulSoup:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch URL: {url}")
        print(f"Error message: {str(e)}")
        return None


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


def format_content(content: str, post_url: str) -> str:
    soup = BeautifulSoup(content, 'html.parser')
    formatted_content = f"Post URL: {post_url}\n\n"
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
    soup = make_soup(artist_page)
    if soup is None:
        return None

    next_link = soup.find('a', class_='next')

    if next_link is not None:
        href = next_link.get('href')
        next_url = urljoin(artist_page, href)
        # print(next_url, "= next URL")  # Uncomment to debug
        return next_url

    return None


# ERROR OUTPUT


# def write_error_to_file(url: str, folder: str, filename: str, error: str) -> bool:
#     error_message = f"[{datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}] Error occurred while scraping {filename} from {url}: {error}\n"
#     file_path = os.path.join(folder, "scraping_errors.txt")

#     os.makedirs(folder, exist_ok=True)  # Create the folder if it doesn't exist

#     with open(file_path, 'a', encoding='utf-8') as f:
#         f.write(error_message)

#     return True


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


def fetch_post_media(url: str, artist_folder: str, artist_platform):
    global stop_requested

    soup = make_soup(url)
    if soup is None:
        return

    post_info = get_post_info(soup, url)

    post_title = post_info['post_title']
    post_date = post_info['post_date']
    folder_name = f'{post_date}_{post_title}'
    folder_name = sanitize_filename(folder_name)[:150]

    post_folder = os.path.join("Artists", artist_folder, artist_platform, folder_name)

    os.makedirs(post_folder, exist_ok=True)

    media_tags = post_info['media_tags']
    download_tags = post_info['download_tags']

    # Count of total files to download
    total_files = len(media_tags) + len(download_tags)
    # Counter for successful downloads
    successful_downloads = 0

    with ThreadPoolExecutor() as executor:
        for media_tag in media_tags:
            media_url = urljoin(url, media_tag.get('href'))
            media_name = media_tag.get('download')
            if media_name is None:
                media_name = media_url.split('/')[-1].split('?')[0]

            media_name = sanitize_filename(unquote(media_name))

            max_filename_length = 180
            if len(media_name) > max_filename_length:
                media_name = media_name[:max_filename_length]

            try:
                result = executor.submit(download,
                                         media_url,
                                         media_name,
                                         post_folder)
                if result.result():  # download returned true for success
                    successful_downloads += 1
            except Exception as e:
                print(f'Error occurred while downloading {media_name}: {str(e)}')

        for download_tag in download_tags:
            download_url = urljoin(url, download_tag.get('href'))
            download_name = download_tag.get('download')
            if download_name is None:
                download_name = download_url.split('/')[-1].split('?')[0]

            download_name = sanitize_filename(unquote(download_name))

            max_filename_length = 255
            if len(download_name) > max_filename_length:
                download_name = download_name[:max_filename_length]

            try:
                result = executor.submit(download, download_url, download_name, post_folder)
                if result.result():  # download returned true for success
                    successful_downloads += 1
            except Exception as error:
                print(error)

        # Download files from the Files section
        files_section = soup.find('div', class_='post__files')
        if files_section:
            for a_tag in files_section.find_all('a', class_='fileThumb'):
                file_url = urljoin(url, a_tag.get('href'))
                file_name = a_tag.get('download')

                # Sanitize the file name
                file_name = sanitize_filename(unquote(file_name))

                # Truncate filename if it exceeds the maximum allowed length
                max_filename_length = 255  # Windows's max length
                if len(file_name) > max_filename_length:
                    file_name = file_name[:max_filename_length]

                try:
                    result = executor.submit(download,
                                             file_url,
                                             file_name,
                                             post_folder)
                    if result.result():  # download returned true for success
                        successful_downloads += 1
                except Exception as error:
                    print(error)
    if successful_downloads < total_files:
        print(f'Not all files downloaded for post {url}. Attempted {total_files}, succeeded {successful_downloads}.')

    content_text = post_info['post_content']
    if content_text:
        formatted_content = format_content(content_text, url)  # Pass the post URL to format_content
        if formatted_content:
            txt_filename = "content.txt"
            with open(os.path.join(post_folder, txt_filename), 'w', encoding='utf-8') as f:
                f.write(formatted_content)


def download(url: str, filename: str, folder: str):
    retry_attempts = 3
    file_path = os.path.join(folder, filename)

    for attempt in range(retry_attempts):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            # print(f"Downloaded {filename} from {url}")
            return True  # Successful download
        except requests.HTTPError as err:
            print(f"HTTP error occurred: {err} - Retry {attempt + 1}")
            time.sleep(1)  # Wait for 1 second before retrying

    print(f"Failed to download {filename} from {url} after {retry_attempts} attempts")
    return False  # Failed download after retrying


def scrape_artist_page(artist_page):
    # Load metadata before starting the scraping process
    soup = make_soup(artist_page)
    if soup is None:
        print(f"Skipping invalid artist page: {artist_page}")
        return

    artist_info = get_artist_info(soup, artist_page)
    artist_name = sanitize_filename(artist_info['artist_name'])
    artist_folder = sanitize_filename(artist_info['artist_name'])
    artist_platform = sanitize_filename(artist_info['artist_platform'])

    artist_folder_path = os.path.join("Artists",
                                      artist_folder,
                                      artist_platform)

    os.makedirs(artist_folder_path, exist_ok=True)

    # Load metadata
    metadata = load_metadata(artist_folder_path)

    # Calculate number of posts to download
    total_posts = artist_info['number_of_posts']
    posts_to_download = total_posts - len(metadata)

    print(f"Downloading posts from '{artist_name}'")

    post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]
    progress_bar = tqdm(total=posts_to_download, initial=len(metadata), ncols=80)

    while len(metadata) < total_posts:
        for index, post_url in enumerate(post_urls, start=1):
            post_id_match = re.search(r'(\d+)$', post_url)
            if post_id_match is None:
                print(f'No valid post ID found in URL {post_url}. Skipping this URL.')
                continue
            post_id = post_id_match.group(0)

            # Check if the post is already in the metadata
            if post_id in metadata:
                progress_bar.update(1)  # Update progress bar even if skipping a post
                continue

            # Otherwise, process the post
            try:
                fetch_post_media(post_url, artist_folder, artist_platform)
                clear_console(artist_name)  # Clear console after downloading post
                metadata[post_id] = True  # Add the post ID to the metadata
            except Exception as e:
                print(f"Exception occurred while fetching media for post {post_url}: {e}")

            progress_bar.update(1)  # Update progress bar after processing a post
            progress_bar.set_postfix_str(f"Downloading post {len(metadata)}/{total_posts}")

        # Save metadata after each page
        save_metadata(artist_folder_path, metadata)

        # Handle next page
        next_page = get_next_page(artist_page)
        if next_page:
            artist_page = next_page
            soup = make_soup(artist_page)
            if soup is None:
                print(f"Skipping invalid artist page: {artist_page}")
                break
            # Get the new post URLs for the next page
            post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]
            progress_bar.total += len(post_urls)  # Update the Nº of posts
        else:
            break

    progress_bar.close()

    clear_console(artist_name)
    # print(f"Finished downloading posts from '{artist_name}'")


def get_artist_post_count(artist_page):
    soup = make_soup(artist_page)
    if soup is None:
        print(f"Skipping invalid artist page: {artist_page}")
        return 0, None

    artist_info = get_artist_info(soup, artist_page)
    artist_name = artist_info['artist_name']
    artist_platform = artist_info['artist_platform']
    artist_folder = sanitize_filename(artist_name)

    artist_folder_path = os.path.join("Artists",
                                      artist_folder,
                                      artist_platform)

    # Load metadata
    metadata = load_metadata(artist_folder_path)

    # Calculate number of posts to download
    total_posts = artist_info['number_of_posts']
    posts_to_download = total_posts - len(metadata)

    # print(f"Getting posts to download from {artist_name}")

    return posts_to_download, artist_name


def download_posts_from_artists(artist_list):
    global stop_requested

    # Calculate the total number of posts to download
    total_posts_to_download = 0
    artists_with_new_posts = []

    # Create a progress bar for the total download progress
    progress_bar_total = tqdm(total=len(artist_list),
                              desc="Artists",
                              leave=False, ncols=80)

    with ThreadPoolExecutor() as executor:
        results = executor.map(get_artist_post_count, artist_list)
        for posts_to_download, artist_name in results:
            if posts_to_download > 0:
                total_posts_to_download += posts_to_download
                artists_with_new_posts.append(artist_name)

            if stop_requested:
                print("Download stopped by user.")
                return

            progress_bar_total.update(1)  # Update the total progress bar

    progress_bar_total.close()  # Close the total progress bar

    # If there are posts to download, print a prompt and wait for user input
    if total_posts_to_download > 0:
        proceed = input(f"{total_posts_to_download} posts from {len(artists_with_new_posts)} artists will be downloaded, continue? (Y/N): ")
        if proceed.lower() != 'y':
            clear_console(None)
            return

        see_list = input("Do you want to see the list of artists whose posts will be downloaded? (Y/N): ")
        if see_list.lower() == 'y':
            print("Artists with new posts:")
            for artist_name in artists_with_new_posts:
                print(f" - {artist_name}")
        else:
            clear_console(None)
    else:
        print("No posts to download!")
        return

    # Create a progress bar for the current artist's posts
    progress_bar_current = tqdm(total=total_posts_to_download,
                                desc="Posts",
                                leave=False,
                                ncols=80)

    for artist_page in artist_list:
        if stop_requested:
            print("Download stopped by user.")
            return
        scrape_artist_page(artist_page)

        # Update the current artist's progress in the total progress bar
        progress_bar_total.set_postfix_str(f"Downloading from {sanitize_filename(artist_name)}")
        clear_console(None)
        progress_bar_total.update(1)

        # Update the total progress bar and close the current progress bar
        progress_bar_total.set_postfix_str("")
        progress_bar_total.set_description("Artists", refresh=True)
        progress_bar_current.close()

        # Re-create the progress bar for the next artist's posts
        progress_bar_current = tqdm(total=total_posts_to_download,
                                    desc="Posts",
                                    leave=False,
                                    ncols=80)

        progress_bar_current.set_postfix_str(f"Downloading from {sanitize_filename(artist_page)}")

    progress_bar_current.close()  # Close the current progress bar


if __name__ == '__main__':
    # Step 1: Get cookies
    session_id_cookie = fetch_session_id_cookie()

    if session_id_cookie:
        # Step 2: Log in
        session = requests.Session()
        session.cookies.set('session',
                            session_id_cookie,
                            domain='kemono.party')

        # Step 3: Get favorite artists
        favorite_artists = get_favorite_artists(session)
        clear_console(None)
        print("Calculating the number of posts to download...",
              "This could take a while!\n")

        # Execute program
        download_posts_from_artists(favorite_artists)
