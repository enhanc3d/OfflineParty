
# OfflineParty

## Prerequisites:

1. Install the required dependencies (Python and the modules it needs) using the install script matching your OS

2. Create a Kemono/Coomer account and/or log in with your default browser

## Instructions: 

1. [Download the latest release](https://github.com/2000GHz/OfflineParty/releases) in your preferred format (.7z or .zip)

2. Sign in to kemono.party or coomer.party (Or kemono.su / coomer.su)

3. Run `download.py` with your terminal (cmd on windows, terminal in unix) using your desired flags. Available flags are:
    - `-k` or `--kemono`: Download data from kemono
    - `-c` or `--coomer`: Download data from coomer
    - `-b` or `--both`: Download data from both kemono and coomer
    - `-r` or `--reset`: Reset (delete) the specific JSON files before downloading

4. Enjoy!

## Example of use

```bash
   python3 download.py -k -r
```
This will reset the `kemono_favorites.json` file, you can use this if for example you accidentally deleted a file, or new ones got added (For example if someone contributted with a higher tier )

You can use flags `-c`, `-b`, `-r` in a similar way.

Also, it's my first time working with shell scripts, so if you have any problems do let me know, thanks! 
