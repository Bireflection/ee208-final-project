import os ,time
from bs4 import BeautifulSoup
for (root, dirs, files) in os.walk('html_netease'):
    if root != 'html_netease':
        try:
            with open(os.path.join(root, 'source.html'), 'r') as f:
                a = f.read()
                soup = BeautifulSoup(a,features="html.parser")
                tag = soup.find('meta',{'name' : 'keywords'})
                # print(soup.head.meta['content'])
                # print(tag['content'])
                # print(soup, os.path.join(root))
                # time.sleep(5)
                with open(os.path.join(root, 'keyword.txt'), 'w') as g:
                    if tag != None:
                        g.write(tag['content'])
                    else:
                        g.write("No keyword")
                # time.sleep(100)
        except:
            continue
    # print(root)