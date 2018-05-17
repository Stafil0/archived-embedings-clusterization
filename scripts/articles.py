import urllib.request
import os
import logging
import re
import string
import socket
import requests
import os
import time
import json
from bs4 import BeautifulSoup

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
SAMPLES_DIR = os.path.join(DATA_DIR, 'samples')

regex = re.compile('[^а-яА-Яa-zA-Z]{2,}')
proxies = {
  'http': 'http://79.105.77.141:8080',
  'https': 'http://79.105.77.141:8080',
}

def download_article(url):
  page = requests.get(url, proxies).content
  soup = BeautifulSoup(page,"lxml")
  for link in soup.find_all('a'):
    try:
      path = link.get('href')
      if 'article/n/' in path:
        name = link.find('div', {'class':'title'}).text
        fname = regex.sub(' ',name)[:100]
        pdf = os.path.abspath(os.path.join(SAMPLES_DIR, fname+'.pdf'))
        download = 'https://cyberleninka.ru'+path+'.pdf'
        urllib.request.urlretrieve(download, pdf)
        print('Saved:', pdf)
    except:
      pass

if __name__ == '__main__':
  start = 16
  pages = 12913
  for i in range(start, pages):
    print('Reading %d page of %d (%f%%)' % (i, pages, i/pages))
    download_article('https://cyberleninka.ru/article/c/meditsina-i-zdravoohranenie/'+str(i))