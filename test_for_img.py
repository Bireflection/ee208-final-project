import requests
page = requests.get("http://i2.chinanews.com.cn/simg/cmshd/2022/01/04/95ed19092a294c9aa2af8ea7b2c2810b.jpg")
print(page.content)