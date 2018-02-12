# emailScraper.py

This tool is designed to take user input for a starting URL and domain, and scrape that URL and any subdirectories that are linked for emails in that domain.

### Instructions

Pretty straightforward, just run this script using python3 and it will ask for input variables.

For the starting URL, don't specify a filename (index.html), but rather the URL directory it's in (http://test.local/). The script currently only supports http: or https:, not both. 

For the domain, if you want all email domains, just leave it blank. The script currently only supports single domains. 

### Future plans/wishlist

As with all github accounts, I plan on adding more features. If I don't get too distracted, these should be fairly easy to implement

-Support for http: and https: links (should be fairly easy to do)
-Support for multiple specified email domains (again, should be fairly easy to do)
-Command line support so this can be scripted (will take more time, but not impossible)

### Disclaimer

This has been provided for testing and academic purposes only. Do not use this tool against networks that you do not own or have express/strict written consent to test against. Do not use for illegal purposes.
