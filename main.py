import requests as req
import os
import shutil
import threading
from time import time, sleep
from math import ceil

if os.name == "nt": # Check if Windows or Linux
    os.system("cls")
else:
    os.system("clear")

class Download():
    def __init__(self):
        self.subs = [ sub.rstrip("\n") for sub in open("subreddits.txt") ]
        self.data = {}
        self.fileTypeList = [ "jpg", "jpeg", "png", "gif" ]
        self.files = 0
        self.successful = 0;
        self.failed = 0;

    def getPostsBySub(self):
        for sub in self.subs:
            print("[+] Getting hottest posts for sub %s" %(sub))
            url = "http://api.reddit.com/r/%s/hot?limit=100" %(sub)
            try:
                res = req.get(url, headers={'User-agent': 'Epic image downloader'}).json()
            except Exception as e:
                print("[-] Fetching data for %s failed" %(sub))
                continue

            self.data[sub] = [ data['data']['url'] for data in res['data']['children'] ]
            self.files += len(self.data[sub])

    def makeSubDirs(self):
        for sub in self.subs:
            path = "images/%s" %(sub)
            if not os.path.exists(path) and not os.path.isdir(path):
                print("[+] Making dir for %s" %(sub))
                os.makedirs(path)

    def downloadAllImages(self):
        print(  "\n***********************************************",
                "[+] Starting download of %d images in 2 seconds" %(self.files),
                "***********************************************\n", sep="\n")
        sleep(2)
        self.timeStarted = time()
        for sub in self.subs:
            t = []
            for url in self.data[sub]:

                filename = url[(url.rfind("/")+1):]
                path = "images/%s/%s" %(sub, filename)

                if os.path.exists(path):
                    print("[?] File %s exists" %(filename))
                    continue

                try:
                    if filename[(filename.rfind(".")+1):] not in self.fileTypeList:
                        print("[?] Filetype %s not allowed" %(filename[(filename.rfind(".")+1):]))
                        continue
                except Exception as e:
                    continue

                t.append(threading.Thread(target=self.downloadImage, args=(url, path,)))

            print("[+] Starting threads")
            [ thread.start() for thread in t ]

            print("[+] Waiting for threads of sub %s to finish" %(sub))
            [ thread.join() for thread in t ]

            print("[+] Threads have finished, continuing")

    def downloadImage(self, url, path):
        try:
            result = req.get(url, stream=True)
        except Exception as e:
            print("[-] Fetching image %s failed" %(url))
            self.failed += 1
            return

        if not result.status_code == 200:
            print("[-] URL {} returned {}".format(url, result.status_code))
            self.failed += 1
            return

        try:
            print("[+] Writing file %s" %(path))
            with open(path, "wb") as f:
                shutil.copyfileobj(result.raw, f)
        except Exception as e:
                print("[-] Writing %s failed" %(path))
                self.failed += 1
                return

        self.successful += 1

    def printEndStats(self):
        print(  "\n+===================STATS===========================+",
                "[+] Finished downloading {} subredddits in {} seconds".format(len(self.subs),(ceil((time( ) - self.timeStarted) * 100) / 100)),
                "+===================================================+",
                "[+] Downloaded %d files successfully" %(self.successful),
                "[-] Download failed on %d files" %(self.failed),
                "*****************************************************", sep="\n")

def main():
    dl = Download()
    dl.getPostsBySub()
    dl.makeSubDirs()
    dl.downloadAllImages()
    dl.printEndStats()

if __name__ == '__main__':
    main()
