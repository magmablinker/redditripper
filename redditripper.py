import requests as req
import os
import shutil
import threading
import argparse
from bs4 import BeautifulSoup as BS
from time import time, sleep
from math import ceil
from random import uniform

class ArgParser():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.add_arguments()
        self.args = self.parser.parse_args()
        self.validate_args()

    
    def add_arguments(self):
        self.parser.add_argument('--verbose', action='store_true', help='Print verbose status messages. The default value is False')
        self.parser.add_argument('-f', "--subreddit_file", help='The file in which the subreddits are stored. The default value is "subreddits.txt"')
        self.parser.add_argument('-c', "--category", help='The category, can be hot, top and new. The default value is "hot"')
        self.parser.add_argument("-l", "--limit", help='The amount of posts you want to fetch per subreddit. Can be from 1 to 100. The default value is 100.')
        self.parser.add_argument("-o", "--image_output_dir", help='The output directory for downloads. Default is "downloads/"')


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

        if self.args.limit is not None:
            try:
                self.args.limit = int(self.args.limit)
            except Exception as e:
                print("[-] The post limit has to be a number!")
                exit(1)

            if self.args.limit < 1:
                print("[-] The minimal allowed limit is 1.")
                exit(1)
            elif self.args.limit > 100:
                print("[-] The maximal allowed limit is 100.")
                exit(1)
        else:
            self.args.limit = 100

        if self.args.image_output_dir is not None:
            if not os.path.exists(self.args.image_output_dir) or not os.path.isdir(self.args.image_output_dir):
                print("[-] Invalid image output directory. Use --help for help.")
                exit(1)
        else:
            self.args.image_output_dir = "downloads"

    def get_arguments(self):
       return self.args

class RedditRipper():
    def __init__(self, is_verbose = False, subreddit_file = "subreddits.txt", category = "hot", limit = 100, image_output_dir = "downloads"):
        self.subreddit_file = subreddit_file
        self.subs = [ sub.rstrip("\n") for sub in open(self.subreddit_file) ]
        self.category = category
        self.limit = limit
        self.data = {}
        self.file_type_list = [ "jpg", "jpeg", "png", "gif", "mp4" ]
        self.files = 0
        self.successful = 0
        self.failed = 0
        self.is_verbose = is_verbose
        self.image_output_dir = image_output_dir
        self.gfycat_failed = 0


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
            url = f"http://api.reddit.com/r/{sub}/{self.category}?limit={self.limit}"

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
            path = f"{self.image_output_dir}/{sub}"
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
                path = f"{self.image_output_dir}/{sub}/{filename}"

                if os.path.exists(path):
                    self.verbose_mode(f"[?] File {filename} exists, skipping it")
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
        if "gfycat" in url and self.gfycat_failed < 10:
            url = self.get_gyfcat_url(url)
            path += ".mp4"
        elif self.gfycat_failed == 10:
            print("*******************************",
                  "[!] gfycat rate limit detected ",
                  "[!] stopping download of gfycat",
                  "[!] urls.                      ", 
                  "*******************************", sep="\n")
        elif self.gfycat_failed > 10:
            return False

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
            self.failed += 1
            return False

    '''
    This method downloads a video from gfycat.

    Args:
        url: the url to the gfycat video.

    Returns:
        The source url for the media found on the url.

    '''
    def get_gyfcat_url(self, url):
        self.verbose_mode("[?] Detected gfycat URL")

        sleeptime = uniform(1, 4)

        self.verbose_mode(f"[?] Sleeping for {sleeptime}s to avoid rate limit")
        sleep(sleeptime)

        try:
            result = req.get(url, timeout=2)
        except Exception as e:
            self.verbose_mode(f"[-] Exception: failed to fetch gfycat data for url {url}")
            self.gfycat_failed += 1
            return None

        if result.status_code != 200:
            self.verbose_mode(f"[-] Failed to fetch gfycat data for url {url} response code {result.status_code}")
            self.gfycat_failed += 1
            return None

        soup = BS(result.text, features="lxml")
        video = soup.find("source", attrs={'type': 'video/mp4'})

        try:
            video = video.get('src')
        except Exception as e:
            self.verbose_mode(f"[-] Failed to fetch the source for the url {url}")
            self.gfycat_failed += 1
            video = None

        return video

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
             f"[+] Finished downloading {len(self.subs)} subredddits in {ceil(((time( ) - self.time_started) * 100) / 100)} seconds",
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

    reddit_ripper = RedditRipper(args.verbose, args.subreddit_file, args.category, args.limit, args.image_output_dir)

    reddit_ripper.run()

if __name__ == '__main__':
    main()
