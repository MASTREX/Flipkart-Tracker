# Flipkart-Tracker
Initially it tracks price of any product and also checks for its availability.

### Requirements
This python script is meant to run 'Termux' app.

- [Termux app](https://play.google.com/store/apps/details?id=com.termux)
- [Termux:API app](https://play.google.com/store/apps/details?id=com.termux.api) (for notification)
- Program needed on termux
  - python
  - [termux-api](https://wiki.termux.com/wiki/Termux:API)
- Python packages
  - requests
  - beautifulsoup

After installing Termux run following command to get all the required packages:
```bash
pkg install python
pkg install termux-api
termux-setup-storage
pip install requests beautifulsoup4
```

## To Run the script
Download the script and save it in your internal storage.

Change to directory of phone internal storage `cd storage/shared` and then to your file location `cd '<path to your file>'`. These commands can be combined together.

To run the file use `python main.py`

Example: As I have my 'main.py' in folder named 'Script' on my internal storage then i use
```
cd 'storage/shared/Script/'
python main.py
```

> Note!: Change main.py according to your need. 
>- Line140: time interval between fetching same product link again