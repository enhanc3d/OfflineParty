import json
import re
import get_favorites
from bs4 import BeautifulSoup
import requests


def generate_json_dictionary_from_data(url):
    # Define regular expressions for extracting domain, service, and id
    domain_pattern = r"https://(.*?)/"
    service_pattern = r"/([^/]+)/user/"
    id_pattern = r"user/([^?]+)"

    # Extract domain, service, and id using regular expressions
    domain_match = re.search(domain_pattern, url)
    service_match = re.search(service_pattern, url)
    id_match = re.search(id_pattern, url)

    if domain_match and service_match and id_match:
        domain = domain_match.group(1)
        service = service_match.group(1)
        artist_id = id_match.group(1)

        # Initialize username as None
        username = None

        if "coomer" in domain:
            username = artist_id
        else:
            # Load the website and parse HTML to find the username
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                meta_tag = soup.find('meta', attrs={'name': 'artist_name', 'content': True})
                if meta_tag:
                    username = meta_tag['content']
        return {
            "faved_seq": "UNKNOWN",
            "id": username if username else "UNKNOWN",
            "indexed": "UNKNOWN",
            "last_imported": "UNKNOWN",
            "name": username if username else "UNKNOWN",
            "service": service,
            "updated": "UNKNOWN"
        }
    else:
        return None


# Define a flag to indicate whether the URL has been found
url_found = False

def input_and_transform_url():
    valid_url = False

    while not valid_url:
        # Ask the user for input URL
        input_url = input("Please, input the URL of the artist, for example:\nhttps://coomer.party/onlyfans/user/otakugirl90\nhttps://kemono.party/patreon/user/81088374\nURL: ")

        # Define a regular expression pattern to match allowed domains
        allowed_domains = r"(coomer\.party|coomer\.su|kemono\.party|kemono\.su)"

        # Define the expected input URL pattern
        input_expected_pattern = f"https://({allowed_domains})/([^/]+)/user/([^/]+)"

        # Use regular expressions to validate the input URL
        if re.match(input_expected_pattern, input_url):
            # Transform the input URL
            url_parts = input_url.split('/')
            transformed_url = f"https://{url_parts[2]}/api/{url_parts[3]}/user/{url_parts[5]}"
            # debug transformed url -- print(transformed_url)
            return transformed_url
        else:
            print("Invalid input URL format. Please enter a valid URL.")


def get_list_of_user_urls(domain, service, artist_id, url):
    global url_found  # Use the global flag
    url = [url]  # Convert to list for compatibility
    post_pages = get_favorites.get_all_page_urls(domain, service, artist_id, url)

    # Check if the URL was found and set the flag accordingly
    return post_pages


def main(username):
    global url_found  # Use the global flag

    # Define the file paths

    # Initialize variables to store JSON data
    coomer_json_file_path = "Config/coomer_favorites.json"
    kemono_json_file_path = "Config/kemono_favorites.json"

    # Load data from coomer_favorites.json
    try:
        with open(coomer_json_file_path, 'r') as coomer_file:
            coomer_json_file_path = json.load(coomer_file)
    except FileNotFoundError:
        print(f"File not found: {coomer_json_file_path}")
        print("Error loading coomer data.")

    # Load data from kemono_favorites.json
    try:
        with open(kemono_json_file_path, 'r') as kemono_file:
            kemono_json_file_path = json.load(kemono_file)
    except FileNotFoundError:
        print(f"File not found: {kemono_json_file_path}")
        print("Error loading kemono data.")

    # Initialize a list to store the combined data
    combined_data = []

    # Check if data from both files is not None and append them to combined_data
    if coomer_json_file_path is not None:
        combined_data.extend(coomer_json_file_path)
    if kemono_json_file_path is not None:
        combined_data.extend(kemono_json_file_path)

    # Search for the username in the combined data and print the corresponding dictionary
    found_user = None
    for user_data in combined_data:
        if user_data.get("name").lower() == username.lower():
            found_user = user_data
            break

    if found_user is not None:
        # Determine the domain based on the format of the `id` field
        id_value = found_user.get("id")
        if id_value.isdigit():
            domain = "kemono.party"
            json_file_path = kemono_json_file_path
        else:
            domain = "coomer.party"
            json_file_path = coomer_json_file_path

        # Extract relevant data from the found_user dictionary
        service = found_user.get("service")
        artist_id = found_user.get("id")

        # Construct the URL
        url = f"https://{domain}/api/{service}/user/{artist_id}"

        print("User found in local data!")
        # debug found url -- print(url)
        print("Obtaining all pages from the artist to proceed... this might take a while.")

        # Set the flag to indicate URL found and exit the function
        url_found = True

        return get_list_of_user_urls(domain, service, artist_id, url), username, json_file_path

    else:
        # If user not found, ask the user for next steps
        user_choice = input("User not found in local data. Would you like to:\n"
                            "1. Use data from your favorites?\n"
                            "2. Input the URL manually\n"
                            "Please enter your choice (1/2): ")

        if user_choice == "1":
            _, coomer_data = get_favorites.main("coomer")
            _, kemono_data = get_favorites.main("kemono")

            combined_data_2 = []

            if coomer_data is not None:
                combined_data_2.extend(coomer_data)
            if kemono_data is not None:
                combined_data_2.extend(kemono_data)

            found_user = None
            for user_data in combined_data_2:
                if user_data.get("name").lower() == username.lower():
                    found_user = user_data
                    print("User found in fetched data!")
                    id_value = found_user.get("id")
                    if id_value.isdigit():
                        domain = "kemono.party"
                    else:
                        domain = "coomer.party"
                    url = f"https://{domain}/api/{found_user.get('service')}/user/{found_user.get('id')}"
                    service = found_user.get('service')
                    artist_id = found_user.get('id')
                    # debug found url -- print(url)
                    # Set the flag to indicate URL found and exit the function
                    url_found = True
                    json_data = generate_json_dictionary_from_data(url)
                    return_data = get_list_of_user_urls(domain, service, artist_id, url), username, json_data
                    return return_data

            transformed_input_url = input_and_transform_url()

            def extract_info(url):
                # Define regular expressions for extracting domain, service, and id
                domain_pattern = r"https://(.*?)/"
                service_pattern = r"/([^/]+)/user/"
                id_pattern = r"user/([^?]+)"

                # Extract domain, service, and id using regular expressions
                domain_match = re.search(domain_pattern, url)
                service_match = re.search(service_pattern, url)
                id_match = re.search(id_pattern, url)

                if domain_match and service_match and id_match:
                    domain = domain_match.group(1)
                    service = service_match.group(1)
                    artist_id = id_match.group(1)

                    # Initialize username as None
                    username = None

                    if "coomer" in domain:
                        username = artist_id
                    else:
                        # Load the website and parse HTML to find the username
                        response = requests.get(url)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            meta_tag = soup.find('meta', attrs={'name': 'artist_name', 'content': True})
                            if meta_tag:
                                username = meta_tag['content']
                    return domain, service, artist_id, username

            domain, service, artist_id, username = extract_info(transformed_input_url)
            json_data = generate_json_dictionary_from_data(transformed_input_url)
            return get_list_of_user_urls(domain, service, artist_id, transformed_input_url), username, json_data

        elif user_choice == "2":
            transformed_input_url = input_and_transform_url()

            def extract_info(url):
                # Define regular expressions for extracting domain, service, and id
                domain_pattern = r"https://(.*?)/"
                service_pattern = r"/([^/]+)/user/"
                id_pattern = r"user/([^?]+)"

                # Extract domain, service, and id using regular expressions
                domain_match = re.search(domain_pattern, url)
                service_match = re.search(service_pattern, url)
                id_match = re.search(id_pattern, url)

                if domain_match and service_match and id_match:
                    domain = domain_match.group(1)
                    service = service_match.group(1)
                    artist_id = id_match.group(1)

                    # Initialize username as None
                    username = None

                    if "coomer" in domain:
                        json_file_path = coomer_json_file_path
                        json_file_path = coomer_json_file_path
                        username = artist_id
                    else:
                        json_file_path = kemono_json_file_path
                        # Load the website and parse HTML to find the username
                        response = requests.get(url)
                        if response.status_code == 200:
                            soup = BeautifulSoup(response.content, 'html.parser')
                            meta_tag = soup.find('meta', attrs={'name': 'artist_name', 'content': True})
                            if meta_tag:
                                username = meta_tag['content']
                    return domain, service, artist_id, username, json_file_path

            domain, service, artist_id, username, json_file_path = extract_info(transformed_input_url)
            return get_list_of_user_urls(domain, service, artist_id, transformed_input_url), username, json_file_path

# Example usage:
# main("alexapearl")
