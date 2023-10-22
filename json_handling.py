import re
import json
import requests


# Look up the user in the provided data and save to the appropriate JSON file
def lookup_and_save_user(url):
    kemono_data = requests.get("https://kemono.su/api/v1/creators.txt").json()
    coomer_data = requests.get("https://coomer.su/api/v1/creators.txt").json() 
    # Regular expression to extract domain, service, and user ID/name from URL
    pattern = r'https://(?P<domain>\w+\.(?:party|su))/api/v1/(?P<service>[\w/]+)/(?P<user_id>[\w\d]+)(\?o=\d+)?'
    if match := re.match(pattern, url):

        # Extract individual groups
        domain = match.group('domain')
        service = match.group('service')
        user_id = match.group('user_id')

        if domain in ["coomer.party", "coomer.su"]:
            data = coomer_data
        elif domain in ["kemono.party", "kemono.su"]:
            data = kemono_data
        else:
            print(f"No matching domain found for: {domain}")
            return

        user_data = next((item for item in data if item.get('id') == user_id), None)

        if user_data:
            # Save to the appropriate JSON file
            if domain in ["coomer.party", "coomer.su"]:
                save_to_coomer_favorites(user_data)
            elif domain in ["kemono.party", "kemono.su"]:
                save_to_kemono_favorites(user_data)
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
        ):  # You matter!
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
        ):  # :)
            # Update the existing user data
            index = existing_data.index(existing_user)
            existing_data[index] = data
        else:
            # Add new user data
            existing_data.append(data)

        # Write the updated data back to the file

        # Go to the beginning of the file
        file.seek(0)
        json.dump(existing_data, file, indent=4)
        file.truncate()  # Remove any remaining old content after this point


# Example usage for debugging:
# url = "https://coomer.party/api/onlyfans/user/astolfitoliz"
# data = [{'faved_seq': 'UNKNOWN', 'id': 'astolfitoliz', 'indexed': 'UNKNOWN', 'last_imported': 'UNKNOWN', 'name': 'astolfitoliz', 'service': 'onlyfans', 'updated': 'UNKNOWN'}]  # Example data
# lookup_and_save_user(url, data)
