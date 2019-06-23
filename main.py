import requests as req
import os
import shutil
import threading
from time import time
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
        self.timeStarted = time()

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

    def makeSubDirs(self):
        for sub in self.subs:
            path = "images/%s" %(sub)
            if not os.path.exists(path) and not os.path.isdir(path):
                print("[+] Making dir for %s" %(sub))
                os.makedirs(path)

    def downloadAllImages(self):
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
                        print("[?] Filetype not allowed")
                        continue
                except Exception as e:
                    continue

                t.append(threading.Thread(target=self.downloadImage, args=(url, path,)))

            for thread in t:
                thread.start()

            try:
                t[len(t)-1].join()
            except Exception as e:
                continue


    def downloadImage(self, url, path):
        try:
            result = req.get(url, stream=True)
        except Exception as e:
            print("[-] Fetching image %s failed" %(url))
            return

        if not result.status_code == 200:
            print("[-] URL {} returned {}".format(url, result.status_code))
            return

        try:
            print("[+] Writing file %s" %(path))
            with open(path, "wb") as f:
                shutil.copyfileobj(result.raw, f)
        except Exception as e:
                print("[-] Writing %s failed" %(path))

    def printEndTime(self):
        print("[+] Finished downloading {} subredddits in {} seconds".format(len(self.subs),(ceil((time( ) - self.timeStarted) * 100) / 100)))

def main():
    dl = Download()
    dl.getPostsBySub()
    dl.makeSubDirs()
    dl.downloadAllImages()
    dl.printEndTime()

if __name__ == '__main__':
    main()
