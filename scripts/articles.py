import urllib.request
import sys
import os
import re
import string
import requests
import time
import random
import colorama
import socket
import socks
import asyncio, time, concurrent
from termcolor import colored
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from proxybroker import Broker
from multiprocessing import Process

CONFIG_FILE = '_config.xml'

colorama.init()
ua = UserAgent()
regex = re.compile('[^а-яА-Яa-zA-Z]+')
proxy_list = []
proxy_excepted = []

def save_config(exctype, value, traceback):
  if exctype == KeyboardInterrupt:
    with open(CONFIG_FILE, 'rb') as file:
      print(value)
      soup = BeautifulSoup(file, 'html.parser')
      articles = soup.find('config', {'name':'articles'})
      articles.find('start').string.replace_with(str(START))
    with open(CONFIG_FILE, 'wb') as file:
      file.write(soup.prettify('utf-8', 'minimal'))
  else:
    sys.__excepthook__(exctype, value, traceback)
sys.excepthook = save_config

def load_config(path):
  global SAMPLES_DIR
  global PAGES
  global START
  global PROXY

  with open(path, 'rb') as file:
    content = file.read()
  soup = BeautifulSoup(content, 'lxml')
  all = soup.find('all')
  articles = soup.find('config', {'name':'articles'})
  SAMPLES_DIR = all.find('samples').text.strip()
  PAGES = int(articles.find('pages').text)
  START = int(articles.find('start').text)
  PROXY = bool(articles.find('proxy').text)

def timeout(time, func, params=()):
  print(colored('>> Start func', 'red'), func, colored('with timeout:','red'), time)
  action = Process(target=func(*params))
  action.start()
  action.join(timeout=time)
  action.terminate()
  print(colored('>> Done!','red'))
  
def get_proxies(count=20, timeout=10):
  exceptions = 0
  print('Loading proxy list')
  while True:
	if exceptions > 10:
	  sleep = 30
	  print(colored('Too many exceptions while getting proxy list. Sleep for:', 'red'), sleep)
	  time.sleep(sleep)
	  break
	try:
	  proxy_list.clear()
	  proxies = asyncio.Queue()
	  broker = Broker(proxies)
	  tasks = asyncio.gather(broker.find(types=['SOCKS5'], limit=count), save_proxy(proxies))
	  loop = asyncio.get_event_loop()
	  loop.run_until_complete(asyncio.wait_for(tasks, timeout))
	  print('Loaded proxies:', colored(len(proxy_list), 'cyan'))
	except Exception as e:
	  print(colored('Error while getting proxy list:', 'red'), e)
	  exceptions += 1
	  broker.stop()
	  tasks.cancel()
	  continue
    
async def save_proxy(proxies):
  while True:
    proxy = await proxies.get()
    if proxy is None: break
    ip = (proxy.host, proxy.port)
    if proxy.avg_resp_time < 0.5 and ip not in proxy_excepted:
      proxy_list.append(ip)

def change_proxy(remove=True, time=30):
  global PROXY
  ok_proxy = False
  empty_count = 0
  current_socks = socks.get_default_proxy()

  while not ok_proxy:
    if remove and current_socks is not None:
      current = (current_socks[1], current_socks[2])
      proxy_excepted.append(current)
      if current in proxy_list: proxy_list.remove(current) 
    if len(proxy_list) < 2:
      timeout(60, get_proxies)
      empty_count += 1
      continue
    if empty_count > 2:
      print(colored('No proxy avaliable. Switch to normal mode.', 'cyan'))
      socks.set_default_proxy()
      socket.socket = socks.socksocket
      PROXY = False
      break
    index = random.randint(0, len(proxy_list)-1)
    proxy = proxy_list[index]
    print(colored('Trying proxy:', 'magenta'), '%s:%d' % (proxy[0], proxy[1]))
    try: 
      socks.set_default_proxy(socks.SOCKS5, proxy[0], proxy[1])
      socket.socket = socks.socksocket     
      iprequest = requests.get('http://checkip.amazonaws.com/', timeout=0.5)
      ok_proxy = True
      print(colored('New IP:', 'green'), iprequest.text.strip())
    except: 
      proxy_excepted.append(proxy)
      proxy_list.remove(proxy) 
      pass   

def download(url, path, pause=0):
  global PROXY
  retrys = 0
  while True:
    if PROXY:
      try:
        request = requests.get(url, headers={'User-Agent': ua.chrome}, timeout=1)
        if request.content.startswith(b'<!DOCTYPE html'):
          retrys += 1
          print('Got capcha on:', colored(url, 'grey'))
          change_proxy()
          continue
        break
      except Exception as e:
        retrys += 1
        print('Retry %d time:'%retrys, colored(url, 'grey'))
        if retrys % 3 == 0: change_proxy()
        continue
    else:
      if pause > 0: time.sleep(pause)
      request = requests.get(url, headers={'User-Agent': ua.chrome}, timeout=1)
      if request.content.startswith(b'<!DOCTYPE html'): 
        print(colored('Banned on main IP. Switch to proxy mode.', 'cyan'))
        PROXY = True
        continue
      break
  with open(path, 'wb') as file:
    file.write(request.content)

def download_articles(htmlpage):
  count = 0
  soup = BeautifulSoup(htmlpage, 'lxml')
  for link in soup.find_all('a'):
    path = link.get('href')
    if 'article/n/' in path:
      name = link.find('div', {'class':'title'}).text
      if name.lower().startswith('таблица'):
        continue
      fname = regex.sub(' ',name)[:150]+'.pdf'
      pdf = os.path.abspath(os.path.join(SAMPLES_DIR, fname))
      url = 'https://cyberleninka.ru'+path+'.pdf'
      download(url, pdf, 10)
      print('Save:', colored(fname, 'grey'))
      count += 1
  return count

def brutforce_articles():
  global START

  print(colored('Using proxy:', 'cyan'), PROXY)
  if PROXY:
    timeout(60, get_proxies)
    change_proxy()

  print(colored('Save path:', 'red'), SAMPLES_DIR)
  for i in range(START, PAGES):
    START = i
    link = 'https://cyberleninka.ru/article/c/meditsina-i-zdravoohranenie/'+str(i)
    print(colored('Downloaded:', 'yellow'), len(os.listdir(SAMPLES_DIR)))
    print(colored('Reading %d page of %d' % (i, PAGES), 'blue'), '(%f%%)' % (i/PAGES))
    while True:
      try: responce = requests.get(link, headers={'User-Agent': UserAgent().chrome})
      except:
        print('Articles page retry:', colored(link, 'grey'))
        if PROXY: change_proxy()
        continue
      break
    download_articles(responce.content)    

if __name__ == '__main__':
  load_config(CONFIG_FILE)
  brutforce_articles()