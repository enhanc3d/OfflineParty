import json
import re
import get_favorites


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
            transformed_url = '/'.join(url_parts[:6])
            print(transformed_url)
            return transformed_url
        else:
            print("Invalid input URL format. Please enter a valid URL.")


def main(username):
    # Define the file paths
    coomer_file_path = 'Config/coomer_favorites.json'
    kemono_file_path = 'Config/kemono_favorites.json'

    # Initialize variables to store JSON data
    coomer_json_data = None
    print("Initializing data...")
    kemono_json_data = None

    # Load data from coomer_favorites.json
    try:
        with open(coomer_file_path, 'r') as coomer_file:
            coomer_json_data = json.load(coomer_file)
    except FileNotFoundError:
        print(f"File not found: {coomer_file_path}")
        print("Error loading coomer data.")

    # Load data from kemono_favorites.json
    try:
        with open(kemono_file_path, 'r') as kemono_file:
            kemono_json_data = json.load(kemono_file)
    except FileNotFoundError:
        print(f"File not found: {kemono_file_path}")
        print("Error loading kemono data.")

    # Initialize a list to store the combined data
    combined_data = []
    print("Combining data...")

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

        print(url)
        print("User found in local data.")
        return
    else:
                # If user not found, ask the user for next steps
        user_choice = input("User not found in local data. Would you like to:\n"
                            "1. Use data from get_favorites\n"
                            "2. Input the URL manually\n"
                            "Please enter your choice (1/2): ")

        if user_choice == "1":
            _, _, favorites_data = get_favorites.main("coomer")
            _, _, kemono_data = get_favorites.main("kemono")

            combined_data_2 = []
            # print("Combining data...")

            if favorites_data is not None:
                combined_data_2.extend(favorites_data)
            if kemono_data is not None:
                combined_data_2.extend(kemono_data)
            print(combined_data_2)

            # Search for the username in the fetched data
            found_user = None
            for user_data in combined_data:
                if user_data.get("id") == username:
                    found_user = user_data
                    print("User found in fetched data!")
                else:
                    print("User not found in fetched data either.")
                    input_and_transform_url()

            # If not found, prompt for manual URL input as before

        elif user_choice == "2":
            # Ask the user for input URL
            input_and_transform_url()


username = "alexapearl"

# First, try to search the user in the local files
main(username)