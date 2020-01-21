import requests as req
import os
import shutil
import threading
import argparse
from bs4 import BeautifulSoup as BS
from time import time, sleep
from math import ceil

class ArgParser():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.add_arguments()
        self.args = self.parser.parse_args()
        self.validate_args()

    
    def add_arguments(self):
        self.parser.add_argument('--verbose', action='store_true', help='Print verbose status messages')
        self.parser.add_argument('-f', "--subreddit_file", help='The file in which the subreddits are stored')
        self.parser.add_argument('-c', "--category", help='The category, can be hot, top and new')


    def validate_args(self):
        if self.args.subreddit_file is not None:
            if not os.path.exists(self.args.subreddit_file):
                print("The specified subreddit file does not exist!")
                exit(1)
        else:
            self.args.subreddit_file = "subreddits.txt"

        if self.args.category is not None:
            if self.args.category not in [ "hot", "top", "new" ]:
                print("Invalid value for the category. Allowed values are 'hot', 'top' and 'new'.", 
                    "", sep="\n")
                exit(1)
        else:
            self.args.category = "hot"


    def get_arguments(self):
       return self.args

class RedditRipper():
    def __init__(self, is_verbose = False, subreddit_file = "subreddits.txt", category = "hot"):
        self.subreddit_file = subreddit_file
        self.subs = [ sub.rstrip("\n") for sub in open(self.subreddit_file) ]
        self.category = category
        self.data = {}
        self.file_type_list = [ "jpg", "jpeg", "png", "gif", "mp4" ]
        self.files = 0
        self.successful = 0
        self.failed = 0
        self.is_verbose = is_verbose


    '''Start the download process'''
    def run(self):
        self.get_posts_by_sub()
        self.make_sub_dirs()
        self.download_all_images()
        self.print_end_stats()

    
    '''
    Get the posts for the subreddits specified
    in the subreddits.txt file or the file
    specified by the command line argument
    '''
    def get_posts_by_sub(self):
        if len(self.subs) < 1:
            print("[-] No subreddits found!",
                  "[-] Please add subreddits to the subreddits.txt file or specify another file.",
                  "[?] Use redditripper.py -h or --help to get help", sep='\n')
            exit(1)

        for sub in self.subs:

            print(f"[+] Getting {self.category} posts for sub {sub}")
            url = f"http://api.reddit.com/r/{sub}/{self.category}?limit=100"

            try:
                res = req.get(url, headers={'User-agent': 'epic image downloader'})

                if res.status_code != 200:
                    print(f"[-] Fetching data for {sub} failed")
                    continue

                res = res.json()

                if len(res['data']['children']) < 1:
                    print(f"[-] Subreddit {sub} not found.")
                    continue

            except Exception as e:
                print(f"[-] Fetching data for {sub} failed")
                continue

            self.data[sub] = [ data['data']['url'] for data in res['data']['children'] ]
            self.files += len(self.data[sub])


    '''
    Create the directories where the 
    subreddit files will be stored
    '''
    def make_sub_dirs(self):
        for sub in self.subs:
            path = "images/%s" %(sub)
            if not os.path.exists(path):
                self.verbose_mode(f"[+] Making dir for {sub}")
                os.makedirs(path)


    '''
    The main "process" that downloads all the
    images that got fetched by the method
    get_posts_by_sub
    '''
    def download_all_images(self):
        print("",
              "***********************************************",
              f"[+] Starting download of {self.files} images in 2 seconds",
              "***********************************************",
              "", sep="\n")

        sleep(2)

        self.time_started = time()

        for sub in self.subs:
            t = []

            for url in self.data[sub]:
                filename = url[(url.rfind("/")+1):]
                path = f"images/{sub}/{filename}"

                if os.path.exists(path):
                    self.verbose_mode(f"[?] File {filename} exists")
                    continue

                try:
                    if filename[(filename.rfind(".")+1):] not in self.file_type_list and "gfycat" not in url:
                        self.verbose_mode(f"[?] Filetype {filename[(filename.rfind('.')+1):]} not allowed")
                        continue
                except Exception as e:
                    continue

                t.append(threading.Thread(target=self.download_image, args=(url, path,)))

            self.verbose_mode("[+] Starting threads")
            [ thread.start() for thread in t ]

            self.verbose_mode(f"[+] Waiting for threads of sub {sub} to finish")
            [ thread.join() for thread in t ]

            self.verbose_mode("[+] Threads have finished, continuing")


    '''
    This method downloads the image.

    Args:
        url: the url for the image
        path: the path where the file should be saved
    
    Returns:
        True or False whether the download was successful or not
    '''
    def download_image(self, url, path):
        if "gfycat" in url:
            url = self.get_gyfcat_url(url)

        if url is not None:
            try:
                result = req.get(url, stream=True)
            except Exception as e:
                self.verbose_mode(f"[-] Fetching image {url} failed")
                self.failed += 1
                return False

            if result.status_code != 200:
                self.verbose_mode(f"[-] URL {url} returned {result.status_code}")
                self.failed += 1
                return False

            try:
                self.verbose_mode(f"[+] Writing file {path}")
                with open(path, "wb") as f:
                    shutil.copyfileobj(result.raw, f)
            except Exception as e:
                    self.verbose_mode(f"[-] Writing {path} failed")
                    self.failed += 1
                    return False

            self.successful += 1
            return True
        else:
            return False


    def get_gyfcat_url(self, url):
        self.verbose_mode("[?] Detected gfycat URL")

        try:
            result = req.get(url)
        except Exception as e:
            return None

        if result.status_code != 200:
            return None

        soup = BS(result.text)
        videos = soup.find_all("source")
        print("****")
        print(videos)

    '''
    This method prints verbose messages if enabled

    Args:
        message: the message that gets printed
    '''
    def verbose_mode(self, message):
        if self.is_verbose:
            print(message)


    def print_end_stats(self):
        print("",
              "+===================STATS===========================+",
             f"[+] Finished downloading {len(self.subs)} subredddits in { ceil(((time( ) - self.time_started) * 100) / 100)} seconds",
              "+===================================================+",
             f"[+] Downloaded {self.successful} files successfully",
             f"[-] Download failed on {self.failed} files",
              "*****************************************************"
              "", sep="\n")

def main():
    if os.name == "nt": # Check if Windows or Linux
        os.system("cls")
    else:
        os.system("clear")

    argparser = ArgParser()
    args = argparser.get_arguments()

    reddit_ripper = RedditRipper(args.verbose, args.subreddit_file, args.category)

    reddit_ripper.run()

if __name__ == '__main__':
    main()
