import os
import sys
import time
import json
import requests
import argparse
import html2text
import get_favorites
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
from pathvalidate import sanitize_filename
from user_search import main as user_search
from json_handling import lookup_and_save_user as save_artist_json
from discord_download import scrape_discord_server as discord_download


# Map Kemono artist IDs to their names
def create_artist_id_to_name_mapping(data):
    if isinstance(data, dict):
        if "id" in data and "name" in data:
            return {data["id"]: data["name"].capitalize()}
        else:
            return {}
    elif isinstance(data, list):
        return {item["id"]: item["name"].capitalize() for item in data if isinstance(item, dict) and "id" in item and "name" in item}
    else:
        return {}  # Return an empty dictionary for unsupported data types


def read_user_txt_list():
    dir_path = 'Config'  # Relative path to the current directory
    file_name = 'user_list.txt'
    file_path = os.path.join(dir_path, file_name)
    user_list = []

    # Create the directory if it does not exist
    if not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as e:
            print(f"Could not create directory {dir_path}. Error: {e}")
            return

    # Check if the file exists
    if os.path.exists(file_path):
        # If it exists, read the usernames from it
        with open(file_path, 'r', encoding='utf-8') as user_list_file:
            user_list = [line.strip() for line in user_list_file.readlines() if line.strip()]
    else:
        # If it doesn't exist, create it
        with open(file_path, 'w', encoding='utf-8') as user_list_file:
            print(f"{file_path} created.")

    # Iterate through the list of usernames
    for username in user_list:
        # Call user_search to get artist information
        urls, labels, json_data = user_search(username)
        artist_id_to_name = create_artist_id_to_name_mapping(json_data)

        print(f"Downloading data for {username.capitalize()}")

        # Call run_with_base_url with the list of URLs directly
        run_with_base_url(urls, artist_id_to_name, json_data)


def clear_console(artist_name_id_or_url, channel_name=None):
    if artist_name_id_or_url is None:
        artist_name_id_or_url = "Unknown Artist"  # Add a default value
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{'='*(len(artist_name_id_or_url)+24)}")
    if channel_name:
        print(f"Downloading posts from: {artist_name_id_or_url} in channel: {channel_name}")
    else:
        print(f"Downloading posts from: {artist_name_id_or_url}")
    print(f"{'='*(len(artist_name_id_or_url)+24)}\n")


# Function to read downloaded posts list from .json file
def read_downloaded_posts_list(platform_folder):
    file_path = os.path.join(platform_folder, "downloaded_posts.json")
    downloaded_posts = set()
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            downloaded_posts = set(json.load(file))
    return downloaded_posts

# Function to write downloaded post IDs to .json file
def write_downloaded_post(platform_folder, downloaded_posts):
    file_path = os.path.join(platform_folder, "downloaded_posts.json")
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(list(downloaded_posts), file, ensure_ascii=False, indent=4)


def get_post_folder_name(post):
    # Get the post title and strip any whitespace or newline characters
    title = post.get('title', '').strip()

    # Get the published date or fallback to the added date
    date = post.get('published') or post.get('added')

    # If there's no title, use the post's id
    if not title:
        title = post.get('id', 'Unknown')

    # If there's a date, append it to the title
    if date:
        return sanitize_filename(f"{title}_{date}")
    else:
        return sanitize_filename(title)


def sanitize_attachment_name(name):
    # Remove any URL components
    name = name.replace("https://", "").replace("http://", "")
    # Further sanitize the name to remove invalid characters
    return sanitize_filename(name)


def get_with_retry(url, retries=5, stream=False, timeout=30, delay=30):
    for i in range(retries):
        try:
            response = requests.get(url, stream=stream, timeout=timeout)
            response.raise_for_status()
            return response
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
            print(f"Failed to get {url}, attempt {i + 1}")
            if i < retries - 1:
                print(f"Waiting for {delay} seconds before retrying.")
                time.sleep(delay)  # Wait for 'delay' seconds before the next retry
            else:
                print(f"Failed to download {url}, logging to errors.txt")
                current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current date and time
                with open("errors.txt", 'a') as error_file:
                    error_line = f"{current_date} - {url} -- {str(e)}\n"  # Include the current date and time
                    error_file.write(error_line)
                return None  # Explicitly return None if all retries fail


def download_file(url, folder_name, file_name, artist_url, artist_name=None):
    try:
        folder_path = os.path.join(folder_name, file_name)
        temp_folder_path = os.path.join(folder_name, file_name + ".temp")

        # If a temporary file exists, remove it to restart the download
        if os.path.exists(temp_folder_path):
            os.remove(temp_folder_path)

        # If the final file exists, skip the download
        if os.path.exists(folder_path):
            print(f"Skipping download: {file_name} already exists")
            return True  # Indicate that download is not needed (file already exists)

        response = get_with_retry(url, stream=True)
        if response is None:  # Check for None returned by get_with_retry
            return False  # Indicate download failure

        if response and response.status_code == 200:
            total_size_in_bytes = int(response.headers.get('content-length', 0))
            progress_bar = tqdm(total=total_size_in_bytes,
                                unit='iB',
                                unit_scale=True,
                                leave=True,
                                desc=file_name)

            # Use a temporary file for the download process
            with open(temp_folder_path, 'wb') as f:
                for data in response.iter_content(1024):
                    progress_bar.update(len(data))
                    f.write(data)

            progress_bar.close()

            # Rename the temporary file to the final file name
            os.rename(temp_folder_path, folder_path)

            if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                print("ERROR, something went wrong")
                return False

            print(f"Finished downloading: {file_name} from {artist_url}")
            clear_console(artist_name or artist_url)  # Use artist_name if available, otherwise use artist_url

            return True  # Indicate download success
        else:
            return False  # Indicate download failure
    except Exception as e:
        print(f"An error occurred while downloading {file_name}: {str(e)}")
        return False  # Indicate download failure



def run_with_base_url(url_list, data, json_file):
    processed_users = set()
    current_artist = None
    current_artist_url = None
    previous_url = None  # Initialize previous_url
    previous_artist_id = None  # Initialize previous_artist_id

    try:
        all_downloaded_posts = set()  # Initialize a set to store all downloaded post IDs

        for i, url in enumerate(tqdm(url_list, desc="Downloading pages...")):
            url_parts = url.split("/")
            if len(url_parts) < 7:
                print(f"Unexpected URL structure: {url}")
                continue

            domain = url_parts[2].split(".")[0].capitalize()
            service = url_parts[5].capitalize()
            artist_id = url_parts[7].split("?")[0]
            artist_name = data.get(artist_id, None)

            if artist_name:
                artist_name = artist_name.capitalize()
            else:
                print(f"Artist ID {artist_id} not found in data.")
                continue

            # Clear the console and show the artist name
            clear_console(artist_name)

            if service == 'Discord':
                discord_download(artist_id)
                continue

            artists_folder = "Creators"
            domain_folder = os.path.join(artists_folder, domain)
            artist_folder = os.path.join(domain_folder, sanitize_filename(artist_name))
            platform_folder = os.path.join(artist_folder, sanitize_filename(service))

            os.makedirs(platform_folder, exist_ok=True)

            response = get_with_retry(url)
            response_data = json.loads(response.text)

            downloaded_post_list = read_downloaded_posts_list(platform_folder)  # Read existing downloaded posts from JSON

            for post_num, post in enumerate(response_data, start=1):
                post_id = post.get('id')
                post_folder_name = get_post_folder_name(post)
                post_folder_path = os.path.join(platform_folder, sanitize_filename(post_folder_name))
                os.makedirs(post_folder_path, exist_ok=True)

                base_url = "/".join(url.split("/")[:3])

                # Initialize a flag to track if all downloads for this post are successful
                all_downloads_successful = True

                if post_id in all_downloaded_posts:
                    print(f"Skipping download: Post {post_id} already downloaded")
                    # Clear the console and show the artist name
                    clear_console(artist_name)
                    continue

                if post_id in downloaded_post_list:
                    print(f"Skipping download: Post {post_id} already downloaded")
                    # Clear the console and show the artist name
                    clear_console(artist_name)
                    continue

                for attachment in post.get('attachments', []):
                    attachment_url = base_url + attachment.get('path', '')
                    attachment_name = sanitize_attachment_name(attachment.get('name', ''))
                    if attachment_url and attachment_name:
                        response = download_file(attachment_url, post_folder_path, attachment_name, url, artist_name)
                        # Pass artist_name to download_file
                        if response == False:  # Check if download was unsuccessful
                            all_downloads_successful = False  # Set the flag to false

                file_info = post.get('file')
                if file_info and 'name' in file_info and 'path' in file_info:
                    file_url = base_url + file_info['path']
                    file_name = sanitize_attachment_name(file_info['name'])
                    if file_url and file_name:
                        response = download_file(file_url, post_folder_path, file_name, url)
                        if response == False:  # Check if download was unsuccessful
                            all_downloads_successful = False  # Set the flag to false

                content = post.get('content', '')
                post_url = f"{base_url}/{service.lower()}/user/{artist_id.lower()}/post/{post['id']}"
                save_content_to_txt(post_folder_path, content, post.get('embed', {}), post_url)

                username = url.split('/')[-1].split('?')[0]
                if username not in processed_users:
                    if artist_name != current_artist:
                        current_artist_url = url
                    else:
                        current_artist = artist_name
                    processed_users.add(username)

                # After all downloads for this post are complete, add the post ID to downloaded posts and save to JSON.
                if all_downloads_successful:  # Only add if all downloads are successful
                    downloaded_post_list.add(post_id)
                    write_downloaded_post(platform_folder, downloaded_post_list)
                    all_downloaded_posts.add(post_id)  # Add post ID to the overall set


            if previous_url is not None:
                if artist_id != previous_artist_id or i == len(url_list) - 1:
                    print("Saving artist to JSON")
                    # Clear the console and show the artist name
                    clear_console(artist_name)
                    save_artist_json(previous_url)
            else:
                save_artist_json(url)

            previous_url = url
            previous_artist_id = artist_id

    except requests.exceptions.RequestException:
        return False



def save_content_to_txt(folder_name, content, embed, post_url):
    folder_path = os.path.join(folder_name, "content.txt")
    comment_section = ""

    try:
        # Fetch the HTML content from the post_url
        response = requests.get(post_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract comments
        comments = soup.find_all('article', class_='comment')
        comment_list = []

        for comment in comments:
            user = comment.find('a', class_='comment__name').text
            message = comment.find('p', class_='comment__message').text
            timestamp = comment.find('time', class_='timestamp').text

            formatted_comment = f"{user} - {message} - {timestamp}"
            comment_list.append(formatted_comment)

        # Join comments with line breaks
        comment_section = '\n'.join(comment_list)

    except Exception as e:
        print(f"Error fetching comments from {post_url}: {e}")

    with open(folder_path, 'w', encoding='utf-8') as f:
        f.write("[POST URL]\n")
        f.write(f"{post_url}\n\n")
        f.write("[CONTENT]\n")
        f.write(html2text.html2text(content))
        f.write("\n")

        if embed:
            f.write("[EMBED]\n")
            for key, value in embed.items():
                f.write(f"{key.capitalize()}: {value}\n")
            f.write("\n")

        if comment_section:
            f.write("[COMMENTS]\n")
            f.write(comment_section)
            f.write("\n")


def main(option):
    options = [option] if option != "both" else ["kemono", "coomer"]
    url_list = []

    for option in options:
        api_pages, json_data = get_favorites.main(option)
        url_list.extend(api_pages)
        artist_id_to_name = create_artist_id_to_name_mapping(json_data)
        run_with_base_url(url_list, artist_id_to_name, json_data)


def delete_json_file(filename):
    # Check if file exists
    if os.path.exists(filename):
        try:
            os.remove(filename)
            print(f"{filename} removed successfully")
        except Exception:
            print(f"Unable to delete {filename}")
            print(Exception)
    else:
        print(f"No file found with the name {filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download data from websites.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-k',
                       '--kemono',
                       action='store_true',
                       help="Download data from kemono")
    group.add_argument('-c',
                       '--coomer',
                       action='store_true',
                       help="Download data from coomer")
    group.add_argument('-b',
                       '--both',
                       action='store_true',
                       help="Download data from both sites")
    group.add_argument('-u',
                        '--user',
                        type=str,
                        metavar='USERNAME/URL',
                        help="Only download posts from specific users, separated by commas")
    group.add_argument('-l',
                        '--list',
                        action='store_true',
                        help="Read usernames from user_list.txt")
    
    parser.add_argument('-r',
                        '--reset',
                        action='store_true',
                        help="Reset JSON file for selected flag")

    args = parser.parse_args()

    # Process the --user flag value to get a list of usernames
    if args.user:
        users = [user.strip() for user in args.user.split(",")]

    if args.list:
        read_user_txt_list()
    elif args.kemono:
        if args.reset:
            delete_json_file('Config/kemono_favorites.json')
        main("kemono")
    elif args.coomer:
        if args.reset:
            delete_json_file('Config/coomer_favorites.json')
        main("coomer")
    elif args.user:
        for user in users:  # Loop over the list of usernames
            url, username, json_data = user_search(user)
            artist_id_to_name = create_artist_id_to_name_mapping(json_data)
            run_with_base_url(url, artist_id_to_name, json_data)
    elif args.both:
        if args.reset:
            delete_json_file('Config/kemono_favorites.json')
            delete_json_file('Config/coomer_favorites.json')
        main("both")