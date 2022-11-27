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


def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars)
    return s


def working():
    while True:
        page = q.get()
        if page not in crawled:
            content, soup, title = get_page(page)
            outlinks = get_all_links(soup, page)
            for links in outlinks:
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
                add_page_to_folder(page, content, allfile, title)
                crawled.append(page)
                print(page)
                varlock.release()
            q.task_done()
        else:
            q.task_done()


def get_page(page):
    content = ''
    try:
        req = urllib.request.Request(page)
        req.add_header(
            'User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.3964.2 Safari/537.36')
        req = urllib.request.urlopen(req, timeout=10)
        req = req.read()
        req2 = req.decode()
        # encoding1 = re.findall('<meta.*?charset="?([\w-]*).*>', req2, re.I)
        # encoding2 = re.findall('<meta.*(http-equiv="?Content-Type"?.*)?charset="?([a-zA-Z0-9_-]+)"?', req2, re.I)
        # if encoding1:
        #     ans =  encoding1[0]
        # else:
        #     ans = 'utf-8'
        soup = BeautifulSoup(req, features="html.parser", from_encoding="gb18030")
        title = soup.head.title.string.strip()
        # content = ''.join(soup.findAll(text=True))
        for i in list(soup.stripped_strings):
            # print(type(i))
            content += i
            content += "\n"
    except:
        return "", "", ""
    return content, soup, title


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
    return links


def add_page_to_folder(page, content, allfile, title=""):  # 将网页存到文件夹里，将网址和对应的文件名写入index.txt中
    index_filename = 'index.txt'  # index.txt中每行是'网址 对应的文件名'
    folder = 'html'  # 存放网页的文件夹
    filename = valid_filename(page)  # 将网址变成合法的文件名
    if (len(filename) > 200):
        filename = filename[0:200]
    cnt = 0
    if ((filename + ".txt") in allfile) and (filename.find(".")):
        filename += ".1"
        cnt += 1
    while ((filename + ".txt") in allfile):
        cnt += 1
        filename = filename[::-1]
        ind = filename.find(".")
        filename = str(cnt) + filename[ind:]
        filename = filename[::-1]
    filename += ".txt"
    allfile.append(filename)
    index = open(index_filename, 'a', encoding="utf-8")
    index.write(str(page.encode('ascii', 'ignore'))
                [1:] + '\t' + filename + '\t' + title + '\n')
    index.close()
    if not os.path.exists(folder):  # 如果文件夹不存在则新建
        os.mkdir(folder)
    f = open(os.path.join(folder, filename), 'w')
    f.write(str(content))  # 将网页存入文件
    f.close()
    if not os.path.exists(os.path.join(folder, filename)):
        exit(-1)


if __name__ == '__main__':
    q = queue.Queue()
    q.put('https://image.baidu.com/')
    allfile = []
    crawled = []
    graph = {}
    varlock = threading.Lock()
    maxnum = 10000
    thread_num = 32
    start_time = time.time()
    for i in range(thread_num):
        t = threading.Thread(target=working)
        t.setDaemon(True)
        t.start()
    q.join()
    end_time = time.time()
    print(end_time - start_time)
