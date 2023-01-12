import os
import string
import random
import urllib.error
import urllib.parse
import urllib.request


def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars)
    return s

if __name__ == '__main__':
    root = "html_netease"
    with open("index.txt", "r") as f:
        line = f.readlines()
        for i in line:
            url = i.split()[0].strip("'")
            folder_name = valid_filename(url)
            print("downloading", folder_name)
            try:
                USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.62']
                user_agent = USER_AGENTS[0]
                req = urllib.request.Request(url)
                req.add_header('User-Agent',user_agent)
                req.add_header('Aceept',"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9")
                req = urllib.request.urlopen(req, timeout=30)
                req = req.read()
                folder = os.path.join(root, folder_name)
                with open(os.path.join(folder, "source.html"), 'wb') as f:
                    f.write(req)

            except Exception as e:
                print("Failed in download:", e)
