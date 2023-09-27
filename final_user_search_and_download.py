import argparse
import re
import json
import requests
from get_favorites import get_all_page_urls
from download import run_with_base_url, create_artist_id_to_name_mapping

def find_user_by_name(name, json_file):
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
            for user in data:
                if user.get('name') == name:
                    return user
    except FileNotFoundError:
        print(f"JSON file {json_file} not found.")
    return {}

def main():
    parser = argparse.ArgumentParser(description="Search for a user and download their content.")
    parser.add_argument("-u", "--user", required=True, help="Name or URL of the artist page.")
    args = parser.parse_args()

    # Define the regex pattern for URL matching
    pattern = r'https://(?P<domain>\w+\.(party|su))/api/(?P<service>\w+)/user/(?P<user_id>[\w\d]+)\?o=\d+'
    
    # If the user input matches the URL pattern, use it directly
    if match := re.match(pattern, args.user):
        domain, service, user_id = match.groups()
        url = f"https://{domain}/api/{service}/user/{user_id}?o=0"
        json_file = "Config/coomer_favorites.json" if "coomer" in domain else "Config/kemono_favorites.json"
    else:
        # If the user input is a name, search for it in the JSON files
        user_data = find_user_by_name(args.user, "Config/coomer_favorites.json") or find_user_by_name(args.user, "Config/kemono_favorites.json")
        
        if user_data:
            domain = "coomer.party" if "coomer" in user_data['service'] else "kemono.party"
            url = f"https://{domain}/api/{user_data['service']}/user/{user_data['id']}?o=0"
            json_file = "Config/coomer_favorites.json" if "coomer" in user_data['service'] else "Config/kemono_favorites.json"
        else:
            print(f"No user found with name: {args.user}")
            return

    # Use the get_all_page_urls function to retrieve all page URLs for the specified artist
    session = requests.Session()  # Create a new session for requests
    headers = {}  # Define any headers if required
    api_url_list = []
    
    get_all_page_urls(domain, user_data['service'], user_data['id'], session, headers, api_url_list)
    
    # Create a mapping of artist IDs to names using the chosen JSON file
    artist_id_to_name = create_artist_id_to_name_mapping(json_file)
    
    # Call the run_with_base_url function with the list of URLs and the chosen JSON file
    run_with_base_url(api_url_list, artist_id_to_name, json_file)

if __name__ == "__main__":
    main()
