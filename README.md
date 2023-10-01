
# OfflineParty

## Prerequisites:

1. Install the required dependencies (Python and the modules it needs) using the install script matching your OS

2. Create a Kemono/Coomer account and/or log in with your default browser **(Not needed if you search by user)**

## Instructions: 

1. [Download the latest release](https://github.com/2000GHz/OfflineParty/releases) in your preferred format (.7z or .zip)

2. Sign in to kemono.party or coomer.party (Or kemono.su / coomer.su)

3. Run `download.py` with your terminal (cmd on windows, terminal in unix) using your desired flags. Available flags are:
    - `-k` or `--kemono`: Download data from kemono
    - `-c` or `--coomer`: Download data from coomer
    - `-b` or `--both`: Download data from both kemono and coomer
    - `-r` or `--reset`: Reset (delete) the specific JSON files before downloading
    - -`u` or `--user`: Allows search for one specific user by their username (Incompatible with the other flags)

4. Enjoy!

## Example of use

```bash
   python3 download.py -k -r
```
This will reset the `kemono_favorites.json` file, you can use this if for example you accidentally deleted a file, or new ones got added (For example if someone contributted with a higher tier )

You can use flags `-c`, `-b`, `-r` in a similar way.

** User search **
```bash
   python3 download.py -u otakugirl90
```

Using this command will look through your favorites, both kemono and coomer, to make sure we get all matching users.
It will first search through the local JSON favorite files, but if a match is not found, the user is prompted to:

1.  Check for new favorites (Will find the updated favorite list online and search for the desired user)
2.  Input the URL manually (Will try to parse the data from the URL, for example: `https://coomer.party/onlyfans/user/otakugirl90` and generate a JSON entry in the according file with the obtainable values)

As of right now, only one user is available for download at a time, but in the future this will be expanded to allow for multiple manual user download at a time

Also, it's my first time working with shell scripts, so if you have any problems do let me know, thanks! 
