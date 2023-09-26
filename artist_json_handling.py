import json
import re
import os

def lookup_and_save_user(url: str, input_filepath: str) -> None:
    """
    Load the JSON data, look up a user based on the provided URL, and save the result to the appropriate file if found.

    Args:
    - url (str): The URL to extract the username/userID from.
    - input_filepath (str): The path to the input JSON file.
    """
    
    # Inner function to find user from URL based on both domain and id
    def find_user(url: str, data: list) -> dict:
        # Extract the domain and userID from the URL using regex
        match = re.search(r'://([^/]+)/api/(\w+)/user/(\w+)', url.lower())
        if not match:
            return None

        domain, service, user_id = match.groups()
        
        # Check if it's a Kemono or Coomer URL based on the domain
        if "kemono.party" in domain:
            service_type = "Kemono"
        elif "coomer.party" in domain:
            service_type = "Coomer"
        else:
            return None

        # Search for the user in the data that matches both service and id
        for user in data:
            if user['id'].lower() == user_id and user['service'].lower() == service_type.lower():
                return user
        return None

    # Inner function to save to JSON file
    def save_to_file(data: dict, filename: str) -> None:
        # Determine the path to save the file
        file_path = os.path.join(os.getcwd(), filename)

        # Load existing data if the file exists
        existing_data = []
        try:
            with open(file_path, "r") as file:
                existing_data = json.load(file)
        except FileNotFoundError:
            pass

        # Check for duplicates
        if data not in existing_data:
            existing_data.append(data)

            # Save the updated data back to the file
            with open(file_path, "w") as file:
                json.dump(existing_data, file, indent=4)
    
    # Load the JSON data
    with open(input_filepath, "r") as file:
        data = json.load(file)

    # Look up the user
    result = find_user(url, data)

    # If a user is found, save the result to the appropriate file based on the domain
    if result:
        if "kemono.party" in url.lower():
            save_to_file(result, "Config/kemono_favorites.json")
        elif "coomer.party" in url.lower():
            save_to_file(result, "Config/coomer_favorites.json")

# To use the function:
# lookup_and_save_user("https://kemono.party/api/patreon/user/49965584", "Config/kemono_favorites.json")
# lookup_and_save_user("https://coomer.party/api/onlyfans/user/alexapearl?o=0", "Config/coomer_favorites.json")
