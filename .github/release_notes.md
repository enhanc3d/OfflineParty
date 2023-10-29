### Release Notes for version 1.4.2

**Changes**

`download`
* Added menu, flags are still available, but this can make things easier
* Added settings menu, not accesible with flags, with some interesting features in it:
    - Ability to change the directory of the Creators folder (Finally!)
    - Ability to add a limit of posts to download from each user
    - Ability to stablish a disk size limit, it will throw warnings when we're closing to our limit and has checks in place to avoid overpassing it
    - Ability to easily change your Discord download preference between all posts in the channel folder or separate folders for each post (This was possible before, but it would only be prompted during the first Discord download and to change it you'd have to manually edit the YAML file)
 
`discord_download`
* Reading path from the YAML to match with `download.py`

`user_search`
* Simplified yes or no retry prompt, pretty simple change but why not log it I guess

`Installation Scripts`
* Gave them executable permissions, so you *should* be able to run them just double clicking on them


**Future changes**

I am actively working (In the little free time I have) on polishing this script: merging as much of the functions as possible, improving speeds, code readability... and overall trying to make the experience better for everyone, users and coders alike. 

This will however take a while, and I can't assure my code will be 100% clean, but I'll try my best!

- Merging of discord_download.py into download.py
- Moving JSON functions from download.py to json_handling or viceversa (Still on the thinking lol)
- Update check for the program on start (Since this project gets updated quite a lot and I usually make stupid mistakes that break everything lol)
- Cron functionality, basically leave your PC on and let the program keep your stash updated at aaaaall times

This is all I can say for now! Not that it's top secret or anything, but I don't wanna spoil any features that won't be around until a few weeks down the road, it'd be bad to keep you guys hanging!

Oh, and it's not Halloween yet but keep it spooky 🎃
