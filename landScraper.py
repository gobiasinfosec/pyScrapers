#!/usr/bin/env python3
"""
# landScraper.py -v 1.8
# currently designed for python 3.11.2
# Author- David Sullivan
#
# Credit to Michael Shilov from scraping.pro/simple-email-crawler-python for the base for this code
#
# As a reminder, web scraping for the purpose of SPAM or hacking is illegal. This tool has been provided for
# legitimate testers to validate the information provided on a website that they have explicit legal right to
# scrape.
#
#
# Revision  1.0     -   02/12/2018- Initial creation of script
# Revision  1.1     -   04/06/2018- Added in some more error handling
# Revision  1.2     -   04/18/2018- Added in ability to blacklist words in links (to avoid looping), and the ability to
#                                   process sub-domains
# Revision  1.3     -   08/07/2018- Added in functionality to write to output as it runs, in case the script breaks
# Revision  1.4     -   01/16/2019- Added a timeout for stale requests, suppression for error messages related to SSL
# Revision  1.5     -   02/13/2019- Renamed tool to landScraper, implemented argparse, broke out functions, implemented
#                                   automated cleanup if the program is terminated using keystrokes
# Revision  1.6     -   10/20/2021- Added a User-Agent header to get around 403 errors
# Revision  1.7     -   03/15/2022- Added 'touch' command to create output file if it doesn't exist to make it forward
#                                   compatible with newer versions of python, updated bad link words
# Revision  1.8     -   06/01/2026- Fixed parsing bug - TC
"""

import re
import sys
import requests.exceptions
import argparse
from collections import deque
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
import urllib3


def manual_url():
    return input(r'Put in the full URL of where you want to start crawling (ex:http://test.local/local): ')


def manual_email():
    return input(r'Put in the email domain you are looking for (ex: @test.local): ')


def manual_output():
    return input(r'Path and filename for results output (ex: /home/test/crawled_emails.txt): ')


def scrape(starting_url, domain_name, email_domain, outfile):
    # a queue of urls to be crawled
    global response
    new_urls = deque([starting_url])

    # a set of urls that we have already crawled
    processed_urls = set()

    # create an empty list for the emails variable
    emails = list()

    # don't include links with the following (to avoid loops)
    bad_link_words = ['##', '.pdf', '.mp3', '.mp4', '.mpg', '.wav', '.jpg', '.png', '.gif', '#', '../']

    # process to handle checking the bad_link_words list
    def avoid_loops(links, words):
        return any(word in links for word in words)

    # process urls one by one until we exhaust the queue
    while len(new_urls):

        # noinspection PyBroadException
        try:
            # move next url from the queue to the set of processed urls
            url = new_urls.popleft()
            processed_urls.add(url)

            # extract base url to resolve relative links
            parts = urlsplit(url)
            base_url = "{0.scheme}://{0.netloc}".format(parts)
            path = url[:url.rfind('/') + 1] if '/' in parts.path else url

            # get url's content
            print(f"Processing {url}")
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0(Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'}, verify=False, timeout=10)
            except (requests.exceptions.MissingSchema, requests.exceptions.ConnectionError):
                # ignore pages with errors
                continue
            except KeyboardInterrupt:
                cleanup_list(outfile, emails, email_domain)

            # extract all email addresses
            new_emails = set(re.findall(r"[a-z0-9.\-+_]+@[a-z0-9.\-+_]+\.[a-z]+"                                                                             , response.text, re.I))

            # write them to output file
            f = open(outfile, 'a+')
            for email in new_emails:
                f.write(email + '\n')
            f.close()

            # noinspection PyBroadException
            try:
                # create a beautiful soup for the html document
                soup = BeautifulSoup(response.text, "html.parser")

                # find and process all the anchors in the document
                for anchor in soup.find_all("a"):
                    # extract link url from the anchor
                    href = anchor.get("href", "")
                    link = href if isinstance(href, str) else (href[0] if href else "")
                    link = link.strip()

                    # skip link with mailto:, tel:, etc., or are empty
                    if not link or link.startswith('#'):
                        continue
                    if ":" in link.split('/', 1)[0] and not link.startswith(('http://', 'https://', '//')):
                        continue

                    # resolve relative links
                    if link.startswith('//'):
                        link = parts.scheme + ':' + link
                    elif link.startswith('/'):
                        link = base_url + link
                    elif not link.startswith(('http://', 'https://')):
                        link = path + link

                    # add the new url to the queue if it was not enqueued nor processed yet
                    if not (link in new_urls or link in processed_urls):
                        # only add the new url if not in the bad_link_words list
                        if not avoid_loops(link, bad_link_words):
                            # only add urls that are part of the domain_name
                            if domain_name in link:
                                new_urls.append(link)

            except KeyboardInterrupt:
                cleanup_list(outfile, emails, email_domain)

            except Exception:
                continue

        except KeyboardInterrupt:
            cleanup_list(outfile, emails, email_domain)

        except Exception:
            continue

    return emails


def cleanup_list(outfile, emails, email_domain):
    print("[+] Cleaning up output file")

    f = open(outfile, 'r')
    for email in f:
        email = email.replace('\n', '')
        emails.append(email)
    f.close()

    # remove duplicates from emails
    emails = set([email.lower() for email in emails])

    # create a list for final_emails
    final_emails = list()

    # remove emails not in the set domain
    for email in emails:
        if email_domain in email:
            final_emails.append(email)

    # write output
    f = open(outfile, 'w')
    for email in final_emails:
        f.write(email + '\n')
    f.close()

    # quit the script
    print(f"[+] Cleanup finished. Results output to {outfile}\n")
    sys.exit(0)


def main():
    # parse input for variables
    parser = argparse.ArgumentParser(description='LandScraper - Domain Email Scraper')
    parser.add_argument('-u', '--url', help='Starting URL')
    parser.add_argument('-d', '--domain', help='Domain name (if different from starting URL')
    parser.add_argument('-e', '--email', help='Email Domain')
    parser.add_argument('-o', '--output', help='Output file name')

    args = parser.parse_args()

    # disable insecure request warning
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # select url
    if args.url is not None:
        url = args.url
    else:
        url = manual_url()

    # select domain
    if args.domain is not None:
        domain = args.domain
    else:
        domain = url

    # select email domain
    if args.email is not None:
        email = args.email
    else:
        email = manual_email()

    # select output
    if args.output is not None:
        outfile = args.output
    else:
        outfile = manual_output()

    # create outfile if it does not exist
    myfile = Path(outfile)
    myfile.touch(exist_ok=True)

    # run the program
    emails = scrape(url, domain, email, outfile)

    # run cleanup on the output file
    cleanup_list(outfile, emails, email)


if __name__ == '__main__':
    main()
