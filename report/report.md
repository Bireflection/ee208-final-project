# <center> Lab 15 Final

</center>

<center> 第八组 陈可 贾涵 朱鑫炜 喻智勇
</center>

# 实验环境

本次实验基于Docker当中的`sjtucmic/ee208`镜像。在此基础上使用了原环境当中没有的库，列举如下：

- `requests`
- `pandas`
- `chardet`
- `face_recognition`(依赖库为`cmake`, `dlib`)
- `jieba`
- `sklearn`

# 任务分工

- 陈可：定向采集 2-3 个新闻网站特定类别（本次实验为体育类）的新闻，并进行关键词、图片搜索，时间、相关度排序，网站制作，汇报展示
- 朱鑫炜：基于人脸的新闻搜索，网站制作协助
- 贾涵：相似新闻的自动聚类
- 喻智勇：协助

# 实验流程

## 任务一 爬虫 作者：陈可

### 网站的选择

在选择我们组所需要的网站的时候，我在很多网站当中做过对比，最后选择了网易体育以及中国新闻网的体育频道。选择这两个新闻网站的原因在于，它们的网址都有明确分类，这一点相比于澎湃新闻等网站相比要便于分类。同时，中国新闻网提供了滚动新闻，即将一天内的所有新闻集中在一页上的页面。这样便于爬取，也不需要重新加载。

但是在实际爬虫当中遇到了比预期更多的问题，将在后面的报告中说明。本次的实验源代码全部基于本人的Lab5的代码改动而来。

要注意的是，现在的文件结构发生了改变，原先为`html_netease`的文件夹现在与接下来要提到的`html_chinanews`合并为了`html`文件夹。一部分的代码可能因此而发生变动，这里保留的是未改动的代码（因为不需要再次爬取了）

### 爬虫任务——网易体育

首先是网易体育的爬取。由于爬虫时修改较多，此次任务共使用了三分代码文件。按照使用的时间顺序首先介绍`netease.py`文件。

首先是主程序`working`。首先设定规则为网易体育的两类域名，不符合此规则的网页不予爬取。接着调用`get_page`函数获取页面信息，利用`get_all_links`获取之后需要爬取的网页，并加入队列。最后，存储爬取到的数据。
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

然后是`get_page`函数。`get_page`函数为了防止被系统识别为爬虫，采用了多种header，使用`random`函数选一个header进行爬虫，并且增加响应格式等参数进行爬虫。如果识别到错误返回码（400，403等）则返回空。同时使用`etree`和`beautifulsoup`对于响应进行解析。`test`参数用于读取标题，如果没有标题则继续返回空。利用`xpath`获取正文，时间，并对时间进行去除无用字符的处理。

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

随后处理图片。第一个问题出现，网易新闻当中，有关图片的所在位置多种多样，杂乱无章，无法使用`xpath`。使用`beautifulsoup`获取图片。这里调用的`bs4`里面的`NavigableString`类。我们先找到`f_center`分类，如果得到的元素类型是`NavigableString`，则舍弃不要，然后去找照片的地址。同时，我们也尽力去找到照片的描述。如果能用`alt`则用`alt`，不能去找它附近的文字描述。这是目前的解决方法。由于不同`img`在`des`部分的区别过大，部分图片会出现图片的名字是js函数的情况。但是，由于图片数量多，这种情况所占比例不是很大，对最后结果的影响不算太大。

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

然后是`get_all_links`函数。这与往期Lab的代码一样，用途是识别是相对地址还是绝对地址，如果为相对地址则加上域名。

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

`add_page_to_folder`函数的作用在于将网页存进文件夹里。与往期lab不一样的地方在于，这个函数同时具备把图片下载的能力。使用`requests`库来获取图片，以二进制储存，修改文件名使其合法。

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

最后是主函数,使用了多线程。这里`maxnum`和最后的数目不一致，是我人为中止所造成的（硬盘空间问题）

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

同时介绍两个小的代码文件。首先是`download.py`。顾名思义，由于写`netease.py`的时候没有下载原网页，为了后期使用方便，增加的。只是单纯的请求网页并下载，不在过多阐述。

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

其次是`getkeyword.py`，用于从网页的keyword字段提取关键词。基于之前下载的网页进行操作，使用`beautifulsoup`找到keyword所在位置，有就存下来。

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

以上便是爬取netease的全部代码。

### 爬虫任务——中国新闻网体育

按照爬取新闻年份的不同，分为两份文件：`chinanews_old.py`和`chinanews_new.py`。不同的年份的编码等有特殊处理，且遇到了一些问题，故分为两份代码。

首先从old开始，介绍一下对于中国新闻网滚动网页的思路。

观察可知，滚动新闻从16年到现在依旧保持着同一个结构。所以我们利用这种结构（如下代码所示）产生一下滚动新闻的网页url。在这里，我们要先产生一个日期序列。这里`date_generator`函数利用`pandas`产生一个日期序列，再利用`datetime`库当中的`strfttime`方法规定格式。传入`scroll_news_generator`函数当中，产生url列表。

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

我们访问页面观察，滚动新闻如下图所示。可以看到，每个新闻的前面都会有一个分类。我们找到其中写着体育的新闻，获取对应url,访问即可。因此我们使用如下`get_url_to_crawl`函数，利用`beautifulsoup`找到这些类别标签所对应的`dd_lm`类，如果是体育类，则保存标题和对应的url。

![滚动新闻页面](E:\大学\大二上\电类工程导论（C类）\lab15-Final\report\chinanews_exp.jpg "chinanews滚动新闻页面")

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

下面就是顺着我们所得到的`url`去爬取网站。首先，我们可以在类型为`left-t`的地方找到时间，在`left_zw`找到正文。当然，老页面有所不同，时间在`content_left_time`里面，我也做了判定。

![time_zw](E:\大学\大二上\电类工程导论（C类）\lab15-Final\report\time_zw.jpg "time_zw")

<center> 时间和正文 </center>

随后我们去找图片。可以看到，图片在`text-align:center`里面。我们分析里面的`src`，如果是`//`开头的，则为缺少`https`，如果头部具有`http`，则直接访问即可。而关于图片的名字，如果有`title`类就以其内容为名字，如果没有，认为这张图片没名字。

![chinanews_pic](E:\大学\大二上\电类工程导论（C类）\lab15-Final/report/chinanews_pic.jpg "chinanews_pic")

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

然后就是网页的储存。问题随之出现。在老网页，例如16年的网页，用的是`GB2312`，新网页用的是`utf-8`。为了分析我获取的是什么样子的网页，引入了一个新的库为`chardet`，它能分析出网页的编码。但是，它将`utf-8`认成了`KOI-8`，`gb2312`却可以识别。无奈之下，分为了两个文件。
对于老网页来说，判断其编码，没有编码证明没爬取成功，如果是`gb2312`就将其转为`gb18030`（足够大）然后进行储存，储存方法和网易那边类似，不再展开。

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

然后是`working`函数，调用这些函数。随后，主函数采用了多进程`multiprocessing`库。但是，第一次尝试的时候，电脑内存爆了。查阅资料得知，python在多进程的时候，内存回收会出现问题。随后实验了更多方法（源代码注释部分），无结果。最后又因为后面将新旧网页分开，所以旧网页使用多进程和进程池，但只有三个进程（3年），就不会爆内存了。新网页则是一年一年的爬（只爬了2022年的，硬盘满了）。主函数如下：

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

`chinanews_new.py`和`old`的区别仅在以下函数。首先判断`req`类型，不是字节类型转成字节类型。不再转码。

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

受限于电脑硬盘，在后面将文件统一移到`html`文件夹的时候丢失了几个文件，但问题不大。代码中提到的`index.txt`和`index_chinanews.txt`等类似物都合并到了`index.txt`文件当中。

在网页的爬取中遇到了很多稀奇的事情，例如编码类型，例如多进程内存溢出等等。幸好对于结果的影响不算太大。

## 任务二 建立索引 作者：陈可

爬取完网站之后就是索引。这部分和往期lab一模一样，在此基础上增加了一个类叫做t3，用于储存时间数据。利用`urlparse`返回的数据得到域名，这样便于我搜索的时候进行域名搜索。

对于时间，网易的时间能精确到秒，中国新闻网不行，于是将长度用00补齐。对于一篇文档，可以存很多照片。为了匹配照片，我们将文件夹里所有的图片放进一个字符串里面。这样搜索的时候就可以搜得到。至于找到我们所需的图片，那是搜索时干的事情，后面会提到。

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

### 搜索、排序

这次的搜索主要分为相关度排序和时间排序。在索引的时候，已经预先准备好了用于进行时间排序的字段。因此搜索的时候，直接利用列表的`sort`功能进行排序即可。Lucene自带的`NumericField`测试过程中发生了溢出，所以没有采用。同时，搜索支持根据域名搜索，只需要在搜索的时候加上`site:域名`就可以了。具体的做法和之前的lab一样，利用的是`urlparse`，得到的数据里是有域名的。

这里我们以时间排序为例，相关度排序相比时间排序少了sort的过程。对于网页所需要的高亮字段，不同于我们之前所使用的人工变色，这里我用了Lucene自带的`Highlighter`等相关库，参考链接为`https://blog.csdn.net/lushuaiyin/article/details/84169148`。`Highlighter`依赖于词汇单元流中每个词汇单元的起始和结束位置偏移量来将原始输入文本中的字符片段进行精确定位用于高亮显示。同时，为了让`Highlighter`挑选出最适合的一个或多个片段，要引入打分器`Scorer`。编码则使用了`SimpleHTMLEncoder`。函数如下：

```python
def time_sort(keyword):
    STORE_DIR = "index"
    vm_env.attachCurrentThread()
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()
    command = keyword

    command_dict = parseCommand(command, False)
    command_dict["contents"] = " ".join(jieba.lcut_for_search(command_dict.get("contents")))
    keys = list(command_dict.keys())
    if ("site" in keys):
        command_dict["site"] = command_dict["site"].strip()
        command_dict["site"] = command_dict["site"].replace(".", " ")
    querys = BooleanQuery.Builder()
    for k,v in command_dict.items():
        query = QueryParser(k, analyzer).parse(v)
        querys.add(query, BooleanClause.Occur.MUST)
    scoreDocs = searcher.search(querys.build(), 10000).scoreDocs
    doc_time = []
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        doc_time.append([doc.get("time_sort"), doc, scoreDoc.score])
    doc_time.sort(key=lambda x: x[0], reverse=True)

    RESULT = []
    cnt = 0
    for x in doc_time:
        doc = x[1]
        # highlights 
        site = doc.get("site")
        path = doc.get("path")
        if ("163" in site):
            img_path = '../static/netease.jpg'
        else:
            img_path = '../static/chinanews.png'
        if doc.get("img"):
            img = doc.get('img').split("|")[0]
            img_path = '../static/' + path + '/' +img + '.jpg'
        if keyword not in str(doc.get('contents').replace(" ", "")):
            continue
        formatter = SimpleHTMLFormatter() 
        scorer = QueryTermScorer(querys.build())
        encoder = SimpleHTMLEncoder()
        highlighter = Highlighter(formatter, encoder, scorer)
        fragmenter = SimpleFragmenter(80)
        highlighter.setTextFragmenter(fragmenter)
        doc_dic = {}
        doc_dic.update({'title': doc.get("title")})
        doc_dic.update({'url': doc.get("url")})
        doc_dic.update({'time': doc.get("time")[0:4] + "年" + doc.get("time")[4:6] + "月" + doc.get("time")[6:8] + "日"})
        doc_dic.update({'score': scoreDoc.score})
        doc_dic.update({'contents': doc.get("contents")})
        doc_dic.update({'highlights': highlighter.getBestFragment(analyzer, 'contents', doc.get('contents')).replace(" ", "")})
        # doc_dic.update({'img': img})
        doc_dic.update({'img_path': img_path})

        cnt += 1
        RESULT.append(doc_dic)
    return RESULT, cnt
```

要注意的是，为了配合网页的制作，要以字典返回所需内容。

### 基于文字的图片搜索

利用文字搜索图片的方式是：爬取图片的同时也爬取图片附近的对应描述，当做文件名。建立索引的时候将这些名字拼接成字符串，对这个字符串去查找。最后，在字符串当中找到我所要查询的关键词所对应的那幅图片。为了防止误判，比如输入`的`能够显示图片，从网上找到了百度停用词表`stopwords.txt`用于之后的使用。要是在停用词表里的搜索关键词，不予搜索。

具体函数如下：

```python
def img_search_by_word(keyword):
    STORE_DIR = "index"
    vm_env.attachCurrentThread()
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()
    command = keyword
    command_dict = parseCommand(command, True)
    command_dict["img_name"] = " ".join(jieba.lcut_for_search(command_dict.get("img_name")))
    keys = list(command_dict.keys())
    if ("site" in keys):
        command_dict["site"] = command_dict["site"].strip()
        command_dict["site"] = command_dict["site"].replace(".", " ")
    querys = BooleanQuery.Builder()
    for k,v in command_dict.items():
        query = QueryParser(k, analyzer).parse(v)
        querys.add(query, BooleanClause.Occur.MUST)
    scoreDocs = searcher.search(querys.build(), 2000).scoreDocs
    RESULT = []
    cnt = 0
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        # highlights 
        site = doc.get("site")
        path = doc.get("path")
        stop = stopwords()
        if ("163" in site):
            img_path = '../static/netease.jpg'
        else:
            img_path = '../static/chinanews.png'
        img_list = doc.get("img").split('|')
        for img in img_list:
            search_item = command_dict["img_name"].split()
            for keyword in search_item:
                if keyword in img and keyword not in stop:
                    img_path = '../static/' + path + '/' + img + '.jpg'
                    if keyword not in str(doc.get('contents').replace(" ", "")):
                        continue
                    formatter = SimpleHTMLFormatter() 
                    scorer = QueryTermScorer(querys.build())
                    encoder = SimpleHTMLEncoder()
                    highlighter = Highlighter(formatter, encoder, scorer)
                    fragmenter = SimpleFragmenter(80)
                    highlighter.setTextFragmenter(fragmenter)
                    doc_dic = {}
                    doc_dic.update({'title': doc.get("title")})
                    doc_dic.update({'url': doc.get("url")})
                    doc_dic.update({'time': doc.get("time")[0:4] + "年" + doc.get("time")[4:6] + "月" + doc.get("time")[6:8] + "日"})
                    doc_dic.update({'score': scoreDoc.score})
                    doc_dic.update({'contents': doc.get("contents")})
                    # doc_dic.update({'img': img})
                    doc_dic.update({'img_path': img_path})

                    cnt += 1
                    RESULT.append(doc_dic)
```

### 网页整合

由于一些事件，留给我制作网页的时间很短。因此很多东西比较的粗糙。

侧边栏导航参考的是`https://blog.csdn.net/qq_25503949/article/details/106244548`。我们点击logo图片，对应的标签就会进行内容的平移操作。为了让我们自己写的部分也能应用到这一平移缩放效果，利用继承类实现。

在首页，我们制作了一个滚动播放的图片栏（虽然后面看效果图像是小广告）。利用`@keyframes`，可以创建动画，通过`left`移动图片使得图片动起来。

```html
  @keyframes re {
      0% {
          left: calc(1000px * 0);
      }
      25% {
          left: calc(1000px * -1);
      }
      50% {
          left: calc(1000px * -1);
      }
      50% {
          left: calc(1000px * -2);
      }
      75% {
          left: calc(1000px * -2);
      }
      75% {
          left: calc(1000px * -3);
      }
      100% {
          left: calc(1000px * -3);
      }
      100% {
          left: calc(1000px * -4);
      }
  }
```

然后是flask的跳转。我们在每个页面基本都是有按钮的，通过表单和按钮达到跳转，或者说是呈现结果的目的。

在普通搜索的时候，和lab7的操作一致，利用普通表单上传搜索内容就可以了。但是，在人脸识别的时候，因为是用户上传文件上来，所以使用了表单当中的`enctype="multipart/form-data"`参数，使之能够接受文件。

呈现结果的result类使用了表格，一行当中放四张图片，然后开始下一行。如果一行图片不满，为了美观就不显示。如果发现没有结果可以显示，会以一张标志着错误的图片作为没有图片的代表。

由于时间不够，后期有的数据改的比较匆忙，很多地方直接用的`<br>`换行，而没有动模板类的详细参数，这也是一个遗憾的地方。

所有的模板都在template文件夹中，这里不再引用。

## 任务四 基于人脸的新闻搜索 作者：朱鑫炜

### 选择使用开源库

在人脸识别开始，我们面临两种选择，自己训练深度学习框架，完成人脸识别的模块，但是就我之前lab的经验而言，我们自行训练的效果比较差，最后我选择了开源库`face recognition`，通过测试，这个库效果比较好。

### 人脸识别模块的结构

这个模块可以分为 `encode_img`， `load_img`， `compare_img` 三个部分，依次实现了将数据库中图片文件转化为人脸的特征向量，并完成数据的存储，读取之前存储的数据，和将目标图片与已有数据进行比对。

### 具体代码的编写

具体代码如下

- 实现了找出目录下所有图片文件，以辅助完成对目录下图片的处理
  
  ```python
  def find_all_img(path):
    for path, dirs, files in os.walk(path):
        for file in files:
            if file[-3:] == 'jpg':
                yield((path,file))
  ```

- 实现了对目录的图片进行处理，同时将新闻的标题，还有图片名称（即图片附近的解释文字），图片的路径加入list，最后利用`numpy`库，将数据存储为`.npy`格式，实现图片数据的预处理。
  
  ```python
    def encode_img(img_path, data_path='./data'):
        """
        convert the imgs under the img_path into numpy ndarray.
        then save it in data_path
        """
        # read img and covert it
        title_list = []
        face_list = []
        img_name_list = []
        img_path_list = []
        for i in img_path:
            for path, file in find_all_img(i):
                try:
                    print(os.path.join(path, file))
                    with open(os.path.join(path, path[path.rfind('/')+1:]+'.txt')) as f:
                        title = f.readline()
                    img = fr.load_image_file(os.path.join(path, file))
                    faces = fr.face_encodings(img)
                    if faces:
                        for face in faces:
                            title_list.append(title)
                            face_list.append(face)
                            img_name_list.append(file)
                            img_path_list.append(os.path.join(path, file))
                except:
                    print("ERROR IMG!")
  
        # save file
        np_title_list = np.array(title_list)
        np_face_list = np.array(face_list)
        np_img_name_list = np.array(img_name_list)
        np_img_path_list = np.array(img_path_list)
  
        if not os.path.exists(data_path):
            os.mkdir(data_path)
        np.save(os.path.join(data_path, 'title.npy'), np_title_list)
        np.save(os.path.join(data_path, 'face.npy'), np_face_list)
        np.save(os.path.join(data_path, 'img_name.npy'), np_img_name_list)
        np.save(os.path.join(data_path, 'img_path.npy'), np_img_path_list)
  ```

- 实现了从npy文件中读入数据
  
  ```python
    def load_img(data_path='./data'):
        if not os.path.exists(data_path):
            print('no such path')
            return [], [], []
        np_title_list = np.load(os.path.join(data_path, 'title.npy'))
        np_face_list = np.load(os.path.join(data_path, 'face.npy'))
        np_img_path_list = np.load(os.path.join(data_path, 'img_name.npy'))
        return np_title_list, np_face_list, np_img_path_list
  ```

- 这一部分是具体的比较，方式是比对目标的特征向量和数据库中的特征向量相似度，然后返回大于阈值的结果，从中默认挑选前10名。如果没有搜到，会输出空列表
  
  ```python
    def compare_img(np_target, np_title_list, np_face_list, np_img_path_list, max_num=10):
        np_truth_list = fr.compare_faces(np_face_list, np_target)
        indices = np.where(np_truth_list)
        img_list = []
        if indices:
            for i in range(min(max_num, len(indices))):
                title = np_title_list[indices[i]]
                img_path = np_img_path_list[indices[i]]
                img_list.append({"title":title, "img_path":img_path})
        return img_list
  ```

## 任务五 基于人脸的新闻搜索 作者：贾涵

我们获取到新闻标题以后，要将其进行聚类分析。首先我们要提取出来相应的标题文本内容，在此我们利用split分割函数将index文档中的每一条消息按照空格进行分割，取每一条的中间部分，写入新的文档index.txt之中，即可完成文本的提取，代码如下：

```python
with open('index.txt','r',encoding='utf-8')as fp:
    texts = fp.readlines()
fptxt = open('index1.txt','w',encoding='utf-8')
for text in texts:
    text = re.compile(r"'\t(.*?)\t").search(text).group(1)
    fptxt.write(text+'\n')
fptxt.close()
```

在提取到新闻标题以后，我们开始进行jieba分词，统计关键词，以及聚类和相关度的分析。此处用到了TF-IDF算法和K-means聚类均值算法进行分析。外置库jieba，pandas，sklearn，cmake库在此用到进行分词和聚类。

```python
def tokenize(text_list, stop):
    texts = []
    tokenized_texts = []
    for text in text_list:
        cut = [each for each in jieba.cut(text) if each not in stop and not re.match(r'\d+', each)]
        if cut:
            texts.append(text)
            tokenized_texts.append(cut)
    return texts, tokenized_texts

def get_best_n_topics(n_candidates, data):
    sse = []
    for n in n_candidates:
        print(f"Kmeans with {n} centers")
        kmeans = KMeans(n_clusters=n, n_init=5)
        kmeans.fit(X=data)
        sse.append(kmeans.inertia_)
    return sse

def fit_kmeans(n, data):
    kmeans = KMeans(n_clusters=n, n_init=5, random_state=10)
    pred = kmeans.fit_transform(X=data)
    return kmeans, pred


def get_key_words(text_vec, vectorizer):
    idx_to_word = {k: v for v, k in vectorizer.vocabulary_.items()}
    key_index = np.array(np.argmax(text_vec, axis=-1)).squeeze()
    return [idx_to_word[k] for k in key_index]

if __name__ == '__main__':
    contents = [each.strip() for each in open("./index1.txt", encoding="utf-8").readlines()]
    stopwords = set(each.strip() for each in open("./stopwords.txt", encoding="utf-8").readlines())
    stopwords.add(" ")

    texts, tokenized_texts = tokenize(contents, stopwords)

    inputs = [" ".join(each) for each in tokenized_texts]
    vectorizer = TfidfVectorizer(max_features=1000)
    text_vec = vectorizer.fit_transform(inputs)


    # sse = get_best_n_topics(list(range(1, 11)), text_vec)
    # plt.plot(sse)
    # plt.show()

    n = 7
    kmeans, pred = fit_kmeans(7, text_vec)
    pred_cls = np.argmin(pred, axis=-1)
    key_words = get_key_words(text_vec, vectorizer)
    res = pd.DataFrame({"标题": texts, "关键词": key_words, "类别": pred_cls})
    res.to_csv("分类结果.csv", index=False)
```

生成的结果以csv的形式写出，分别为标题，标题中所包含的关键词以及所属类，从而可以在为用户推荐时做到相关新闻的推荐；

# 最终效果

详情见答辩PPT和演示视频

# 实验总结

本次实验的过程比较的曲折，但在最后的努力下，我们圆满实现了所有包括optimal的实验目标。一个遗憾在于网站的美化没有做的更好，其他的搜索结果我们认为已经很完善了。

一个小的提议：因为在实验过程当中，问题出的比较多的地方就是Lucene的应用.因为pylucene在资料查找上比较复杂，而且出现问题需要阅读java语法，比较麻烦。感觉基于Lucene的Elasticsearch可能有更好的对于python的适应度。