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