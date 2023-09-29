import os
import sys
import json
import requests
import argparse
import html2text
import get_favorites
from tqdm import tqdm
from pathvalidate import sanitize_filename
from json_handling import lookup_and_save_user as save_artist_json
from user_search import main as user_search_main


# Map Kemono artist IDs to their names
def create_artist_id_to_name_mapping(json_file_path):
    try:
        with open(json_file_path, "r") as file:
            data = json.load(file)
        return {item["id"]: item["name"].capitalize() for item in data}
    except FileNotFoundError:
        print(f"No such file: {json_file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Could not parse JSON file: {json_file_path}")
        return {}


def get_with_retry_and_fallback(url, retries=3,
                                fallback_tld=".su",
                                stream=False):
    for i in range(retries):
        try:
            response = requests.get(url, stream=stream)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException:
            print(f"Failed to get {url}, attempt {i + 1}")
            if i == retries - 1:
                fallback_url = url.replace(".party", fallback_tld)
                print(f"Retrying with fallback URL: {fallback_url}")
                for j in range(retries):
                    try:
                        fallback_response = requests.get(fallback_url,
                                                         stream=stream)
                        fallback_response.raise_for_status()
                        return fallback_response
                    except requests.exceptions.RequestException:
                        print(f"Failed to get {fallback_url}, attempt {j + 1}")
                        if j == retries - 1:
                            print(f"Failed to download {fallback_url}",
                                  'logging to errors.txt')
                            with open("errors.txt", 'a') as error_file:
                                error_file.write(f"{fallback_url}\\n")


def download_file(url, folder_name, file_name, artist_url):
    # sourcery skip: extract-method
    folder_path = os.path.join(folder_name, file_name)
    if os.path.exists(folder_path):
        print(f"Skipping download: {file_name} already exists")
        return

    response = get_with_retry_and_fallback(url, stream=True)
    if response and response.status_code == 200:
        total_size_in_bytes = int(response.headers.get('content-length', 0))
        progress_bar = tqdm(total=total_size_in_bytes,
                            unit='iB',
                            unit_scale=True,
                            leave=False)

        with open(folder_path, 'wb') as f:
            for data in response.iter_content(1024):
                progress_bar.update(len(data))
                f.write(data)

        progress_bar.close()

        if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
            print("ERROR, something went wrong")

        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console
        sys.stdout.write("\033[F")  # Move the cursor to the previous line
        sys.stdout.write("\033[K")  # Clear the line
        print(f"Downloading files from {artist_url}:")
        print(f"Downloading: {file_name}")


def run_with_base_url(url_list, artist_id_to_name, json_file):
    # debug -- print("------------------------------URL LIST-------------------------------\n", url_list)
    # debug -- print("------------------------------JSON FILE-------------------------------\n", json_file)
    processed_users = set()  # Initialize an empty set to store processed users
    current_artist = None  # Initialize a variable to keep track of the current artist
    current_artist_url = None  # Initialize a variable to keep track of the current artist's URL

    try:
        for url in tqdm(url_list, desc="Downloading pages..."): # Wrong number of pages from artist being shown
            # Extract the domain, platform, and artist name from the URL
            url_parts = url.split("/")
            if len(url_parts) < 7:
                # Commented until resolved -- print(f"Unexpected URL structure: {url}")
                continue
            domain = url_parts[2].split(".")[0].capitalize()
            service = url_parts[4].capitalize()
            artist_id = url_parts[6].split("?")[0] # Split the artist's name by the question mark
            artist_name = artist_id_to_name.get(artist_id, artist_id).capitalize()

            # Construct the folder structure
            artists_folder = "Creators"
            domain_folder = os.path.join(artists_folder, domain)
            artist_folder = os.path.join(domain_folder, (sanitize_filename(artist_name)))
            platform_folder = os.path.join(artist_folder, sanitize_filename(service))

            os.makedirs(platform_folder, exist_ok=True)

            # Download the page and parse it as JSON
            response = get_with_retry_and_fallback(url)
            data = json.loads(response.text)

            # total_posts = sum(len(page_data) for page_data in data)

            for post_num, post in enumerate(data, start=1):
                post_folder_name = sanitize_filename(post.get('title') + "_" + sanitize_filename(post.get('published'))) if post.get('title') and post.get('published') else sanitize_filename(post.get('published', ''))

                post_folder_path = os.path.join(platform_folder, post_folder_name)
                os.makedirs(post_folder_path, exist_ok=True)

                base_url = "/".join(url.split("/")[:3])  # Extract the base URL

                for attachment in post.get('attachments', []):
                    attachment_url = base_url + attachment.get('path', '')
                    attachment_name = attachment.get('name', '')
                    if attachment_url and attachment_name:
                        download_file(attachment_url, post_folder_path, attachment_name, url)

                file_info = post.get('file')
                if file_info and 'name' in file_info and 'path' in file_info:
                    file_url = base_url + file_info['path']
                    file_name = file_info['name']

                    if file_url and file_name:
                        download_file(file_url, post_folder_path, file_name, url)

                content = post.get('content', '')
                save_content_to_txt(post_folder_path, content)

                # Extract the username from the URL
                username = url.split('/')[-1].split('?')[0]

                # Check if the username is not in the set of processed users
                if username not in processed_users:
                    # Check if the current artist is different from the previous one
                    if artist_name != current_artist:
                        print(f"Processing user: {username}")
                        current_artist_url = url  # Update the current artist's URL
                    else:
                        print(f"User {username} already processed. Skipping.")

                    # Update the current artist
                    current_artist = artist_name

                    # Add the username to the set of processed users
                    processed_users.add(username)
            # Update the JSON file for every page downloaded (Temporary change)
            if current_artist_url:
                print("Saving artist to JSON")
                print(current_artist_url, json_file)
                save_artist_json(current_artist_url, json_file)

    except requests.exceptions.RequestException:
        return False

    return True


def save_content_to_txt(folder_name, content):
    folder_path = os.path.join(folder_name, "content.txt")
    with open(folder_path, 'w', encoding='utf-8') as f:
        f.write(html2text.html2text(content))


def main(option):
    options = [option] if option != "both" else ["kemono", "coomer"]
    url_list = []

    for option in options:
        api_pages, json_file = get_favorites.main(option)
        # debug -- print(json_file)
        url_list.extend(api_pages)
    artist_id_to_name = create_artist_id_to_name_mapping("Config/kemono_favorites.json")
    run_with_base_url(url_list, artist_id_to_name, json_file)


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
                        metavar='USERNAME',
                        help="Only download posts from a specific user")
    parser.add_argument('-r',
                        '--reset',
                        action='store_true',
                        help="Reset JSON file for selected flag")

    args = parser.parse_args()

    if args.kemono:
        if args.reset:
            delete_json_file('Config/kemono_favorites.json')
        main("kemono")
    elif args.coomer:
        if args.reset:
            delete_json_file('Config/coomer_favorites.json')
        main("coomer")

    elif args.user:
        user = args.user if args.user else str(input("Please type the name of the creator: "))
        url, username, json_file_path,  = user_search_main(user)
        # DEBUG print("-------------------URL----------------------\n",url)
        # DEBUG print("-------------------Username----------------------\n",username)
        # DEBUG print("-------------------json_file_path----------------------\n",json_file_path)
        artist_id_to_name = create_artist_id_to_name_mapping("Config/kemono_favorites.json")
        run_with_base_url(url, artist_id_to_name, json_file_path)
    elif args.both:
        if args.reset:
            delete_json_file('Config/kemono_favorites.json')
            delete_json_file('Config/coomer_favorites.json')
        main("both")
