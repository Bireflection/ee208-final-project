import re



with open("d:\Desktop\index.txt",'r',encoding='utf-8') as fp:
    texts = fp.readlines()
fptxt = open('d:\Desktop\index1.txt','w',encoding='utf-8')
for text in texts:
    text = re.compile(r"'\t(.*?)\t").search(text).group(1)
    fptxt.write(text+'\n')
fptxt.close()
