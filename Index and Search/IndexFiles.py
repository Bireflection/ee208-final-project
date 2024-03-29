# SJTU EE208

import string
import time
import threading
import lucene
import os
import sys
import jieba
from org.apache.lucene.util import Version
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.index import FieldInfo, IndexWriter, IndexWriterConfig, IndexOptions
from org.apache.lucene.document import Document, Field, FieldType, StringField, TextField, LongPoint, DateTools,StoredField, NumericDocValuesField
from org.apache.lucene.analysis.core import WhitespaceAnalyzer
from org.apache.lucene.analysis.miscellaneous import LimitTokenCountAnalyzer
from org.apache.lucene.search import IndexSearcher
from java.nio.file import Paths
from urllib.parse import urlparse
from datetime import datetime
INDEX_DIR = "IndexFiles.index"
CNT = 0

# from java.io import File

"""
This class is loosely based on the Lucene (java implementation) demo class 
org.apache.lucene.demo.IndexFiles.  It will take a directory as an argument
and will index all of the files in that directory and downward recursively.
It will index on the file path, the file name and the file contents.  The
resulting Lucene index will be placed in the current directory and called
'index'.
"""

def valid_filename(s):
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    s = ''.join(c for c in s if c in valid_chars)
    return s

class Ticker(object):

    def __init__(self):
        self.tick = True

    def run(self):
        while self.tick:
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1.0)


class IndexFiles(object):
    """Usage: python IndexFiles <doc_directory>"""

    def __init__(self, root, storeDir):

        if not os.path.exists(storeDir):
            os.mkdir(storeDir)

        # store = SimpleFSDirectory(File(storeDir).toPath())
        store = SimpleFSDirectory(Paths.get(storeDir))
        analyzer = WhitespaceAnalyzer()
        analyzer = LimitTokenCountAnalyzer(analyzer, 1048576)
        config = IndexWriterConfig(analyzer)
        config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
        writer = IndexWriter(store, config)

        self.indexDocs(root, writer)
        ticker = Ticker()
        print('commit index')
        threading.Thread(target=ticker.run).start()
        writer.commit()
        writer.close()
        ticker.tick = False
        print('done')

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
                    
                    # print(time, title, url)
                    # time.sleep(100)
                elif (len(i.split()) == 1):
                    print("Not crawled")
                    flag = False
                    # return
                    # title = "No accessible"
                    # filename = i.split()[-1]
                    # url = i.split()[0].strip("'")
        # for root, dirnames, filenames in os.walk(root):
            # for filename in filenames:
                # if not filename.endswith('.txt'):
                #     continue
                
                
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
                        ori_content = contents
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
                        # doc.add(Field("filename", folder_name+'.txt', t1))
                        # doc.add(Field("path", folder, t1))
                        # doc.add(Field("title", title, t1))
                        # doc.add(Field("url", url, t1))
                        # doc.add(Field("time_sort", time_sort, t1))
                        # doc.add(Field("time", time, t1))
                        doc.add(Field("filename", folder_name+'.txt', t1))
                        doc.add(Field("path", folder, t1))
                        doc.add(Field("title", title, t1))
                        doc.add(Field("url", url, t1))
                        doc.add(Field("site", site, t2))
                        if type(time_sort) != int:
                            time_sort = 0
                        # print(time_sort)
                        doc.add(Field("time_sort", time_sort, t3))
                        # doc.add(StoredField("time_sort", time_sort))
                        # print(doc.get("time_sort"))
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
                            doc.add(Field("ori_content", ori_content, t1))
                        else:
                            print("warning: no content in %s" % folder_name+'.txt')
                        writer.addDocument(doc)
                    except Exception as e:
                        print("Failed in indexDocs:", e)


if __name__ == '__main__':
    lucene.initVM()  # vmargs=['-Djava.awt.headless=true'])
    print('lucene', lucene.VERSION)
    # import ipdb; ipdb.set_trace()
    start = datetime.now()
    try:
        IndexFiles('html', "index")
        end = datetime.now()
        print(end - start, CNT)
    except Exception as e:
        print("Failed: ", e)
        raise e