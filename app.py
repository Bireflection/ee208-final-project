# SJTU EE208
from pickle import FALSE
import sys, os, lucene
import jieba, random, time

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

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

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
def parseCommand(command):
    allowed_opt = ['site', 'time_sort']
    command_dict = {}
    opt = 'contents'
    for i in command.split(' '):
        if ':' in i:
            print(opt)
            opt, value = i.split(':')[:2]
            opt = opt.lower()
            if opt in allowed_opt and value != '':
                command_dict[opt] = command_dict.get(opt, '') + ' ' + value
        else:
            command_dict[opt] = command_dict.get(opt, '') + ' ' + i
    return command_dict

@app.route('/')
def root():
    if request.method == "POST":
        keyword = request.form['keyword']
        return redirect(url_for('result', keyword=keyword))
    return render_template("root.html")

@app.route('/result', methods=['POST', 'GET'])
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
    
    is_time_sort = False
    command_dict = parseCommand(command)
    command_dict["contents"] = " ".join(jieba.lcut_for_search(command_dict.get("contents")))
    keys = list(command_dict.keys())

    if ("site" in keys):
        command_dict["site"] = command_dict["site"].strip()
        command_dict["site"] = command_dict["site"].replace(".", " ")
    if ("time_sort" in keys):
        is_time_sort = True
    querys = BooleanQuery.Builder()
    for k,v in command_dict.items():
        if (k == "time_sort"):
            continue
        else:
            query = QueryParser(k, analyzer).parse(v)
            querys.add(query, BooleanClause.Occur.MUST)
    scoreDocs = searcher.search(querys.build(), 50).scoreDocs
    RESULT = []
    empty = False
    if (is_time_sort):
        doc_time = []
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
            doc_time.append([doc.get("time_sort"), doc, scoreDoc.score])
            
        mergesort(doc_time, 0, len(doc_time)-1)
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
    else:
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
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
    
    # empty = False
    # for i,scoreDoc in enumerate(scoreDocs):
    #     doc = searcher.doc(scoreDoc.doc)
    #     res = {}
    #     res['title'] = doc.get("title")
    #     res['url'] = doc.get("url")
    #     words = doc.get("contents").split()
    #     content = "".join(words)
    #     # res["test"] = content
    #     res["key"] = words
    #     res['add'] = ""
    #     res['left'] = ""
    #     res['right'] = ""
        # if content.find(keyword) >= 0:
        #     index = content.find(keyword)
        #     if index < 20:
        #         res['left'] = "".join(content[0:index].strip().lstrip("，。；-+=【】、‘’?,.？"))
        #     else:
        #         res['left'] = "".join(content[index - 20: index].strip().lstrip("，。；-+=【】、‘’?,.？"))
        #     if len(content) - index < 20:
        #         res['right'] = "".join(content[index+len(keyword):len(content) -1].strip().rstrip("，。；-+=【】、‘’?,.？"))
        #     else:
        #         res['right'] = "".join(content[index+len(keyword):index+len(keyword)+20].strip().rstrip("，。；-+=【】、‘’?,.？"))
        # else:
        #     length = len(content)
        #     ind = random.randint(0, length - 50)
        #     if length < 50:
        #         res["key"] = " ".join(jieba.cut(command_dict.get("contents"), cut_all=False))
        #         res['add'] = " " + content
        #     else:
        #         res["key"] = " ".join(jieba.cut(command_dict.get("contents"), cut_all=False))
        #         res['add'] = " " + content[ind:ind+50]
        
    if len(RESULT) == 0:
        empty = True;
    return render_template("result.html", keyword = keyword, RESULT = RESULT, empty = empty)



if __name__ == '__main__':
    vm_env = lucene.initVM()
    app.run(debug=True, port=8080)
