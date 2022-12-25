import os
from datetime import datetime
import queue
import re
import string
import threading
import time
import random
import urllib.error
import urllib.parse
import urllib.request
import requests
import pandas as pd
from bs4 import BeautifulSoup
from lxml import etree
from bs4.element import NavigableString 

def date_generator():
    date = [datetime.strftime(x,'%Y%m%d') for x in list(pd.date_range(start="20150101", end="20221225"))]
    return date
def scroll_news_generator():
    for i in range():
        pass
if __name__ == '__main__':
    print(date_generator())
    