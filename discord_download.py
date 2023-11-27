import os
import requests
from tqdm import tqdm
from pathvalidate import sanitize_filename
from json_handling import save_to_kemono_favorites



def scrape_discord_server(server_id):

    BASE_URL = "https://kemono.su"  # Updated base URL

    from download import download_file, save_content_to_txt, load_settings
    settings = load_settings()
    stash_path = settings['stash_path']
    creators_list = requests.get("https://kemono.su/api/v1/creators.txt").json()

    for creator in creators_list:
        if creator['id'] == server_id:
            artist_name = sanitize_filename(creator['name'])

    # If artist name is not found, default to server_id
    artist_name_or_id = artist_name if artist_name else server_id

    # Use stash_path from YAML file as the base directory
    base_path = os.path.join(stash_path, "Creators", "Kemono", artist_name_or_id)

    download_preference = settings['download_preference']

    def fetch_discord_channels(server_id):
        """Fetch the list of channels for a given server."""
        url = f"{BASE_URL}/api/v1/discord/channel/lookup/{server_id}"
        response = requests.get(url)

        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code} for URL: {url}")
            print(response.text)
            return []

        try:
            return response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"Error decoding JSON from URL: {url}")
            print(response.text)
            return []

    def fetch_discord_posts(channel_id, skip_value):
        """Fetch posts for a given channel."""
        response = requests.get(f"{BASE_URL}/api/v1/discord/channel/{channel_id}?skip={skip_value}")
        if response.status_code == 200:
            return response.json()
        return []
    
    def get_post_folder_name(post):
        """Generate a folder name for a given post."""
        if date := post.get('published') or post.get('added'):
            return sanitize_filename(date)
        else:
            return sanitize_filename(post.get('id', 'Unknown'))
        
    def sanitize_attachment_name(name):
        # Remove any URL components
        name = name.replace("https://", "").replace("http://", "")
        # Further sanitize the name to remove invalid characters
        return sanitize_filename(name)

    channels = fetch_discord_channels(server_id)
    for channel in channels:
        print(f"Fetching posts from channel: {channel['name']}...\n")
        channel_path = os.path.join(base_path, channel['name'])

        skip_value = 0
        last_post_id = None
        while True:
            posts = fetch_discord_posts(channel['id'], skip_value)
            if not posts:
                break

            current_last_post_id = posts[-1]['id']

            if last_post_id == current_last_post_id:
                break  # Break the loop if the last post ID starts repeating

            last_post_id = current_last_post_id  # Update the last_post_id for the next iteration
            skip_value += 10  # Increment skip value for the next batch

            for post in posts:
                post_folder_name = get_post_folder_name(post)
                post_folder_path = os.path.join(channel_path, post_folder_name)

                # If preference is to save all in the channel folder, adjust paths
                if download_preference == '2':
                    post_folder_path = channel_path
                    post_date_prefix = f"{post_folder_name}_"
                else:
                    post_date_prefix = ""

                if not os.path.exists(post_folder_path):
                    os.makedirs(post_folder_path)

                for attachment in post.get('attachments', []):
                    attachment_url = BASE_URL + attachment.get('path', '')
                    attachment_name = sanitize_attachment_name(post_date_prefix + attachment.get('name', ''))
                    if attachment_url and attachment_name:
                        download_file(attachment_url, post_folder_path, attachment_name, BASE_URL, artist_name_or_id, channel['name'])

                save_content_to_txt(post_folder_path, post.get('content', ''), post.get('embed', {}), post)

        print(f"Finished fetching posts from channel: {channel['name']}\n")

    print(f"\n{'='*40}")
    print("Download complete!")
    print(f"{'='*40}\n")

    # Call save_to_kemono_favorites to save the data of the Discord server
    artist_data = next((item for item in creators_list if item['id'] == server_id), None)
    if artist_data:
        save_to_kemono_favorites(artist_data)
    else:
        print(f"Failed to find data for artist with server ID: {server_id}")