# <center> Lab 15 Final
</center>

<center> 第八组 陈可 贾涵 朱鑫炜 喻智勇
</center>

# 实验环境

本次实验基于Docker当中的sjtucmic/ee208镜像。在此基础上使用了原环境当中没有的库，列举如下：

- requests
- pandas
- chardet
- face_recognition(依赖库为cmake, dlib)
- jieba
- sklearn
- bootstrap-flask

# 任务分工

- 陈可：定向采集 2-3 个新闻网站特定类别（本次实验为体育类）的新闻，并进行关键词、图片搜索，时间、相关度排序，网站制作，汇报展示
- 朱鑫炜：基于人脸的新闻搜索
- 贾涵：相似新闻的自动聚类
- 喻智勇：协助

# 实验流程

## 任务一 爬虫 作者：陈可

### 网站的选择

&ensp;&ensp;&ensp;&ensp;在选择我们组所需要的网站的时候，我在很多网站当中做过对比，最后选择了网易体育以及中国新闻网的体育频道。选择这两个新闻网站的原因在于，它们的网址都有明确分类，这一点相比于澎湃新闻等网站相比要便于分类。同时，中国新闻网提供了滚动新闻，即将一天内的所有新闻集中在一页上的页面。这样便于爬取，也不需要重新加载。

&ensp;&ensp;&ensp;&ensp;但是在实际爬虫当中遇到了比预期更多的问题，将在后面的报告中说明。本次的实验源代码全部基于本人的Lab5的代码改动而来。

&ensp;&ensp;&ensp;&ensp;要注意的是，现在的文件结构发生了改变，原先为html_netease的文件夹现在与接下来要提到的html_chinanews合并为了html文件夹。一部分的代码可能因此而发生变动，这里保留的是未改动的代码（因为不需要再次爬取了）
### 爬虫任务——网易体育

&ensp;&ensp;&ensp;&ensp;首先是网易体育的爬取。由于爬虫时修改较多，此次任务共使用了三分代码文件。按照使用的时间顺序首先介绍netease.py文件。

&ensp;&ensp;&ensp;&ensp;首先是主程序working。首先设定规则为网易体育的两类域名，不符合此规则的网页不予爬取。接着调用get_page函数获取页面信息，利用get_all_links获取之后需要爬取的网页，并加入队列。最后，存储爬取到的数据。
函数体如下：

```python
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
```

&ensp;&ensp;&ensp;&ensp;然后是get_page函数。get_page函数为了防止被系统识别为爬虫，采用了多种header，使用random函数选一个header进行爬虫，并且增加响应格式等参数进行爬虫。如果识别到错误返回码（400，403等）则返回空。同时使用etree和beautifulsoup对于响应进行解析。test参数用于读取标题，如果没有标题则继续返回空。利用xpath获取正文，时间，并对时间进行去除无用字符的处理。

```python
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
user_agent = random.choice(USER_AGENTS)
req = urllib.request.Request(page)
req.add_header('User-Agent',user_agent)
req.add_header('Aceept',"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9")

req = urllib.request.urlopen(req, timeout=10)
if (req.getcode() == 403 or req.getcode() == 400):
    return "", "", "", "", "", ""
req = req.read()
tree = etree.HTML(req,parser=etree.HTMLParser(encoding='utf-8'))
soup = BeautifulSoup(req, features="html.parser")
test = tree.xpath('//*[@id="container"]/div[1]/h1/text()')
if test == []:
    return soup, "", "", "", "",""
title = tree.xpath('//*[@id="container"]/div[1]/h1/text()')[0]

main_text = "".join(tree.xpath('//*[@id="content"]/div[2]//p/text()'))
time = (tree.xpath('//*[@id="container"]/div[1]/div[2]/text()'))[0].replace(u'\u3000',u'').replace('\n', '').replace('\r', '').replace('\t', '').lstrip().rstrip()
index = time.find("来源")
time = time[:index]
```

&ensp;&ensp;&ensp;&ensp;随后处理图片。第一个问题出现，网易新闻当中，有关图片的所在位置多种多样，杂乱无章，无法使用xpath。使用beautifulsoup获取图片。z这里调用的bs4里面的NavigableString类。我们先找到f_center分类，如果得到的元素类型是NavigableString，则舍弃不要，然后去找照片的地址。同时，我们也尽力去找到照片的描述。如果能用alt则用alt，不能去找它附近的文字描述。这是目前的解决方法。由于不同img在des部分的区别过大，部分图片会出现图片的名字是js函数的情况。但是，由于图片数量多，这种情况所占比例不是很大，对最后结果的影响不算太大。

```python
img = []
for i in soup.findAll('p',{'class' : 'f_center'}):
    if isinstance(i.contents[0], NavigableString):
        continue
    else:
        pho = i.contents[0].get('src',"")
        if i.contents[0].get('alt') ==  None:
            if i.contents[-1] != "":
                des = i.contents[-1]
            elif i.nextSibling.string != "":
                des = i.nextSibling.string
            else:
                des = ''
        else:
            des = i.contents[0].get('alt',"")
        img.append((pho, des))
```

&ensp;&ensp;&ensp;&ensp;然后是get_all_links函数。这与往期Lab的代码一样，用途是识别是相对地址还是绝对地址，如果为相对地址则加上域名。

```python
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
```

&ensp;&ensp;&ensp;&ensp;add_page_to_folder函数的作用在于将网页存进文件夹里。与往期lab不一样的地方在于，这个函数同时具备把图片下载的能力。使用requests库来获取图片，以二进制储存，修改文件名使其合法。

```python
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
```

&ensp;&ensp;&ensp;&ensp;最后是主函数,使用了多线程。这里maxnum和最后的数目不一致，是我人为中止所造成的（硬盘空间问题）

```python
if __name__ == '__main__':
    q = queue.Queue()
    q.put("https://sports.163.com/")
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
```

&ensp;&ensp;&ensp;&ensp;同时介绍两个小的代码文件。首先是download.py。顾名思义，由于写netease.py的时候没有下载原网页，为了后期使用方便，增加的。只是单纯的请求网页并下载，不在过多阐述。

```python
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
```

&ensp;&ensp;&ensp;&ensp;其次是getkeyword.py，用于从网页的keyword字段提取关键词。基于之前下载的网页进行操作，使用beautifulsoup找到keyword所在位置，有就存下来。

```python
import os
from bs4 import BeautifulSoup
for (root, dirs, files) in os.walk('html_chinanews'):
    if root != 'html_chinanews':
        try:
            with open(os.path.join(root, 'source.html'), 'r') as f:
                a = f.read()
                soup = BeautifulSoup(a,features="html.parser")
                tag = soup.find('meta',{'name' : 'keywords'})
                with open(os.path.join(root, 'keyword.txt'), 'w') as g:
                    if tag != None:
                        g.write(tag['content'])
                    else:
                        g.write("No keyword")
        except:
            continue
```

&ensp;&ensp;&ensp;&ensp;以上便是爬取netease的全部代码。

## 爬虫任务——中国新闻网体育

&ensp;&ensp;&ensp;&ensp;按照爬取新闻年份的不同，分为两份文件：chinanews_old.py和chinanews_new.py。不同的年份的编码等有特殊处理，且遇到了一些问题，故分为两份代码。

&ensp;&ensp;&ensp;&ensp;首先从old开始，介绍一下对于中国新闻网滚动网页的思路。

&ensp;&ensp;&ensp;&ensp;观察可知，滚动新闻从16年到现在依旧保持着同一个结构。所以我们利用这种结构（如下代码所示）产生一下滚动新闻的网页url。在这里，我们要先产生一个日期序列。这里date_generator函数利用pandas产生一个日期序列，再利用datetime库当中的strfttime方法规定格式。传入scroll_news_generator函数当中，产生url列表。

```python
def date_generator(year):
    date = [datetime.strftime(x,'%Y%m%d') for x in list(pd.date_range(start= str(year) +"0101", end= str(year)+"1231"))]
    return date

def scroll_news_generator(date):
    url_list = []
    for i in range(len(date)):
        year = date[i][0:4]
        day = date[i][4:8]
        url_date = "https://www.chinanews.com.cn/scroll-news/{}/{}/news.shtml".format(year, day)
        url_list.append(url_date)
    return url_list
```

&ensp;&ensp;&ensp;&ensp;我们访问页面观察，滚动新闻如下图所示。可以看到，每个新闻的前面都会有一个分类。我们找到其中写着体育的新闻，获取对应url,访问即可。因此我们使用如下get_url_to_crawl函数，利用beautifulsoup找到这些类别标签所对应的dd_lm类，如果是体育类，则保存标题和对应的url。

![滚动新闻页面](/report/chinanews_exp.jpg "chinanews滚动新闻页面")
<center> chinanews滚动新闻页面
</center>

```python
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
```

&ensp;&ensp;&ensp;&ensp;下面就是顺着我们所得到的url去爬取网站。首先，我们可以在类型为left-t的地方找到时间，在left_zw找到正文。当然，老页面有所不同，时间在content_left_time里面，我也做了判定。

![time_zw](/report/time_zw.jpg "time_zw")

<center> 时间和正文 </center>

&ensp;&ensp;&ensp;&ensp;随后我们去找图片。可以看到，图片在text-align:center里面。我们分析里面的src，如果是//开头的，则为缺少https，如果头部具有http，则直接访问即可。而关于图片的名字，如果有title类就以其内容为名字，如果没有，认为这张图片没名字。

![chinanews_pic](/report/chinanews_pic.jpg "chinanews_pic")
<center> src分析 </center>

```python
def get_page(url_li):
    page = url_li[0]
    title = url_li[1]
    img = []
    print(title)
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
        soup = BeautifulSoup(req, features="html.parser",from_encoding="gb18030")
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
            elif x.get("src")[0:4] == 'http':
                img.append([x.get("src"), x.get("title","no title").replace("\u3000","")])
            else:
                img.append(["https://www.chinanews.com.cn/" + x.get("src"), x.get("title","no title").replace("\u3000","")])
    except:
        return  "", "", "", [], b''
    return title, main_text, time, img, req
```

&ensp;&ensp;&ensp;&ensp;然后就是网页的储存。问题随之出现。在老网页，例如16年的网页，用的是GB2312，新网页用的是utf-8。为了分析我获取的是什么样子的网页，引入了一个新的库为chardet，它能分析出网页的编码。但是，它将utf-8认成了KOI-8，gb2312却可以识别。无奈之下，分为了两个文件。
&ensp;&ensp;&ensp;&ensp;对于老网页来说，判断其编码，没有编码证明没爬取成功，如果是gb2312就将其转为gb18030（足够大）然后进行储存，储存方法和网易那边类似，不再展开。

```python
def add_page_to_folder(page, title="", main_text="", time="", img=[], req=""):
    try:
        print(title)
        way_of_encoding = chardet.detect(req)
        if way_of_encoding['encoding'] == None:
            return
        elif way_of_encoding['encoding'] == 'GB2312':
            way_of_encoding['encoding'] = 'gb18030'
        index_filename = 'index_chinanews.txt'  # index.txt中每行是'网址 对应的文件名'
        # folder = 'html_chinanews'  # 存放网页的文件夹
        folder = 'test_chinanews'
        additional_folder = valid_filename(page)
        filename = valid_filename(page)  # 将网址变成合法的文件名
        if (len(filename) > 200):
            filename = filename[0:200]

        filename += ".txt"

        # title = str(title.encode('utf-8'))
        # with lock:
        index = open(index_filename, 'a', encoding="utf-8")
        index.write(str(page.encode('ascii', 'ignore'))
                    [1:] + '\t' + title + '\t' + time + '\n')
        index.close()

        if not os.path.exists(folder):  # 如果文件夹不存在则新建
            os.mkdir(folder)
        if not os.path.exists(os.path.join(folder, additional_folder)): 
            os.mkdir(os.path.join(folder, additional_folder))
        f = open(os.path.join(folder, additional_folder, filename), 'w', encoding="utf-8")
        f.write(title + "\n"+ main_text + "\n")  # 将网页存入文件
        f.close()
        # with open(os.path.join(folder, additional_folder, "cece.txt"), 'w' ) as f:
        #     f.write(req)
        with open(os.path.join(folder, additional_folder, "source.html"), 'wb') as f:
            f.write(req.decode(way_of_encoding['encoding']).encode("utf-8"))
        for i in range(len(img)):
            if (img[i][0] == ""):
                continue
            else:
                req = requests.get(img[i][0])
                print(req.text)
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
    except:
        print("ERROR")
        folder = 'html_chinanews'  # 存放网页的文件夹
        additional_folder = valid_filename(page)
        with open(os.path.join(folder, additional_folder, "WRONG.TXT"),'w') as f:
            f.write("WRONG")
```

&ensp;&ensp;&ensp;&ensp;然后是working函数，调用这些函数。随后，主函数采用了多进程（multiprocessing）库。但是，第一次尝试的时候，电脑内存爆了。查阅资料得知，python在多进程的时候，内存回收会出现问题。随后实验了更多方法（源代码注释部分），无结果。最后又因为后面将新旧网页分开，所以旧网页使用多进程和进程池，但只有三个进程（3年），就不会爆内存了。新网页则是一年一年的爬（只爬了2022年的，硬盘满了）。主函数如下：

```python
if __name__ == '__main__':
    lock = multiprocessing.Lock()
    pool = multiprocessing.Pool(3)
    for i in range(2016,2019):
        print(i)
        pool.apply_async(working,args=(i,))
    pool.close()
    pool.join()
```

&ensp;&ensp;&ensp;&ensp;chinanews_new.py和old的区别仅在以下函数。首先判断req类型，不是字节类型转成字节类型。不再转码。
```python
def add_page_to_folder(page, title="", main_text="", time="", img=[], req=""):
    try:
        print(title)
        if (type(req) == bytes):
            req = req
        else:
            # print(req.text)
            req = req.content
        
        index_filename = 'index_chinanews_2022.txt'  # index.txt中每行是'网址 对应的文件名'
        # folder = 'html_chinanews'  # 存放网页的文件夹
        folder = 'test_for_chinanews'
        additional_folder = valid_filename(page)
        filename = valid_filename(page)  # 将网址变成合法的文件名
        if (len(filename) > 200):
            filename = filename[0:200]

        filename += ".txt"

        # title = str(title.encode('utf-8'))
        # with lock:
        index = open(index_filename, 'a', encoding="utf-8")
        index.write(str(page.encode('ascii', 'ignore'))
                    [1:] + '\t' + title + '\t' + time + '\n')
        index.close()

        if not os.path.exists(folder):  # 如果文件夹不存在则新建
            os.mkdir(folder)
        if not os.path.exists(os.path.join(folder, additional_folder)): 
            os.mkdir(os.path.join(folder, additional_folder))
        f = open(os.path.join(folder, additional_folder, filename), 'w', encoding="utf-8")
        f.write(title + "\n"+ main_text + "\n")  # 将网页存入文件
        f.close()
        # with open(os.path.join(folder, additional_folder, "cece.txt"), 'w' ) as f:
        #     f.write(req)
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
                    img_name = img_name.replace('\\', '').replace('/', '').replace(':', '').replace('*', '').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '').replace('\n', '').strip()
                    if (len(img_name) > 100):
                        img_name = img_name[0:50] + '.jpg'
                f = open(os.path.join(folder, additional_folder, img_name), 'wb')#以二进制格式写入img文件夹中
                f.write(req.content)
                f.close()
        if not os.path.exists(os.path.join(folder, additional_folder, filename)):
            exit(-1)
    except:
        print("ERROR")
        folder = 'html_chinanews'  # 存放网页的文件夹
        additional_folder = valid_filename(page)
        with open(os.path.join(folder, additional_folder, "WRONG.TXT"),'w') as f:
            f.write("WRONG")
```

### 第一部分总结
&ensp;&ensp;&ensp;&ensp;受限于电脑硬盘，在后面将文件统一移到html的时候丢失了几个文件，但问题不大。代码中提到的index.txt和index_chinanews.txt等类似物都合并到了index.txt文件当中。

&ensp;&ensp;&ensp;&ensp;在网页的爬取中遇到了很多稀奇的事情，例如编码类型，例如多进程内存溢出等等。幸好对于结果的影响不算太大。

## 任务二 建立索引 作者：陈可
&ensp;&ensp;&ensp;&ensp;爬取完网站之后就是索引。这部分和往期lab一模一样，在此基础上增加了一个类叫做t3，用于储存时间数据。利用urlparse返回的数据得到域名，这样便于我搜索的时候进行域名搜索。

&ensp;&ensp;&ensp;&ensp;对于时间，网易的时间能精确到秒，中国新闻网不行，于是将长度用00补齐。对于一篇文档，可以存很多照片。为了匹配照片，我们将文件夹里所有的图片放进一个字符串里面。这样搜索的时候就可以搜得到。至于找到我们所需的图片，那是搜索时干的事情，后面会提到。
```python
def indexDocs(self, root, writer):
    t1 = FieldType()
    t1.setStored(True)
    t1.setTokenized(False)
    t1.setIndexOptions(IndexOptions.NONE)  # Not Indexed

    t2 = FieldType()
    t2.setStored(True)
    t2.setTokenized(True)
    # Indexes documents, frequencies and positions.
    t2.setIndexOptions(IndexOptions.DOCS_AND_FREQS_AND_POSITIONS)

    t3 = FieldType()
    t3.setStored(True)
    t3.setTokenized(True)
    t3.setIndexOptions(IndexOptions.DOCS_AND_FREQS)
    
    with open("index.txt", "r") as f:
        line = f.readlines()
        global CNT
        for i in line:
            flag = True
            url, title, time = "", "", ""
            time_sort = 0
            # print(i.split())
            if (len(i.split()) != 1):
                time = " ".join(i.split()[-2:])
                title = " ".join(i.split()[1:-2])
                url = i.split()[0].strip("'")
                time ="".join(filter(str.isdigit, time))
                if len(time) == 12:
                    time += '00'
                time_sort = int(time.replace('-','').replace(':','').replace(" ",''))

            elif (len(i.split()) == 1):
                print("Not crawled")
                flag = False

            if (flag):
                parsed_result = urlparse(url)
                site = parsed_result.netloc
                for i in range(len(site)):
                    if site[i:i+4] == "www.":
                        site = site[i+4:]
                        break
                site = site.replace(".", " ")
                folder_name = valid_filename(url)
                print("adding", folder_name)
                try:
                    with open('keyword.txt','r') as f:
                        keyword = f.read()
                except:
                    keyword = "No key"
                try:
                    folder = os.path.join(root, folder_name)
                    
                    file = open(os.path.join(folder, folder_name+'.txt'), encoding='utf-8')
                    contents = file.read()
                    contents = " ".join(jieba.lcut_for_search(contents))
                    file.close()
                    img_name = []
                    allfiles = os.listdir(os.path.join(root, folder_name))
                    all_files_name = os.listdir(os.path.join(root, folder_name))
                    for k in range(len(allfiles)):
                        allfiles[k]=os.path.splitext(allfiles[k])[1]
                    for k in range(len(allfiles)):
                        if allfiles[k] == '.jpg':
                            img_name.append(all_files_name[k])
                            
                    doc = Document()
                    doc.add(Field("filename", folder_name+'.txt', t1))
                    doc.add(Field("path", folder, t1))
                    doc.add(Field("title", title, t1))
                    doc.add(Field("url", url, t1))
                    doc.add(Field("site", site, t2))
                    if type(time_sort) != int:
                        time_sort = 0
                    doc.add(Field("time_sort", time_sort, t3))
                    doc.add(Field("time", time, t1))
                    doc.add(Field("keyword",keyword,t2))
                    img = ""
                    for pic in img_name:
                        img += pic.replace(".jpg",'') + '|'
                    img_ori = img
                    img = " ".join(jieba.lcut_for_search(img))
                    doc.add(TextField("img_name", img, Field.Store.YES))
                    doc.add(TextField("img", img_ori, Field.Store.YES))
                    CNT += 1
                    if len(contents) > 0:
                        doc.add(Field("contents", contents, t2))
                    else:
                        print("warning: no content in %s" % folder_name+'.txt')
                    writer.addDocument(doc)
                except Exception as e:
                    print("Failed in indexDocs:", e)
```

## 任务三 搜索，排序与网站制作 作者：陈可
## 任务四 作者：朱鑫炜
## 任务五 作者：贾涵
# 最终效果
