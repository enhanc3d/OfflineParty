import os
import sys
import time
import json
import yaml
import requests
import argparse
import html2text
import webbrowser
import get_favorites
from tqdm import tqdm
from bs4 import BeautifulSoup
from datetime import datetime
from pathvalidate import sanitize_filename
from user_search import main as user_search
from json_handling import lookup_and_save_user as save_artist_json
from discord_download import scrape_discord_server as discord_download

__version__ = "v1.4.6"

updates_available = False  # Variable to store whether updates are available
first_run = True  # Variable to identify the first run

def display_ascii_art():
    ascii_art = '''
 .d88888b.  8888888888 8888888888 888      8888888 888b    888 8888888888      8888888b.     d8888 8888888b. 88888888888 Y88b   d88P 
d88P" "Y88b 888        888        888        888   8888b   888 888             888   Y88b   d88888 888   Y88b    888      Y88b d88P  
888     888 888        888        888        888   88888b  888 888             888    888  d88P888 888    888    888       Y88o88P   
888     888 8888888    8888888    888        888   888Y88b 888 8888888         888   d88P d88P 888 888   d88P    888        Y888P    
888     888 888        888        888        888   888 Y88b888 888             8888888P" d88P  888 8888888P"     888         888     
888     888 888        888        888        888   888  Y88888 888             888      d88P   888 888 T88b      888         888     
Y88b. .d88P 888        888        888        888   888   Y8888 888             888     d8888888888 888  T88b     888         888     
 "Y88888P"  888        888        88888888 8888888 888    Y888 8888888888      888    d88P     888 888   T88b    888         888                                                                                                                                  
    '''
    print(ascii_art.strip())
    time.sleep(1)


def check_for_updates():
    global updates_available  # Make updates_available a global variable
    try:
        url = "https://api.github.com/repos/2000GHz/OfflineParty/releases/latest"
        response = requests.get(url)
        latest_version = response.json()['tag_name']
        
        if latest_version != __version__:
            updates_available = True  # Set updates_available to True if updates are found
    except Exception as e:
        print(f"Could not check for updates: {e}")


def clear_console(artist_name_id_or_url, channel_name=None):
    if artist_name_id_or_url is None:
        artist_name_id_or_url = "Unknown Artist"  # Add a default value
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    separator = '=' * (len(artist_name_id_or_url) + 24)
    print(separator)
    
    if channel_name:
        print(f"Downloading posts from: {artist_name_id_or_url} in channel: {channel_name}")
    else:
        print(f"Downloading posts from: {artist_name_id_or_url}")
    
    print(separator)


def load_settings():
    dir_path = 'Config'
    file_name = 'user_settings.yaml'
    file_path = os.path.join(dir_path, file_name)

    # Default settings
    settings = {
        'stash_path': './',
        'post_limit': 0,  # 0 downloads all posts from the artist, it's the default value
        'disk_limit': 0,  # 0 disables the download limit. Expressed in MB
        'download_preference' : 0,
        'minimum_file_size' : 0,
        'maximum_file_size' : 0,
        'file_type_to_download' : ['Image', 'GIF', 'Video', 'Compressed', 'PSD', 'Other'],
        'show_startup_logo' : 0,
        'create_post_folder': True,
        # File type extensions
        'file_type_extensions' : {
            'Image': [
                '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.svg', 
                '.webp', '.raw', '.heif', '.indd', '.ai', '.eps'
            ],
            'GIF': [
                '.gif'
            ],
            'Video': [
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', 
                '.m4v', '.mpg', '.mpeg', '.3gp', '.vob', '.swf'
            ],
            'Compressed': [
                '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', '.tgz'
            ],
            'Audio': [
                '.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a', '.wma', 
                '.alac', '.amr'
            ],
            'PSD': [
                '.psd'
            ]
        }

    }

    # Check if the directory exists, if not create it
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Check if the YAML file exists, if not create it
    if not os.path.exists(file_path):
        save_settings(settings)

    # Read the YAML file
    with open(file_path, 'r', encoding='utf-8') as settings_file:
        try:
            loaded_settings = yaml.safe_load(settings_file)
            settings.update(loaded_settings)
        except yaml.YAMLError as e:
            print(f"Error reading settings file: {e}")

    return settings


def save_settings(settings):
    dir_path = 'Config'
    file_name = 'user_settings.yaml'
    file_path = os.path.join(dir_path, file_name)

    # Check if the directory exists, if not create it
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with open(file_path, 'w', encoding='utf-8') as settings_file:
        yaml.dump(settings, settings_file, default_flow_style=False)


def is_file_type_allowed(file_name, allowed_types, file_type_extensions):
    extension = os.path.splitext(file_name)[1].lower()

    if 'Other' in allowed_types:
        # If 'Other' is allowed, check that the extension is not in the listed types
        if not any(extension in ext_list for ext_list in file_type_extensions.values()):
            return True

    for file_type, extensions in file_type_extensions.items():
        if file_type in allowed_types and extension in extensions:
            return True

    return False


def get_folder_size(folder_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size // (1024 * 1024)  # convert bytes to MB


def check_disk_limit():
    settings = load_settings()
    disk_limit = settings['disk_limit']  # Fetch disk limit from settings
    creators_folder = os.path.join(settings['stash_path'], 'Creators')

    if disk_limit == 0 or 0.0:
        return True  # Skip disk limit check if set to 0

    if os.path.exists(creators_folder):
        current_size = get_folder_size(creators_folder)
        percentage_used = (current_size / disk_limit) * 100

        if percentage_used >= 70:
            print(f"\033[91mWarning: You are using {percentage_used:.2f}% of your disk limit.\033[0m")
            if percentage_used >= 100:
                print("You have reached or exceeded your disk limit. Exiting.")
                time.sleep(10)
                sys.exit(1)

        return percentage_used < 100

    return True  # Return True if Creators folder doesn't exist yet


def check_file_size_within_limit(file_size):
    settings = load_settings()
    disk_limit = settings['disk_limit']  # Fetch disk limit from settings in MB
    creators_folder = os.path.join(settings['stash_path'], 'Creators')

    if disk_limit == 0 or 0.0:
        return True  # Skip disk limit check if set to 0

    if os.path.exists(creators_folder):
        current_size = get_folder_size(creators_folder)  # in MB
        remaining_space = disk_limit - current_size  # in MB
        file_size_mb = file_size / (1024 * 1024)  # Convert file size to MB

        return file_size_mb <= remaining_space

    return True  # Return True if Creators folder doesn't exist yet


def settings_menu():
    settings = load_settings()  # Assume this function is defined elsewhere
    original_settings = settings.copy()  # Store the original settings for comparison
    changes_unsaved = False  # Flag to keep track of unsaved changes

    file_types_options = {
        '1': 'Image',
        '2': 'GIF',
        '3': 'Video',
        '4': 'Compressed',
        '5' : 'Audio',
        '6': 'PSD',
        '7': 'Other'
    }

    # Set the initial description for Discord download preference
    old_preference = settings['download_preference']
    description = ""
    if old_preference == 0:
        description = "No preference assigned yet."
    elif old_preference == 1:
        description = "Save files in separate folders for each message"
    elif old_preference == 2:
        description = "Save all files directly in the channel folder"
        
    original_description = description  # Store the original description for comparison

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear console before displaying menu

        # Add a flag for unsaved changes and color it red if changes are unsaved
        unsaved_changes_warning = " - \033[91mWarning! You have changes unsaved\033[0m" if changes_unsaved else ""
        menu_title = "Settings Menu" + unsaved_changes_warning

        # Calculate the length of the ANSI escape codes used for red color
        ansi_code_length = len("\033[91m") + len("\033[0m") if changes_unsaved else 0

        # Create the separator line
        separator = '=' * (len(menu_title) - ansi_code_length)

        print(separator)
        print(menu_title)
        print(separator, "\n")

        def format_setting(label, value, is_list = False):
            if label == 'download_preference':
                compare_value = description
                original_value = original_description
            else:
                compare_value = settings[label]
                original_value = original_settings[label]
            
            if is_list:  # Additional formatting for lists (e.g., file types)
                formatted_list = []
                for item in value:
                    color = "\033[94m" if item in settings[label] else "\033[0m"
                    formatted_list.append(f"{color}{item}\033[0m")
                return ', '.join(formatted_list)

            return "{}{}{}".format("\033[91m" if original_value != compare_value else "\033[94m", value, "\033[0m")
        
        def format_file_types_setting(current_file_types, original_file_types):
            if current_file_types == original_file_types:
                color_code = "\033[94m"  # Blue for unchanged
            else:
                color_code = "\033[91m"  # Red for changed

            if len(current_file_types) == len(file_types_options):
                return f"{color_code}All\033[0m"
            else:
                return ', '.join([f"{color_code}{ft}\033[0m" for ft in current_file_types])


        print(f"1. Change stash path (Current setting: {format_setting('stash_path', settings['stash_path'])})")
        print(f"2. Change post download limit (Current setting: {format_setting('post_limit', settings['post_limit'])})")
        print(f"3. Change disk size limit (Current setting: {format_setting('disk_limit', settings['disk_limit'])} MB)")
        print(f"4. Change Discord post saving preference (Current setting: {format_setting('download_preference', description)})")
        print(f"5. Change minimum file size to download (Current setting: {format_setting('minimum_file_size', settings['minimum_file_size'])} MB)")
        print(f"6. Change maximum file size to download (Current setting: {format_setting('maximum_file_size', settings['maximum_file_size'])} MB)")
        print(f"7. Change file types to download (Current setting: {format_file_types_setting(settings['file_type_to_download'], original_settings['file_type_to_download'])})")
        print(f"8. Create post folder (Current setting: {format_setting('create_post_folder', 'Enabled' if settings['create_post_folder'] else 'Disabled')})")
        print(f"9. Show OfflineParty logo (Current setting: {format_setting('show_startup_logo', settings['show_startup_logo'])})")
        print("10. Save and exit")
        print("11. Discard changes and go back")

        choice = input("\nEnter your choice: ")

        def has_changes():
            return any(original_settings[key] != settings[key] for key in original_settings) or original_description != description

        if choice in ['1', '2', '3', '4','5']:
            changes_unsaved = has_changes()  # Update the flag based on actual changes

        if choice == '1':
            new_path = input("\nEnter new stash path (Current: {}): ".format(settings['stash_path']))
            settings['stash_path'] = new_path

        elif choice == '2':
            try:
                print("\n0 = Download all posts from the user")
                new_limit = int(input("\nEnter new post download limit (Current: {}): ".format(settings['post_limit'])))
                settings['post_limit'] = new_limit
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)

        elif choice == '3':
            try:
                new_disk_limit = float(input("Enter new disk size limit, use '.'' for decimals (Current: {} MB): ".format(settings['disk_limit'])))
                settings['disk_limit'] = new_disk_limit
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)

        elif choice == '4':
            os.system('cls' if os.name == 'nt' else 'clear')
            print(separator)
            print("Settings Menu")
            print(separator, "\n")
            print("Choose one option from the list:\n")
            print("0. No preference assigned yet.")
            print("1. Save files in separate folders for each message.")
            print("2. Save all files directly in the channel folder.")
            try:
                new_discord_download_preference = int(input("\nEnter new Discord download preference: "))
                settings['download_preference'] = new_discord_download_preference
                # Update the description based on the new setting
                if new_discord_download_preference == 0:
                    description = "No preference assigned yet."
                elif new_discord_download_preference == 1:
                    description = "Save files in separate folders for each message"
                elif new_discord_download_preference == 2:
                    description = "Save all files directly in the channel folder"
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)
        
        elif choice == '5':
            try:
                new_min_size = float(input("\nEnter new minimum file size, 0 for no limit, use '.'' for decimals (MB): "))
                settings['minimum_file_size'] = new_min_size
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)

        elif choice == '6':
            try:
                new_max_size = float(input("\nEnter new maximum file size, 0 for no limit, use '.'' for decimals (MB): "))
                settings['maximum_file_size'] = new_max_size
            except ValueError:
                print("Invalid input. Please enter a number.")
                time.sleep(2)


        elif choice == '7':
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                print("Select file types to download:")
                for key, value in file_types_options.items():
                    color = "\033[94m" if value in settings['file_type_to_download'] else ""
                    print(f"{color}{key}. {value}\033[0m")
                print("8. Toggle all")
                print("9. Go back")

                file_type_choice = input("\nEnter your choices (comma-separated, e.g., 1,2,3): ")
                
                if file_type_choice == '8':  # Toggle all
                    if len(settings['file_type_to_download']) == len(file_types_options):
                        settings['file_type_to_download'].clear()  # Turn all off if all are on
                    else:
                        settings['file_type_to_download'] = list(file_types_options.values())  # Turn all on
                    continue


                if file_type_choice == '9':  # Exit submenu
                    if settings['file_type_to_download']:
                        break
                    else:
                        print("Please select at least one file type.")
                        time.sleep(2)
                        continue

                # Process the input to handle extra spaces and invalid entries
                selected_types = [t.strip() for t in file_type_choice.split(',') if t.strip() in file_types_options]
                settings['file_type_to_download'] = [file_types_options[t] for t in selected_types]


        elif choice == '8':
            settings['create_post_folder'] = not settings['create_post_folder']

        elif choice == '9':
            settings['show_startup_logo'] = not settings['show_startup_logo']

        elif choice == '10':
            save_settings(settings)
            changes_unsaved = False  # Reset flag to False after saving
            original_settings = settings.copy()  # Update original settings to new saved settings
            original_description = description  # Update original description
            print("\nChanges saved!")
            time.sleep(2)
            break

        elif choice == '11':
            break
        else:
            print("Invalid choice. Please try again.")
            time.sleep(2)
        
        changes_unsaved = has_changes()  # Update the flag based on actual changes after each loop iteration


# Map Kemono artist IDs to their names
def create_artist_id_to_name_mapping(data):
    if isinstance(data, dict):
        # If "id" and "name" are in the data:
        return {data.get("id", ""): data.get("name", "").capitalize()}
    elif isinstance(data, list):
        return {item.get("id", ""): item.get("name", "").capitalize() for item in data if isinstance(item, dict)}
    else:
        return {}  # Return an empty dictionary for unsupported data types


def read_user_txt_list():
    dir_path = './'  # Relative path to the current directory
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


# Function to read downloaded posts list from .json file
def read_downloaded_posts_list(platform_folder):
    file_path = os.path.join(platform_folder, "downloaded_posts.json")
    downloaded_posts = set()
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            downloaded_posts = set(json.load(file))
    
    return downloaded_posts

# Function to write downloaded post IDs to .json file
def write_to_downloaded_post_list(platform_folder, downloaded_posts):
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
                try:
                    with open("errors.txt", 'a') as error_file:
                        error_line = f"{current_date} - {url} -- {str(e)}\n"  # Include the current date and time
                        error_file.write(error_line)
                except Exception as write_error:
                    print(f"Could not write to errors.txt. Error: {write_error}")
                return None  # Explicitly return None if all retries fail


def download_file(url, folder_name, file_name, artist_url, artist_name):
    # Load settings
    settings = load_settings()

    # Check file type
    if not is_file_type_allowed(file_name, settings['file_type_to_download'], settings['file_type_extensions']):
        print(f"Skipping download: {file_name} is not a selected file type.")
        return False

    # Check if download would exceed disk limit
    if not check_disk_limit():
        print("Skipping download due to disk limit reached.")
        return False

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

            # Convert settings to bytes for comparison
            min_size_bytes = settings['minimum_file_size'] * 1024 * 1024
            max_size_bytes = settings['maximum_file_size'] * 1024 * 1024

            # Check if the file size is within the specified limits (0 means no limit)
            if (settings['minimum_file_size'] > 0 and total_size_in_bytes < min_size_bytes) or \
               (settings['maximum_file_size'] > 0 and total_size_in_bytes > max_size_bytes):
                print(f"Skipping download: {file_name} does not meet size criteria.")
                return False

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
    if url_list is None or len(url_list) == 0:
        print("No URLs to process. Exiting function.")
        return
    processed_users = set()
    current_artist = None
    current_artist_url = None
    previous_url = None
    previous_artist_id = None

    # Explicitly load settings within the function
    settings = load_settings()
    stash_path = settings.get('stash_path', '')  # If stash_path is not found, default to empty string
    post_limit = settings.get('post_limit', 0)  # Fetch the post limit from settings, default to 0 (download all)

    # Dictionary to keep track of the number of downloaded posts for each artist
    artist_post_count = {}

    try:
        all_downloaded_posts = set()

        for i, url in enumerate(tqdm(url_list, desc="Downloading pages...")):
            url_parts = url.split("/")
            if len(url_parts) < 7:
                print(f"Unexpected URL structure: {url}")
                continue

            domain = url_parts[2].split(".")[0].capitalize()
            service = url_parts[5].capitalize()
            artist_id = url_parts[7].split("?")[0]
            artist_name = data.get(artist_id, None)

            # Check if we've reached the post limit for this artist
            if post_limit > 0 and artist_post_count.get(artist_id, 0) >= post_limit:
                print(f"Skipping {artist_name} due to reaching post limit.")
                continue

            if artist_name:
                artist_name = artist_name.capitalize()
            else:
                print(f"Artist ID {artist_id} not found in data.")
                continue

            clear_console(artist_name)

            if service == 'Discord':
                discord_download(artist_id)
                continue

            domain_folder = os.path.join(stash_path, "Creators", domain)
            artist_folder = os.path.join(domain_folder, sanitize_filename(artist_name))
            platform_folder = os.path.join(artist_folder, sanitize_filename(service))

            os.makedirs(platform_folder, exist_ok=True)

            response = get_with_retry(url)
            response_data = json.loads(response.text)

            downloaded_post_list = read_downloaded_posts_list(platform_folder)

            for post_num, post in enumerate(response_data, start=1):
                post_id = post.get('id')
                post_folder_name = get_post_folder_name(post)
                if settings['create_post_folder']:
                    post_folder_path = os.path.join(platform_folder, sanitize_filename(post_folder_name))
                    os.makedirs(post_folder_path, exist_ok=True)
                else:
                    post_folder_path = platform_folder
                

                base_url = "/".join(url.split("/")[:3])

                all_downloads_successful = True

                if post_id in all_downloaded_posts or post_id in downloaded_post_list:
                    print(f"Skipping download: Post {post_id} already downloaded")
                    clear_console(artist_name)
                    continue

                # If we've reached the post limit for this artist, skip further posts
                if post_limit > 0 and artist_post_count.get(artist_id, 0) >= post_limit:
                    print(f"Reached post limit for {artist_name}. Skipping further posts.")
                    break

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
                        response = download_file(file_url, post_folder_path, file_name, url, artist_name)
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
                if all_downloads_successful:
                    downloaded_post_list.add(post_id)
                    write_to_downloaded_post_list(platform_folder, downloaded_post_list)
                    all_downloaded_posts.add(post_id)

                    # Increment the post count for this artist
                    artist_post_count[artist_id] = artist_post_count.get(artist_id, 0) + 1

            if previous_url is not None:
                if artist_id != previous_artist_id or i == len(url_list) - 1:
                    print("Saving artist to JSON")
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
    get_favorites.create_config("Config")
    os.system('cls' if os.name == 'nt' else 'clear')
    settings = load_settings()
    if settings['show_startup_logo']: display_ascii_art()
    check_for_updates()
    parser = argparse.ArgumentParser(description="Download data from websites.")
    group = parser.add_mutually_exclusive_group()  # Removed required=True
    group.add_argument('-k', '--kemono', action='store_true', help="Download data from Kemono")
    group.add_argument('-c', '--coomer', action='store_true', help="Download data from Coomer")
    group.add_argument('-b', '--both', action='store_true', help="Download data from both sites")
    group.add_argument('-u', '--user', type=str, metavar='USERNAME/URL', help="Only download posts from specific users, separated by commas")
    group.add_argument('-l', '--list', action='store_true', help="Read usernames from user_list.txt")

    parser.add_argument('-r', '--reset', action='store_true', help="Reset JSON file for selected flag")

    args = parser.parse_args()


    if not any(vars(args).values()):  # Check if any arguments were provided
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            menu_title = "Main Menu"
            update_warning = " - Updates Available!" if updates_available else ""
            full_title = menu_title + update_warning

            # Calculate the length of the ANSI escape codes used for green color
            ansi_code_length = 0
            if updates_available:
                full_title = f"Main Menu - \033[92mUpdates Available!\033[0m"
                ansi_code_length = len("\033[92m") + len("\033[0m")
            
            # Create the separator line
            separator = '=' * (len(full_title) - ansi_code_length)

            print(separator)
            print(full_title)
            print(separator, "\n")
            print("1. Download data from Kemono")
            print("2. Download data from Coomer")
            print("3. Download data from both sites")
            print("4. Search by user(s) or URL(s)")
            print("5. Read usernames from user_list.txt")
            print("6. Settings")
            if updates_available:
                print("7. Download Updates (Opens in default browser)")
            print("8. Exit" if updates_available else "7. Exit")

            choice = input("Enter your choice: ")

            if choice == '1':
                main("kemono")
            elif choice == '2':
                main("coomer")
            elif choice == '3':
                main("both")
            elif choice == '4':
                users = input("Enter usernames or URLs, separated by commas: ").split(',')
                users = [user.strip() for user in users]
                for user in users:
                    url, username, json_data = user_search(user)
                    artist_id_to_name = create_artist_id_to_name_mapping(json_data)
                    run_with_base_url(url, artist_id_to_name, json_data)
            elif choice == '5':
                read_user_txt_list()
            elif choice == '6':
                os.system('cls' if os.name == 'nt' else 'clear')
                settings_menu()
            elif choice == '7':
                if updates_available:
                    webbrowser.open("https://github.com/2000GHz/OfflineParty/releases/latest")
                else:
                    print("Exiting...")
                    break
            elif choice == '8' and updates_available:
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")
    else:
        # Existing code to handle flags
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
