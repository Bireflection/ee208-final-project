# SJTU EE208
import os
import re
import string
import urllib.error
import urllib.parse
import urllib.request
import threading
import time
import queue
from bs4 import BeautifulSoup
from urllib.parse import urlparse



def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars)
    return s


def working():
    rule = re.compile("^https://www.163.com/sports/.+$")
    while True:
        page = q.get()
        if page not in crawled:
            content, soup, title, imgset = get_page(page)
            outlinks = get_all_links(soup, page)
            for links in outlinks:
                if (rule.match(links)):
                    q.put(links)
            if (varlock.acquire()):
                if (len(crawled) >= maxnum):
                    while(not q.empty()):
                        x = q.get()
                        q.task_done()
                    varlock.release()
                    q.task_done()
                    break
                graph[page] = outlinks
                add_page_to_folder(page, content, allfile, title, imgset)
                crawled.append(page)
                print(page)
                varlock.release()
            q.task_done()
        else:
            q.task_done()


def get_page(page):
    content = []
    imgset = []
    full = re.compile('^http.*')
    try:
        req = urllib.request.Request(page)
        req.add_header(
            'User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.3964.2 Safari/537.36')
        req = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(req, features="html.parser")
        title = soup.head.title.string.strip()
        for i in soup.findAll('img'):
            img = i.get('src')
            name = i.get('alt')
            if (img != None) and (name != None):
                if img in imgset:
                    pass
                else:
                    img.strip()
                    name.strip()
                    if img == "" or name == "":
                        pass
                    elif full.match(img):
                        imgset.append(img)
                        content.append(name)
                    else:
                        pass
    except:
        return [], "", "", []
    return content, soup, title, imgset


def get_all_links(content, page):
    links = []
    href = []
    if content == "":
        return links
    all_content = content.findAll('a', {'href': re.compile('^http|^/')})
    for tag in all_content:
        href.append(tag.get("href"))
    full = re.compile('^http.*')
    for i in href:
        if full.match(i) == None:
            i = urllib.parse.urljoin(page, i)
        links.append(i)
    # for i in range(1000):
    #     links.append(page[:-2]+"{}".format(i))
    return links


# 将网页存到文件夹里，将网址和对应的文件名写入index.txt中
def add_page_to_folder(page, content, allfile, title="", imgset=[]):
    index_filename = 'index_photo.txt'  # index.txt中每行是'网址 对应的文件名'
    folder = 'html_photo'  # 存放网页的文件夹
    filename = valid_filename(page)  # 将网址变成合法的文件名
    if (len(filename) > 200):
        filename = filename[0:200]
    if ((filename + ".txt") in allfile) and (filename.find(".")):
        return
    filename += ".txt"
    allfile.append(filename)
    index = open(index_filename, 'a', encoding="utf-8")
    index.write(str(page.encode('ascii', 'ignore'))
                [1:] + '\t' + filename + '\t' + title + '\n')
    index.close()
    if not os.path.exists(folder):  # 如果文件夹不存在则新建
        os.mkdir(folder)
    f = open(os.path.join(folder, filename), 'w')
    for i in range(len(imgset)):
        f.write(str(content[i]+imgset[i]+"\n"))
    f.close()
    if not os.path.exists(os.path.join(folder, filename)):
        exit(-1)


if __name__ == '__main__':
    q = queue.Queue()
    q.put("https://sports.163.com/")
    allfile = []
    crawled = []
    graph = {}
    varlock = threading.Lock()
    maxnum = 500
    thread_num = 8
    start_time = time.time()
    for i in range(thread_num):
        t = threading.Thread(target=working)
        t.setDaemon(True)
        t.start()
    q.join()
    end_time = time.time()
    print(end_time - start_time)