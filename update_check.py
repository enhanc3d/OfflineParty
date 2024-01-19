import requests

__version__ = "v1.4.5"

updates_available = False  # Variable to store whether updates are available
first_run = True  # Variable to identify the first run


def check_for_updates():
    global updates_available  # Make updates_available a global variable
    try:
        url = "https://api.github.com/repos/2000GHz/OfflineParty/releases/latest"
        response = requests.get(url)
        latest_version = response.json()['tag_name']

        if latest_version != __version__:
            return True
    except Exception as e:
        print(f"Could not check for updates: {e}")