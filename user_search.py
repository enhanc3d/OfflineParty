import json
import subprocess
import re

def is_valid_input_url(url):
    # Define a regular expression pattern to match allowed domains
    allowed_domains = r"(coomer\.party|coomer\.su|kemono\.party|kemono\.su)"

    # Define the expected input URL pattern
    input_expected_pattern = f"https://({allowed_domains})/([^/]+)/user/([^/]+)"

    # Use regular expressions to validate the input URL
    return re.match(input_expected_pattern, url)

def transform_url(url):
    # Split the URL by '/'
    url_parts = url.split('/')

    # Reassemble the desired URL
    desired_url = '/'.join(url_parts[:6])  # Keep the first 6 parts

    return desired_url

def main(username):

    # Define the file paths
    coomer_file_path = 'Config/coomer_favorites.json'
    kemono_file_path = 'Config/kemono_favorites.json'

    # Initialize variables to store JSON data
    coomer_json_data = None
    kemono_json_data = None

    # Load data from coomer_favorites.json
    try:
        with open(coomer_file_path, 'r') as coomer_file:
            coomer_json_data = json.load(coomer_file)
    except FileNotFoundError:
        print(f"File not found: {coomer_file_path}")

    # Load data from kemono_favorites.json
    try:
        with open(kemono_file_path, 'r') as kemono_file:
            kemono_json_data = json.load(kemono_file)
    except FileNotFoundError:
        print(f"File not found: {kemono_file_path}")

    # Initialize a list to store the combined data
    combined_data = []

    # Check if data from both files is not None and append them to combined_data
    if coomer_json_data is not None:
        combined_data.extend(coomer_json_data)
    if kemono_json_data is not None:
        combined_data.extend(kemono_json_data)

    # Search for the username in the combined data and print the corresponding dictionary
    found_user = None
    for user_data in combined_data:
        if user_data.get("id") == username:
            found_user = user_data
            break

    if found_user is not None:
        # Determine the domain based on the format of the `id` field
        id_value = found_user.get("id")
        if id_value.isdigit():
            domain = "kemono.party"
        else:
            domain = "coomer.party"

        # Extract relevant data from the found_user dictionary
        service = found_user.get("service")
        artist_id = found_user.get("id")

        # Construct the URL
        url = f"https://{domain}/api/{service}/user/{artist_id}"

        # print(f"Constructed URL for username={username}:\n")
        print(url)
    else:
        print(f"Username '{username}' not found in the combined data.")

        # Ask the user for input URL
        input_url = input("Please, input the URL of the artist.\nFor example: https://coomer.party/onlyfans/user/otakugirl90 // https://kemono.party/patreon/user/81088374: ")

        # Validate the user-provided input URL
        if is_valid_input_url(input_url):
            # Transform the input URL
            transformed_url = transform_url(input_url)

            # print(f"Transformed URL for input URL={input_url}:\n")
            print(transformed_url)
        else:
            print("Invalid input URL format. Please enter a valid URL.")

if __name__ == "__main__":
    main("alexapearl")
