
# OfflineParty

## Prerequisites:

1. Install the required dependencies (Python and the modules it needs) using the install script matching your OS
2. Alternatively, if you already have python installed or the installation of modules failed, just run ```pip install -r requirements.txt```
3. Create a Kemono/Coomer account and/or log in with your default browser **(Not needed if you search by user)**

## Instructions / Manual of use: 

1. [Download the latest release](https://github.com/2000GHz/OfflineParty/releases) in your preferred format (.7z or .zip)

2. Sign in to kemono.party or coomer.party (Or kemono.su / coomer.su)

3. Run `download.py` with your terminal (cmd on windows, terminal in unix) using your desired flags.

You can run the script with or without flags, running it without any flags will give you a menu like this:

![image](https://github.com/2000GHz/OfflineParty/assets/59731892/26bdb2a1-f3c6-4625-bd91-bc77ca9e9bf5)

Let's check what they do:

1. **Download data from Kemono**: **REQUIRES SIGNING INTO THE KEMONO WEBSITE**, it fetches your list of favorite users and downloads posts from them.
2. **Download data from Coomer**: **REQUIRES SIGNING INTO THE COOMER WEBSITE**, basically the same as the first.
3. **Download data from both sites**: Take a guess!
4. **Search by user(s) or URL(s)**: Allows search for specific users by their username or URL, separated by commas and without spaces.
    - **WARNING, IF THE USERNAME HAS WHITESPACES IN THEIR NAME YOU HAVE TO USE QUOTES**
    - EXAMPLES:
    -     "afrobull,Your Favorite Artist"
    -     afrobull,vicineko,otakugirl90 (No whitespaces in their names, so no quotes needed)
5. **Read usernames from user_list.txt**: You can create a .txt with the name `user_list.txt` and store the usernames or URLs of the users you want to download, great alternative if you don't want to create an account.If you haven't created the file it will create itself. The file has to be structured with one user/url per line, like this:

![image](https://github.com/2000GHz/OfflineParty/assets/59731892/7421a0a7-56d2-4dda-96ed-9e9c8c6053a6)


6. **Settings**: This can be interesting to check:

![image](https://github.com/2000GHz/OfflineParty/assets/59731892/a36ce528-bdcf-42ff-acd7-44ee879aa90b)

As we can see, some values are highlighted in blue, these are our **current** settings, and having any unchanged value on them will highlight them red.

Let us go over each of the settings: 

1. **Change stash path**: This is the folder where you want all your stuff to be downloaded. A folder to store all the users will be created there. By default, this folder will be created in the same directory the script is being ran from, but you can copy and paste the path to your desired directory.
2. **Change post download limit**: Pretty self explanatory, by default is set to **0**, which **downloads all posts from the users**. NOTE: This limit applies for every artist, not in general, and is meant to be used to keep X amount of new posts downloaded.
3. **Change disk size limit**: Similarly to the previous point, **0 disables the disk size limit**, when we're closing the disk size limit, we'll get a warning. If any file exceeds the limit set, it will be skipped. When the limit is reached, the script won't download anything else, and you'll have to increase the limit or remove some files. **Expressed in MB.**
4. **Change Discord post saving preference**: Enables you to easily change your Discord download preference between all posts in the channel folder or separate folders for each post.
5. **Save and exit**: Save new settings to YAML and go back to the menu.
6. **Discard changes and go back**: Calls in an airstrike to your house (very dangerous)

You also have the option to use flags, which can help you skip the menus and make stuff faster

Available flags are:
- `-k` or `--kemono`: Download data from Kemono
- `-c` or `--coomer`: Download data from Coomer
- `-b` or `--both`: Download data from both Kemono and Coomer
- `-l` or `--list`: Download from your own list of users/urls (user_list.txt in the running folder, if it doesn't exist it will be created in the first run with this flag)
  - The txt file has to follow this structure, as we've discussed before:
    - ```
      UserOrUrl1
      UserOrUrl2
      UserOrUrl3
      ... 
  - `-r` or `--reset`: Reset (delete) the specific JSON files before downloading
  - -`u` or `--user`: Allows search for specific users by their username or URL, separated by commas and without spaces. (Incompatible with the other flags)
    - **WARNING, IF THE USERNAME HAS WHITESPACES IN THEIR NAME YOU HAVE TO USE THE COMMAND WITH QUOTES**
    - EXAMPLES:
    -     download.py -u "afrobull,Your Favorite Artist"
    -     download.py -u afrobull,vicineko,otakugirl90 (No whitespaces in their names, so no quotes needed)

6. Enjoy!

Note: You'll find a "content.txt" file inside every post's folder, inside it you'll find some relevant information such as the post URL, embedded content and comments where the artist could have included important information, make sure to check it out if you find an empty folder!

## Example of use

```bash
   python3 download.py -k -r
```
This will reset the `kemono_favorites.json` file, you can use this if for example you accidentally deleted a file, or new ones got added (For example if someone contributted with a higher tier )

You can use flags `-c`, `-b`, `-r` in a similar way.

** User search **
```bash
   python3 download.py -u otakugirl90
   python3 download.py -u https://kemono.party/discord/server/935649752475897936
```

Using this command will look through all creators, both kemono and coomer, to make sure we get all matching users.

Also, it's my first time working with shell scripts, so if you have any problems do let me know, thanks! 
