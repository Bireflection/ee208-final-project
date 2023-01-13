# SJTU EE208
from pickle import FALSE
import sys, os, lucene
import jieba, random, time
import face_recognition.api as fr
import numpy as np
from Face_Recognition import face
from werkzeug.utils import secure_filename
from Face_Recognition import face
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
from org.apache.lucene.search.highlight import Highlighter, QueryTermScorer,SimpleFragmenter,SimpleHTMLEncoder,SimpleHTMLFormatter
INDEX_DIR = "IndexFiles.index"

from flask import Flask, redirect, render_template, request, url_for, flash

app = Flask(__name__,static_url_path='/static')
app.config['UPLOAD_FOLDER'] = '/upload'

def parseCommand(command, img):
    if (img):
        opt = 'img_name'
    else:
        opt = 'contents'
    allowed_opt = ['site']
    command_dict = {}
    
    for i in command.split(' '):
        if ':' in i:
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

        

    return RESULT, cnt
                    
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
    scoreDocs = searcher.search(querys.build(), 2000).scoreDocs
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
        if keyword not in str(doc.get('contents').replace(" ", "")):
            continue
        formatter = SimpleHTMLFormatter() 
        scorer = QueryTermScorer(querys.build())
        encoder = SimpleHTMLEncoder()
        highlighter = Highlighter(formatter, encoder, scorer)
        fragmenter = SimpleFragmenter(80)
        highlighter.setTextFragmenter(fragmenter)
        if keyword not in str(doc.get('contents').replace(" ", "")):
            continue
        doc_dic = {}
        # if (not doc.get('contents')):
        #     continue
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

def recommend():
    pass

@app.route('/',methods=['GET', 'POST'])
def begin():
    pic_list = list(face.find_all_img('./static/home'))
    all_pic = []
    for i in pic_list:
        url = "." + i[0] + "/" + i[1]
        all_pic.append({"img": url})
    pictures = all_pic
    return render_template("Home.html", pictures = pictures)

keywords = ""
@app.route('/search',methods=["GET","POST"])
def search():  # put application's code here
    if request.method == "GET":
         return render_template('Search.html')
    S = request.form.get("Search")
    global keywords
    if(S):
        keywords=S
    relevence = request.form.get("相关度排序")
    time = request.form.get("时间排序")
    img = request.form.get("搜索图片")
    if (relevence == "相关度排序"):
        items, totalnum = relevence_sort(keywords)
    elif (time == "时间排序"):
        items, totalnum = time_sort(keywords)
    elif (img == "搜索图片"):
        items, totalnum = (keywords)
    else:
        items, totalnum = relevence_sort(keywords)
    return render_template("Search_result.html", items=items, nums=totalnum)

photo = ""
@app.route('/search_pic_word',methods=["GET","POST"])
def search_pic_by_word():  # put application's code here
    if request.method == "GET":
         return render_template('Search.html')
    S = request.form.get("Search")
    global photo
    if(S):
        photo=S
    items, totalnum = img_search_by_word(photo)
    return render_template("Search_photo_word_result.html", items=items, nums=totalnum)

FILENAME = ""
@app.route('/face',methods=["GET","POST"])
def upload():  # put application's code here
    global FILENAME
    illegal = False
    if request.method == "POST":
        f = request.files['file']
        if f.filename[-3:] == 'jpg':
            f.save("./upload/" + secure_filename(f.filename))
            FILENAME = secure_filename(f.filename)
            return redirect(url_for('face_result'))
        else:
            illegal = True
            return render_template('Face.html', illegal=illegal)
    else:
        return render_template('Face.html', illegal=illegal)
    
@app.route('/face_result',methods=["GET","POST"])
def face_result():
    target = "./upload/" + FILENAME
    print(target)
    
    target_load = fr.load_image_file(target)
    target_load = fr.face_encodings(target_load)
    np_title_list, np_face_list, np_img_path_list = face.load_img()
    faces = face.compare_img(target_load, np_title_list, np_face_list, np_img_path_list, 200)
    print(faces)

    with open("index.txt", "r") as f:
        lines = f.readlines()
        for i in faces:
            
            for line in lines:   
                if (i.get('title') in line):
                    url = line.split()[0].strip("'")
                    i.update({"url": url})
    totalnum = len(faces)
    os.remove(target)
    return render_template("Face_Rc.html", items=faces, nums=totalnum)

@app.route('/class',methods=["GET","POST"])
def classify():
    pass
if __name__ == '__main__':
    vm_env = lucene.initVM()
    app.run(debug=True, port=8080)
