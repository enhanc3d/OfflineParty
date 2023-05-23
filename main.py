import os
import re
import requests
import string
import datetime
import subprocess
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote, urlparse, urlunparse
from pathvalidate import sanitize_filename


def clear_console():
    subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)


def make_soup(url: str) -> BeautifulSoup:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup


def get_new_posts(artist_id, artist_page):
    soup = make_soup(artist_page)
    artist_uploaded = False
    artist_info = get_artist_info(soup, artist_page)

    artist_total_posts = artist_info['number_of_posts']

    # If the JSON file does not exist or is empty, return the current total posts
    if not os.path.exists("latest_post_data.json") or os.stat("latest_post_data.json").st_size == 0:
        # Create an empty JSON file with '{}' as the initial content
        with open("latest_post_data.json", 'w') as f:
            f.write('{}')
        return artist_total_posts, artist_uploaded

    with open("latest_post_data.json", 'r') as f:
        data = json.load(f)

    # If the artist is not in the JSON file, return the current total posts
    if artist_id not in data:
        return artist_total_posts, artist_uploaded

    downloaded_posts = data[artist_id].get('number_of_posts', 0)
    print(downloaded_posts, "downloaded posts")

    new_posts = artist_total_posts - downloaded_posts
    print(new_posts, "new posts")

    if new_posts != 0:
        artist_uploaded = True

    return new_posts, artist_uploaded


# JSON MANAGEMENT FUNCTIONS #

def save_latest_post_data(artist: str, id: int, date: str, number_of_posts: int, 
                          last_downloaded_post: str, downloaded_posts: int, first_post: bool):
    
    all_data = {}

    # If the JSON file already exists, load its current contents
    if os.path.exists('latest_post_data.json'):
        with open('latest_post_data.json', 'r') as json_file:
            all_data = json.load(json_file)

    # If this artist is not in the JSON file, add an empty dictionary
    if artist not in all_data:
        all_data[artist] = {}

    # Based on the value of first_post, we decide which data to update
    if first_post:
        # For the first post, we update all fields
        data = {'post_id': id, 'date': date, 'number_of_posts': number_of_posts, 
                'last_downloaded_post': last_downloaded_post, 'downloaded_posts': downloaded_posts}
    else:
        # For subsequent posts, we only update last_downloaded_post and downloaded_posts
        data = {'post_id': all_data[artist]['post_id'], 
                'date': all_data[artist]['date'], 
                'number_of_posts': all_data[artist]['number_of_posts'], 
                'last_downloaded_post': last_downloaded_post, 
                'downloaded_posts': downloaded_posts}

    # Append the new post data
    all_data[artist] = data

    # Save the new JSON data with proper encoding
    with open('latest_post_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(all_data, json_file, indent=4, ensure_ascii=False)  # Set ensure_ascii=False



def load_latest_post_data(artist: str):
    data = {}

    # If the JSON file does not exist, return None values
    if not os.path.exists("latest_post_data.json") or os.stat("latest_post_data.json").st_size == 0:
        return None, 0

    with open("latest_post_data.json", 'r') as f:
        data = json.load(f)

    # If the artist is not in the JSON file, return None values
    if artist not in data:
        return None, 0

    # Get the post data for this artist
    artist_data = data[artist]
    return artist_data.get('post_id', None), artist_data.get('downloaded_posts', 0)


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

    def get_artist_id(artist_page):
        soup = make_soup(artist_page)
        artist_name_meta = soup.select_one('meta[name="id"]')
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
    artist_id = get_artist_id(artist_page)
    number_of_posts = get_number_of_posts(soup)
    artist_platform_element = soup.select_one('meta[name="service"]')
    artist_platform = artist_platform_element.get('content') if artist_platform_element else None

    artist_info = {
        'artist_id': artist_id,
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
    print(f'Downloading media from {url}')

    soup = make_soup(url)
    post_info = get_post_info(soup, url)

    post_title = post_info['post_title']
    post_date = post_info['post_date']

    folder = os.path.join("Artists", artist_folder, f'{post_date}_{post_title}')
    os.makedirs(folder, exist_ok=True)  # Ensure the folder is created before anything else

    media_tags = post_info['media_tags']
    for media_tag in media_tags:
        media_url = urljoin(url, media_tag.get('href'))
        media_name = media_url.split('/')[-1].split('?')[0]
        media_name = sanitize_filename(unquote(media_name))
        try:
            print(f'Downloading {media_name}')
            download(media_url, media_name, folder)
        except Exception as e:
            print(f'Error occurred while downloading {media_name}: {str(e)}')
            write_error_to_file(folder, media_name, url, str(e))

    download_tags = post_info['download_tags']
    for download_tag in download_tags:
        download_url = urljoin(url, download_tag.get('href'))
        download_name = download_url.split('/')[-1].split('?')[0]
        download_name = sanitize_filename(unquote(download_name))
        try:
            print(f'Downloading {download_name}')
            download(download_url, download_name, folder)
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

    print(f'Saving {filename} to {folder}')
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(folder, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def scrape_artist_page(artist_page):
    soup = make_soup(artist_page)

    parsed_url = urlparse(artist_page)
    artist_page = urlunparse(parsed_url._replace(query=''))

    artist_info = get_artist_info(soup, artist_page)

    artist_name = artist_info['artist_name']
    artist_id = artist_info['artist_id']
    number_of_posts = artist_info['number_of_posts']

    print(f'Scraping artist page for "{artist_name}"')

    if artist_id:
        artist_folder = sanitize_filename(artist_name)
        artist_folder_path = os.path.join("Artists", artist_folder)
        if os.path.exists(artist_folder_path):
            print(f'Artist folder already exists: {artist_folder}')
        else:
            print(f'Creating folder for artist: {artist_folder}')
            os.makedirs(artist_folder_path)

        post_urls = [urljoin(artist_page, tag.get('href')) for tag in soup.select('article.post-card > a, article.post-card--preview > a')]

        total_posts_count = artist_info['number_of_posts']

        if total_posts_count == 0:
            print('No posts found for this artist.')
            return

       # Load the saved latest post id and downloaded_posts count
        latest_post_id, downloaded_posts = load_latest_post_data(artist_id)

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
            if latest_post_id is None or post_id > latest_post_id:
                new_post_urls.append(url)
            elif post_id <= latest_post_id:
                break

        # Get the number of new posts and if artist uploaded any content
        number_of_new_posts, artist_uploaded = get_new_posts(artist_id, artist_page)

        if number_of_new_posts > 0:
            if artist_uploaded:
                print(f'{number_of_new_posts} new posts will be downloaded. Proceed? (Y/N): ')
            else:
                print(f'{number_of_new_posts} posts will be downloaded. Proceed? (Y/N): ')
            user_input = input().strip().lower()
            if user_input != 'y':
                print('Download cancelled.')
                return
        else:
            print("No new posts to download!")
            return

        # Bool flag to check if it is the first post
        # Runs once in the first loop
        first_post = True

        for i, post_url in enumerate(new_post_urls):
            if i > 0:
                clear_console()
            try:
                fetch_post_media(post_url, artist_folder)

                # Get post info
                soup = make_soup(post_url)
                post_info = get_post_info(soup, post_url)
                post_date = post_info['post_date']

                # Extract the post ID from the URL
                post_id_match = re.search(r'(\d+)$', post_url)
                if post_id_match is not None:
                    post_id = int(post_id_match.group(1))
                else:
                    print(f'No valid post ID found in URL {post_url}. Skipping this URL.')
                    continue

                if first_post:
                    # Save the latest post data
                    save_latest_post_data(artist_id,
                              post_id,
                              post_date,
                              number_of_posts,
                              post_url,
                              downloaded_posts + i + 1,
                              first_post)
                    first_post = False
                else:
                    # Update only post_url and downloaded_posts
                    save_latest_post_data(artist_id,
                              post_id,
                              post_date,
                              number_of_posts,
                              post_url,
                              downloaded_posts + i + 1,
                              first_post)
            except Exception as e:
                print(f"Exception occurred while fetching media for post {post_url}: {e}")
                break

            print(f'Finished downloading post {i+1} of {number_of_new_posts}.')

    print('Finished scraping artist page.')


if __name__ == '__main__':
    artist_page = 'https://kemono.party/patreon/user/22757225'
    scrape_artist_page(artist_page)
