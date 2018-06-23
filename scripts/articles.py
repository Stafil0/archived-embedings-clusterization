import sys, os
import re, string
import requests, urllib.request
import colorama
import socket, socks
import asyncio, aiohttp, time, concurrent, random
from termcolor import colored
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from proxybroker import Broker

CONFIG_FILE = '_config.xml'

colorama.init()
ua = UserAgent()
regex = re.compile('[^а-яА-Яa-zA-Z]+')
default_socket = socket.socket
proxy_list = []
proxy_excepted = []
current_proxy = ()

def save_start2config(start_pos):
  with open(CONFIG_FILE, 'rb') as file:
    soup = BeautifulSoup(file, 'html.parser')
    articles = soup.find('config', {'name':'articles'})
    articles.find('start').string.replace_with(str(start_pos))
  with open(CONFIG_FILE, 'wb') as file:
    file.write(soup.prettify('utf-8', 'minimal'))

def load_config(path):
  global SAMPLES_DIR
  global PAGES
  global START
  global PROXY
  global COUNT

  with open(path, 'rb') as file:
    content = file.read()
  soup = BeautifulSoup(content, 'lxml')
  all = soup.find('all')
  articles = soup.find('config', {'name':'articles'})
  SAMPLES_DIR = all.find('samples').text.strip()
  PAGES = int(articles.find('pages').text)
  START = int(articles.find('start').text)
  COUNT = int(articles.find('count').text)
  PROXY = articles.find('proxy').text.strip() == 'True'
  
def get_proxies(timeout=20, broker_timeout=7, max_conn=150, max_tries=3, limit=40):
  exceptions = 0
  print('Loading proxy list')
  try:
    proxy_list.clear()
    setup_proxy(reset=True)
    proxies = asyncio.Queue()
    broker = Broker(proxies, timeout=broker_timeout, max_conn=max_conn, max_tries=max_tries)
    tasks = asyncio.gather(broker.find(types=['SOCKS5'], limit=limit), save_proxy(proxies))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.wait_for(tasks, timeout))
    print('Loaded proxies:', colored(len(proxy_list), 'cyan'))
  except Exception as e:
    print(colored('Error while loading proxies.','red'),e)
    time.sleep(5)
    pass
  finally:
    broker.stop()
    tasks.cancel()

def setup_proxy(type=None, host=None, port=None, reset=False):
  if reset: 
    socket.socket = default_socket
  else: 
    socks.set_default_proxy(type, host, port)
    socket.socket = socks.socksocket

async def save_proxy(proxies):
  while True:
    proxy = await proxies.get()
    if proxy is None: break
    ip = (proxy.host, proxy.port)
    if proxy.avg_resp_time < 0.5 and ip not in proxy_excepted:
      proxy_list.append(ip)

def change_proxy(remove=True):
  global PROXY
  global current_proxy
  empty_count = 0

  while True:
    if remove and len(current_proxy) > 1:
      proxy_excepted.append(current_proxy)
      if current_proxy in proxy_list: proxy_list.remove(current_proxy)

    if empty_count > 3:	
      print(colored('No proxy avaliable. Switch to normal mode.', 'cyan'))
      PROXY = False
      setup_proxy(reset=True)
      break   
	  
    if len(proxy_list) < 3:	
      get_proxies()
      empty_count += 1
      continue	

    index = random.randint(0, len(proxy_list)-1)
    current_proxy = proxy_list[index]
    print(colored('Trying proxy:', 'magenta'),'%s:%d'%(current_proxy[0], current_proxy[1]))
    try: 
      setup_proxy(socks.SOCKS5, current_proxy[0], current_proxy[1])
      iprequest = requests.get('http://checkip.amazonaws.com/', timeout=0.5)      
      print(colored('New IP:', 'green'), iprequest.text.strip())
      break
    except: 
      proxy_excepted.append(current_proxy)
      proxy_list.remove(current_proxy) 
      continue  

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
      download(url, pdf, 5)
      print('Save:', colored(fname, 'grey'))
      count += 1
  return count

def brutforce_articles():
  print(colored('Using proxy:', 'cyan'), PROXY)
  if PROXY:
    get_proxies()
    change_proxy(False)

  print(colored('Save path:', 'red'), SAMPLES_DIR)
  for i in range(START, PAGES):   
    save_start2config(i)
    downloaded = len(os.listdir(SAMPLES_DIR))
    print(colored('Downloaded:', 'yellow'), downloaded)
    print(colored('Reading %d page of %d' % (i, PAGES), 'blue'), '(%f%%)' % (i/PAGES))
    if downloaded > COUNT: break
    link = 'https://cyberleninka.ru/article/c/meditsina-i-zdravoohranenie/'+str(i)
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