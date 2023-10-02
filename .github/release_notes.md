
### Release Notes for version 1.1.1

**Fixes**

1. **Fixed selection of multiple users when there are duplicates (`user_search.py`):**
   - The selection of multiple users in the duplicate_finder prompt was causing issues due to wrong returns

2. **Modularization to allow reuse of useful functions in the rest of the code (`get_favorites.py`):**
   - Separated the big fetch_favorite_artists function in 2:
      - Retrieval of the JSON favorites data from the server
      - Processing of said data
      - This helped speed up massively the search for users, as we were calculating all the pages for all the artists unneedingly


