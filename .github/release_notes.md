### Release Notes for version 1.4.1

**Changes**

`download.py`
    - Handling of connection loss during downloads by using retries and timeouts
    - Prettified the console output for downloads
    - Fixed error where posts could be added to the downloaded list even if there were errors in the download

`get_favorites.py`
    - Fixed update discovery of discord users

**Future changes**

I am actively working (In the little free time I have) on polishing this script: merging as much of the functions as possible, improving speeds, code readability... and overall trying to make the experience better for everyone, users and coders alike. 

This will however take a while, and I can't assure my code will be 100% clean, but I'll try my best!

- Merging of discord_download.py into download.py
- Moving JSON functions from download.py to json_handling or viceversa (Still on the thinking lol)
- Update check for the program on start (Since this project gets updated quite a lot and I usually make stupid mistakes that break everything lol)
- Cron functionality, basically leave your PC on and let the program keep your stash updated at aaaaall times
- Creation of a settings menu, where you'll be able to change some parameters like the path of your stash, the number of posts to download from each artist, disk size limitations to not fill up every drive you own lol
- Menu so you can use the program with or without the need to use flags (Flags make it easier imo, but some people don't like them so I don't mind giving them a lil treat)

This is all I can say for now! Not that it's top secret or anything, but I don't wanna spoil any features that won't be around until a few months down the road, it'd be bad to keep you guys hanging!

Oh, and it's not Halloween yet but keep it spooky 🎃