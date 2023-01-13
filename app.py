# SJTU EE208
from pickle import FALSE
import sys, os, lucene
import jieba, random, time
import face_recognition.api as fr
import numpy as np

from java.io import File
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.util import Version
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import BooleanClause

INDEX_DIR = "IndexFiles.index"

from flask import Flask, redirect, render_template, request, url_for, flash

app = Flask(__name__,static_url_path='/static')

def find_all_img(path):
    for path, dirs, files in os.walk(path):
        for file in files:
            if file[-3:] == 'jpg':
                yield((path,file))

def encode_img(img_path, data_path='./data'):
    """
    convert the imgs under the img_path into numpy ndarray.
    then save it in data_path
    """
    # read img and covert it
    title_list = []
    face_list = []
    img_name_list = []
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
            except:
                print("ERROR IMG!")
    
    # save file
    np_title_list = np.array(title_list)
    np_face_list = np.array(face_list)
    np_img_name_list = np.array(img_name_list)
    if not os.path.exists(data_path):
        os.mkdir(data_path)
    np.save(os.path.join(data_path, 'title.npy'), np_title_list)
    np.save(os.path.join(data_path, 'face.npy'), np_face_list)
    np.save(os.path.join(data_path, 'img_name.npy'), np_img_name_list)
    
def load_img(data_path='./data'):
    if not os.path.exists(data_path):
        print('no such path')
        return [],[],[]
    np_title_list = np.load(os.path.join(data_path, 'title.npy'))
    np_face_list = np.load(os.path.join(data_path, 'face.npy'))
    np_img_name_list = np.load(os.path.join(data_path, 'img_name.npy'))
    return np_title_list, np_face_list, np_img_name_list

def compare_img(np_target, np_title_list, np_face_list, np_img_name_list, max_num=10):
    ans = []
    np_truth_list = fr.compare_faces(np_face_list, np_target)
    indices = np.where(np_truth_list)
    if indices:
        for i in range(min(max_num, len(indices))):
            title = np_title_list[indices[i]]
            img_name = np_img_name_list[indices[i]]
            ans.append([title, img_name])
    return ans
        
def merge(a, low, mid, high):
    tmp=[]
    for i in range(high-low+1):
        tmp.append([0, 0])
    i = low
    j = mid+1
    k = 0
    while(i <= mid and j <= high):
        if (a[i][0] < a[j][0]):
            tmp[k] = a[j]
            j += 1
        else:
            tmp[k] = a[i]
            i += 1
        k += 1
    while(i <= mid):
        tmp[k] = a[i]
        i+=1
        k+=1
    while(j <= high):
        tmp[k] = a[j]
        j+=1
        k+=1
    for x in range(0, high-low+1):
        a[x+low] = tmp[x]

def mergesort(a, low, high):
    if low >= high:
        return
    mid = int((low + high)/2)
    mergesort(a, low, mid)
    mergesort(a, mid+1, high)
    merge(a, low, mid, high)
    
# 对搜索的网站进行限制
def parseCommand(command, img):
    if (img):
        opt = 'img_name'
    else:
        opt = 'contents'
    allowed_opt = ['site']
    command_dict = {}
    
    for i in command.split(' '):
        if ':' in i:
            print(opt)
            opt, value = i.split(':')[:2]
            opt = opt.lower()
            if opt in allowed_opt and value != '':
                command_dict[opt] = command_dict.get(opt, '') + ' ' + value
        else:
            command_dict[opt] = (command_dict.get(opt, '') + ' ' + i).strip()
            
    return command_dict

def stopwords():
    with open('stopwords.txt', 'r') as f:
        stopwords = f.readlines()
    for i in range(len(stopwords)):
        stopwords[i] = stopwords[i].rstrip('\n')
    return stopwords

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
    scoreDocs = searcher.search(querys.build(), 100).scoreDocs
    doc_time = []
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        doc_time.append([doc.get("time_sort"), doc, scoreDoc.score])
    mergesort(doc_time, 0, len(doc_time)-1)
    return doc_time

def img_search_by_word(keyword):
    STORE_DIR = "index"
    vm_env.attachCurrentThread()
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()
    command = keyword
    command_dict = parseCommand(command,True)
    command_dict["img_name"] = " ".join(jieba.lcut_for_search(command_dict.get("img_name")))
    keys = list(command_dict.keys())
    if ("site" in keys):
        command_dict["site"] = command_dict["site"].strip()
        command_dict["site"] = command_dict["site"].replace(".", " ")
    querys = BooleanQuery.Builder()
    for k,v in command_dict.items():
        query = QueryParser(k, analyzer).parse(v)
        querys.add(query, BooleanClause.Occur.MUST)
    scoreDocs = searcher.search(querys.build(), 2).scoreDocs
    cnt = 0
    stop = stopwords()
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
        img_list = doc.get("img").split('|')
        for img in img_list:
            search_item = command_dict["img_name"].split()
            for keyword in search_item:
                if keyword in img and keyword not in stop:
                    print('title:', doc.get("title"))
                    print('url:', doc.get("url"))
                    print('time:', doc.get("time"))
                    print('score:',scoreDoc.score)
                    print('img:', img +'.jpg')
                    cnt += 1
                    
def img_search_by_pic(target):
    # encode_img(img_path=['./html'])
    target = fr.load_image_file(target)
    target = fr.face_encodings(target)
    np_title_list, np_face_list, np_img_name_list = load_img()
    return compare_img(target, np_title_list, np_face_list, np_img_name_list, 20)

def relevence_sort(keyword):
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
    scoreDocs = searcher.search(querys.build(), 100).scoreDocs
    RESULT = []
    cnt = 0
    for scoreDoc in scoreDocs:
        doc = searcher.doc(scoreDoc.doc)
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
        
        
        doc_dic = {}
        doc_dic.update({'title': doc.get("title")})
        doc_dic.update({'url': doc.get("url")})
        doc_dic.update({'time': doc.get("time")})
        doc_dic.update({'score': scoreDoc.score})
        doc_dic.update({'contents': doc.get("contents")})
        # doc_dic.update({'img': img})
        doc_dic.update({'img_path': img_path})
        
        cnt += 1
        RESULT.append(doc_dic)
    return RESULT, cnt
def recommend():
    pass
# @app.route('/')
# def root():
#     if request.method == "POST":
#         keyword = request.form['keyword']
#         return redirect(url_for('result', keyword=keyword))
#     return render_template("root.html")
    
@app.route('/',methods=['GET', 'POST'])
def begin():
    pic_list = list(find_all_img('./static/home'))
    all_pic = []
    for i in pic_list:
        url = "." + i[0] + "/" + i[1]
        all_pic.append({"img": url})
    pictures1 = all_pic
    pictures2 = all_pic
    pictures3 = all_pic
    return render_template("Home.html", pictures1 = pictures1, pictures2 = pictures2, pictures3 = pictures3)

Search = ""
@app.route('/search',methods=["GET","POST"])
def Search():  # put application's code here
    if request.method == "GET":
         return render_template('Search.html')
    S = request.form.get("Search")
    global Search
    if(S):
        Search=S
    is_img_search = False
    is_time_sort = False
    is_relevence_sort = True
    relevence = request.form.get("相关度排序")
    time = request.form.get("时间排序")
    img = request.form.get("搜索图片")
    print(relevence,time)
    if (relevence == "相关度排序"):
        items, totalnum = relevence_sort(Search)
    elif (time):
        s[1] = Search
        items = doFilter(s)["hits"]["hits"]
        totalnum = int(doFilter(s)['hits']['total']['value'])
    elif (img):
        s[2] = Search
        items = doFilter(s)["hits"]["hits"]
        totalnum = int(doFilter(s)['hits']['total']['value'])
    else:
        items, totalnum = relevence_sort(Search)
    return render_template("Search_result.html", items=items, nums=totalnum)

@app.route('/result_time_sort', methods=['POST', 'GET'])
def result():
    STORE_DIR = "index"
    # 输入keyword
    keyword = request.args.get('keyword')
    # 不输入情况
    if(keyword == ""):
        empty = True
        return render_template("result.html", empty = empty)
    # 建立搜索
    vm_env.attachCurrentThread()
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()
    command = keyword
 
    for doc in doc_time:    
        res = {}
        res['title'] = doc.get("title")
        res['url'] = doc.get("url")
        
        words = doc.get("contents").split()
        content = "".join(words)
        res["key"] = content
        res['add'] = ""
        res['left'] = ""
        res['right'] = ""
        RESULT.append(res)
    # else:
    #     for scoreDoc in scoreDocs:
    #         doc = searcher.doc(scoreDoc.doc)
    #         res = {}
    #         res['title'] = doc.get("title")
    #         res['url'] = doc.get("url")
    #         words = doc.get("contents").split()
    #         content = "".join(words)
    #         res["key"] = content
    #         res['add'] = ""
    #         res['left'] = ""
    #         res['right'] = ""
    #         RESULT.append(res)
    
    # # empty = False
    # # for i,scoreDoc in enumerate(scoreDocs):
    # #     doc = searcher.doc(scoreDoc.doc)
    # #     res = {}
    # #     res['title'] = doc.get("title")
    # #     res['url'] = doc.get("url")
    # #     words = doc.get("contents").split()
    # #     content = "".join(words)
    # #     # res["test"] = content
    # #     res["key"] = words
    # #     res['add'] = ""
    # #     res['left'] = ""
    # #     res['right'] = ""
    #     # if content.find(keyword) >= 0:
    #     #     index = content.find(keyword)
    #     #     if index < 20:
    #     #         res['left'] = "".join(content[0:index].strip().lstrip("，。；-+=【】、‘’?,.？"))
    #     #     else:
    #     #         res['left'] = "".join(content[index - 20: index].strip().lstrip("，。；-+=【】、‘’?,.？"))
    #     #     if len(content) - index < 20:
    #     #         res['right'] = "".join(content[index+len(keyword):len(content) -1].strip().rstrip("，。；-+=【】、‘’?,.？"))
    #     #     else:
    #     #         res['right'] = "".join(content[index+len(keyword):index+len(keyword)+20].strip().rstrip("，。；-+=【】、‘’?,.？"))
    #     # else:
    #     #     length = len(content)
    #     #     ind = random.randint(0, length - 50)
    #     #     if length < 50:
    #     #         res["key"] = " ".join(jieba.cut(command_dict.get("contents"), cut_all=False))
    #     #         res['add'] = " " + content
    #     #     else:
    #     #         res["key"] = " ".join(jieba.cut(command_dict.get("contents"), cut_all=False))
    #     #         res['add'] = " " + content[ind:ind+50]
        
    # if len(RESULT) == 0:
    #     empty = True;
    return render_template("result.html", keyword = keyword, RESULT = RESULT, empty = empty)



if __name__ == '__main__':
    vm_env = lucene.initVM()
    app.run(debug=True, port=8080)
