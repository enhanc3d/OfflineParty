
### Release Notes for version 1.1.0

**New Functionalities:**

1. **Download from specific users (`download.py`):**
   - Introduces a new flag -u which automatically tries to find users from your favorites
   - Alternatively, if you haven't set up your favorites, you can download with their page URL e.g: https://coomer.party/onlyfans/user/otakugirl90)
    #### Example use:
     - download.py -u otakugirl90

2. **Duplicate Finder (`duplicate_finder.py`):**
   - Added to handle the likely possibility that the searched user is favorited under multiple services

3. **User Search (`user_search.py`):**
   - Provides functionality to search for and extract user information from URLs or our favorites data.
   - Utilizes regular expressions to extract domain, service, and user ID details from URLs.

**Changes**

1. **Favorites Handler (`get_favorites.py`):**
   - Includes a safe printing function to handle UTF-8 encoded texts. (Debug purposes)
   - New function to handle the updates for non-favorited users that we've previously downloaded from

2. **JSON Handling (`json_handling.py`):**
   - Added compatibility with the .su domains
   - Extracts domain, service, and user ID/name from URLs and saves user data to appropriate JSON files.


