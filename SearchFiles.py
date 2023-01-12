# SJTU EE208

import lucene
from org.apache.lucene import search
from org.apache.lucene.util import Version
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.queryparser.classic import QueryParser
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.analysis.cjk import CJKAnalyzer;
from org.apache.lucene.search import Sort
from org.apache.lucene.search import SortField
from java.io import File
from org.apache.lucene.search import BooleanQuery
from org.apache.lucene.search import BooleanClause
import jieba
INDEX_DIR = "IndexFiles.index"


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

def run(searcher, analyzer):
    is_time_sort = False
    is_img_search = False
    print()
    print ("Hit enter with no input to quit.")
    command = input("Query:")
    if command == '':
        return
    print()
    type_of_search = input("Select search type: 1 for default 2 for time sort 3 for img search:")
    if type_of_search == "2":
        is_time_sort = True
    if type_of_search == "3":
        is_img_search = True
    print()
    print ("Searching for:", command)
    
    command_dict = parseCommand(command, is_img_search)
    if is_img_search:
        command_dict["img_name"] = " ".join(jieba.lcut_for_search(command_dict.get("img_name")))
    else:
        command_dict["contents"] = " ".join(jieba.lcut_for_search(command_dict.get("contents")))
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
    if (is_time_sort):
        doc_time = []
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
            doc_time.append([doc.get("time_sort"), doc, scoreDoc.score])
            
        mergesort(doc_time, 0, len(doc_time)-1)
        for doc in doc_time:    
            print('title:', doc[1].get("title"))
            print('url:', doc[1].get("url"))
            print('time_sort:', doc[1].get("time"))
            print('score:',doc[2]) 
            cnt += 1    

    elif (is_img_search):
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
    else:
        for scoreDoc in scoreDocs:
            doc = searcher.doc(scoreDoc.doc)
            print('title:', doc.get("title"))
            print('url:', doc.get("url"))
            print('time:', doc.get("time"))
            print('score:',scoreDoc.score)
            cnt += 1
            
    print("%s total matching documents." % cnt)
        
if __name__ == '__main__':
    STORE_DIR = "index"
    lucene.initVM(vmargs=['-Djava.awt.headless=true'])
    print ('lucene', lucene.VERSION)
    # base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    directory = SimpleFSDirectory(File(STORE_DIR).toPath())
    searcher = IndexSearcher(DirectoryReader.open(directory))
    analyzer = WhitespaceAnalyzer()#Version.LUCENE_CURRENT)
    run(searcher, analyzer)
    del searcher
    