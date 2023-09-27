
# OfflineParty

## Prerequisites:

1. Install the required dependencies (Python and the modules it needs) using the install script matching your OS
2. Create a Kemono/Coomer account and/or log in with your default browser

## Instructions: 

1. [Download Repo](https://github.com/2000GHz/OfflineParty/archive/refs/heads/main.zip)
2. Using the terminal, run 
```bash 
pip install -r requirements.txt
```
3. Sign in to kemono.party or coomer.party (Or kemono.su / coomer.su)

4. Run `download.py` with desired flags. Available flags are:
    - `-k` or `--kemono`: Download data from kemono
    - `-c` or `--coomer`: Download data from coomer
    - `-b` or `--both`: Download data from both kemono and coomer
    - `-r` or `--reset`: Reset (delete) the specific JSON files before downloading
```bash
   python3 download.py -k -r
```
This will download data from "kemono" and reset (delete) `kemono_favorites.json` file. You can use flags `-c`, `-b`, `-r` in a similar way.

5. Enjoy!

Also, it's my first time working with shell scripts, so if you have any problems do let me know, thanks! 
