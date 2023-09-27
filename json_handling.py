
import re
import json


def lookup_and_save_user(url, data):
    """Look up the user in the provided data and save to the appropriate JSON file."""
    # Regular expression to extract domain, service, and user ID/name from URL
    # Change .party hardcode to allow .su domain
    pattern = r'https://(?P<domain>\w+\.party)/api/(?P<service>\w+)/user/(?P<user_id>[\w\d]+)\?o=\d+'
    if match := re.match(pattern, url):
        domain, service, user_id = match.groups()
        # debug -- print(f"Extracted from URL -> Domain: {domain}, Service: {service}, User ID: {user_id}")

        if user_data := next(
            (item for item in data if item.get('id') == user_id), None
        ):
            print(f"Found user in provided data: {user_data}")

            # Save to the appropriate JSON file
            if domain == "coomer.party":
                save_to_coomer_favorites(user_data)
            elif domain == "kemono.party":
                save_to_kemono_favorites(user_data)
            else:
                print(f"No matching domain found for: {domain}")
        else:
            print(f"No user matched in the provided data for URL: {url}")
    else:
        print("No match found in the URL using regex.")


def save_to_coomer_favorites(data):
    """Save or update the provided user data in coomer_favorites.json."""
    with open("Config/coomer_favorites.json", "r+") as file:
        # Load the existing data
        existing_data = json.load(file)

        if existing_user := next(
            (item for item in existing_data if item.get('id') == data['id']),
            None,
        ):
            # Update the existing user data
            index = existing_data.index(existing_user)
            existing_data[index] = data
        else:
            # Add new user data
            existing_data.append(data)

        # Write the updated data back to the file
        file.seek(0)  # Go to the beginning of the file
        json.dump(existing_data, file, indent=4)
        file.truncate()  # Remove any remaining old content after this point


def save_to_kemono_favorites(data):
    """Save or update the provided user data in coomer_favorites.json."""
    with open("Config/kemono_favorites.json", "r+") as file:
        # Load the existing data
        existing_data = json.load(file)

        if existing_user := next(
            (item for item in existing_data if item.get('id') == data['id']),
            None,
        ):
            # Update the existing user data
            index = existing_data.index(existing_user)
            existing_data[index] = data
        else:
            # Add new user data
            existing_data.append(data)

        # Write the updated data back to the file
        file.seek(0)  # Go to the beginning of the file
        json.dump(existing_data, file, indent=4)
        file.truncate()  # Remove any remaining old content after this point
