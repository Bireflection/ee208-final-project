import os
from datetime import datetime
import re
import string
import random
import urllib.error
import urllib.parse
import urllib.request
import requests
import pandas as pd
import multiprocessing
from bs4 import BeautifulSoup


def date_generator(year):
    date = [datetime.strftime(x,'%Y%m%d') for x in list(pd.date_range(start= str(year) +"0101", end= str(year)+"1226"))]
    return date

def scroll_news_generator(date):
    url_list = []
    for i in range(len(date)):
        year = date[i][0:4]
        day = date[i][4:8]
        url_date = "https://www.chinanews.com.cn/scroll-news/{}/{}/news.shtml".format(year, day)
        url_list.append(url_date)
    return url_list

def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars)
    return s

def add_page_to_folder(page, title="", main_text="", time="", img=[], req=""):
    index_filename = 'index.txt'  # index.txt中每行是'网址 对应的文件名'
    folder = 'html_netease'  # 存放网页的文件夹
    additional_folder = valid_filename(title)
    filename = valid_filename(title)  # 将网址变成合法的文件名
    if (len(filename) > 200):
        filename = filename[0:200]
    filename += ".txt"
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

    
def get_url_to_crawl(url_list):
    url_to_crawl = []
    for i in range(len(url_list)):
        page = url_list[i]
        print(page)
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
            user_agent = random.choice(USER_AGENTS)
            req = urllib.request.Request(page)
            req.add_header('User-Agent',user_agent)
            
            req = urllib.request.urlopen(req, timeout=10)
            req = req.read()
            soup = BeautifulSoup(req, features="html.parser")
        
            for i in soup.findAll('div', {'class' : 'dd_lm'}):
                if i.contents[1].string == "体育":
                    title = i.nextSibling.nextSibling.contents[0].string
                    url = "https://www.chinanews.com.cn/" + i.nextSibling.nextSibling.contents[0].get("href")
                    url_to_crawl.append([url, title])
        except:
            print("fail")
        
    return url_to_crawl

def get_page(url_li):
    page = url_li[0]
    title = url_li[1]
    img = []
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
        user_agent = random.choice(USER_AGENTS)
        req = urllib.request.Request(page)
        req.add_header('User-Agent',user_agent)
        
        req = urllib.request.urlopen(req, timeout=10).read()
        soup = BeautifulSoup(req, features="html.parser")
        zw = soup.find('div', {'class' : 'left_zw'})
        main_text = ""
        for i in zw.contents:
            if i.string != None:
                main_text += i.string.strip()
        time = soup.find('div', {'class' : 'left-t'})
        if time == None:
            time = soup.find('div', {'class' : 'content_left_time'}).contents[0].string.strip().replace("\u3000","")
        else:
            time = time.contents[0].string.strip().replace("\u3000","")
        print(time)
        for i in soup.findAll('div', {"style":"text-align:center"}):
            x = i.contents[0]
            if x.get("src")[0:2] == "//":
                img.append(["https:" + x.get("src"), x.get("title","no title").replace("\u3000","")])
            else:
                img.append(["https://www.chinanews.com.cn/" + x.get("src"), x.get("title","no title").replace("\u3000","")])
    except:
        return  "", "", "", [],""
    return title, main_text, time, img, req

def add_page_to_folder(page, allfile, title="", main_text="", time="", img=[], req=""):
    # print(title)
    index_filename = 'index_chinanews.txt'  # index.txt中每行是'网址 对应的文件名'
    folder = 'html_chinanews'  # 存放网页的文件夹
    additional_folder = valid_filename(page)
    filename = valid_filename(page)  # 将网址变成合法的文件名
    if (len(filename) > 200):
        filename = filename[0:200]
    if ((filename + ".txt") in allfile):
        return
    filename += ".txt"
    allfile.append(filename)
    # title = str(title.encode('utf-8'))
    with lock:
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

def working(year):
    dates = date_generator(year)
    url_list = scroll_news_generator(dates)
    url_to_crawl = get_url_to_crawl(url_list)
    for i in range(len(url_to_crawl)):
        title, main_text, time, img, req = get_page(url_to_crawl[i])
        add_page_to_folder(url_to_crawl[i][0], title, main_text, time, img, req)
    
if __name__ == '__main__':
    lock = multiprocessing.Lock()
    pool = multiprocessing.Pool(7)
    for i in range(2016,2023):
        print(i)
        pool.apply_async(working,args=(i,))
    # t1 = multiprocessing.Process(target=working, args=(1))
    # t2 = multiprocessing.Process(target=working, args=(2))
    # t3 = multiprocessing.Process(target=working, args=(3))
    # t4 = multiprocessing.Process(target=working, args=(4))
    # t5 = multiprocessing.Process(target=working, args=(5))
    # t6 = multiprocessing.Process(target=working, args=(6))
    # t7 = multiprocessing.Process(target=working, args=(7))
    pool.close()
    pool.join()