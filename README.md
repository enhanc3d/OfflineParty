
# KemonoDL

## Instructions: 

1. [Download Repo](https://github.com/2000GHz/KemonoDL/archive/refs/heads/main.zip)
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
