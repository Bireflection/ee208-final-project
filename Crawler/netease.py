# SJTU EE208

import os
import queue
import re
import string
import threading
import time
import random
import urllib.error
import urllib.parse
import urllib.request
import requests
from bs4 import BeautifulSoup
from lxml import etree
from bs4.element import NavigableString 


def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars)
    return s


def working():
    rule = re.compile("^https://www.163.com/sports/.+$|^https://sports.163.com/.+$")
    while True:
        page = q.get()
        if page not in crawled:
            soup, title, main_text, time, img, req = get_page(page)
            # print(title)
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
                add_page_to_folder(page, allfile, title, main_text, time, img, req)
                crawled.append(page)
                print(page)
                varlock.release()
            q.task_done()
        else:
            q.task_done()


def get_page(page):
    try:
        USER_AGENTS = [
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.125 Safari/537.36',
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 UBrowser/6.2.3964.2 Safari/537.36'
            "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
            "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
            "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
            "Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
            "Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
            "Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5"
        ]
        USER_AGENTS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.62']
        # PROXY_LI = ["121.13.252.62", "61.216.185.88", "121.13.252.60", "183.236.232.160", "222.74.73.202", "192.168.1.101"]
        user_agent = random.choice(USER_AGENTS)
        req = urllib.request.Request(page)
        # print(req.get())
        req.add_header('User-Agent',user_agent)
        req.add_header('Aceept',"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9")
        
        req = urllib.request.urlopen(req, timeout=10)
        if (req.getcode() == 403):
            return "", "", "", "", "", ""
        req = req.read()
        # print(req)
        tree = etree.HTML(req,parser=etree.HTMLParser(encoding='utf-8'))
        # print(tree)
        soup = BeautifulSoup(req, features="html.parser")
        # print(soup)
        test = tree.xpath('//*[@id="container"]/div[1]/h1/text()')
        # print(test)
        if test == []:
            return soup, "", "", "", "",""
        title = tree.xpath('//*[@id="container"]/div[1]/h1/text()')[0]
        
        # if len(title) == 0:
        #     title = tree.xpath('//*[@id="ne_wrap"]/head/title/text()'[0])
        main_text = "".join(tree.xpath('//*[@id="content"]/div[2]//p/text()'))
        time = (tree.xpath('//*[@id="container"]/div[1]/div[2]/text()'))[0].replace(u'\u3000',u'').replace('\n', '').replace('\r', '').replace('\t', '').lstrip().rstrip()
        index = time.find("来源")
        time = time[:index]
        
        img = []
        cnt = 0
        for i in soup.findAll('p',{'class' : 'f_center'}):
            # print(type(i.contents[0]))
            if isinstance(i.contents[0], NavigableString):
                continue
            else:
                pho = i.contents[0].get('src',"")
                # print(i.contents[0].get('src'))
                if i.contents[0].get('alt') ==  None:
                    # print(i.contents[-1])
                    if i.contents[-1] != "":
                        des = i.contents[-1]
                    elif i.nextSibling.string != "":
                        des = i.nextSibling.string
                    else:
                        des = ''
                else:
                    des = i.contents[0].get('alt',"")
                img.append((pho, des))

        #     for i in soup.findAll('div',{'class' : 'post_author'}):
        #         content += i
        #         content += "\n"
        # else:
        #     for i in list(soup.stripped_strings):
        #     # print(type(i))
        #         content += i
        #         content += "\n"
        # print(title)
    except:
        return "", "", "", "", "",""
    return soup, title, main_text, time, img, req

def get_img(tree):
    img = tree.xpath('//*[@id="content"]/div[2]/p[3]/img@src')
    # print(img)
    if (img == None):
        return "No img"
    return img

def get_all_links(soup, page):
    links = []
    href = []
    if soup == "":
        return links
    all_content = soup.findAll('a', {'href': re.compile('^http|^/')})
    for tag in all_content:
        href.append(tag.get("href"))
    full = re.compile('^http.*')
    for i in href:
        if full.match(i) == None:
            i = urllib.parse.urljoin(page, i)
        links.append(i)
    return links


# 将网页存到文件夹里，将网址和对应的文件名写入index.txt中
def add_page_to_folder(page, allfile, title="", main_text="", time="", img=[], req=""):
    rule = re.compile("^https://www.163.com/sports/article/.+$")
    if rule.match(page):
        # print(title)
        index_filename = 'index.txt'  # index.txt中每行是'网址 对应的文件名'
        folder = 'html_netease'  # 存放网页的文件夹
        additional_folder = valid_filename(page)
        filename = valid_filename(page)  # 将网址变成合法的文件名
        if (len(filename) > 200):
            filename = filename[0:200]
        if ((filename + ".txt") in allfile):
            return
        filename += ".txt"
        allfile.append(filename)
        # title = str(title.encode('utf-8'))
        index = open(index_filename, 'a', encoding="utf-8")
        index.write(str(page.encode('ascii', 'ignore'))
                    [1:] + '\t' + title + '\t' + time + '\n')
        index.close()
        if not os.path.exists(folder):  # 如果文件夹不存在则新建
            os.mkdir(folder)
        if not os.path.exists(os.path.join(folder, additional_folder)): 
            os.mkdir(os.path.join(folder, additional_folder))
        f = open(os.path.join(folder, additional_folder, filename), 'w')
        f.write(title + "\n" + main_text + "\n")  # 将网页存入文件
        f.close()
        with open(os.path.join(folder, additional_folder, "source.html"), 'wb') as f:
            f.write(req)
        for i in range(len(img)):
            if (img[i][0] == ""):
                continue
            else:
                req = requests.get(img[i][0])
                if img[i][1] == "":
                    img_name = "{}.jpg".format(i+1)
                else:
                    img_name = "{}.jpg".format(img[i][1])
                    img_name = img_name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
                    if (len(img_name) > 100):
                        img_name = img_name[0:50] + '.jpg'
                f = open(os.path.join(folder, additional_folder, img_name), 'wb')#以二进制格式写入img文件夹中
                f.write(req.content)
                f.close()
        if not os.path.exists(os.path.join(folder, additional_folder, filename)):
            exit(-1)
    else:
        return

if __name__ == '__main__':
    q = queue.Queue()
    q.put("https://sports.163.com/")
    # q.put("https://www.163.com/sports/article/HNQL0CVN00059D57.html")
    # q.put("https://www.163.com/sports/article/HNLP6AG90005877U.html")
    # q.put("https://www.163.com/sports/article/HNR0K81U00059D57.html")
    allfile = []
    crawled = []
    graph = {}
    varlock = threading.Lock()
    maxnum = 15000
    thread_num = 15
    start_time = time.time()
    for i in range(thread_num):
        t = threading.Thread(target=working)
        t.setDaemon(True)
        t.start()
    q.join()
    end_time = time.time()
    print(end_time - start_time)
