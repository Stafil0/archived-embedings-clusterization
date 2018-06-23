import logging
import manager
import gzip
import os
import sys
import pickle
import gensim.models.doc2vec
import multiprocessing
import datetime
import time 
import gensim
import string
import re
import colorama
import pandas as pd
import matplotlib.pyplot as plt
import random
import multiprocessing
from bs4 import BeautifulSoup
from sklearn.manifold import TSNE
from termcolor import colored
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec
from collections import OrderedDict
from random import shuffle
from contextlib import contextmanager
from timeit import default_timer
from nltk.stem.snowball import SnowballStemmer

CONFIG_FILE = '_config.xml'
MODEL_DIR = '.'
PLOT_DIR = '.'
VOCAB_PATH = '.'
EPOCH = 0

colorama.init()
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

@contextmanager
def elapsed_timer():
  start = default_timer()
  elapser = lambda: default_timer() - start
  yield lambda: elapser()
  end = default_timer()
  elapser = lambda: end-start

def trim_punctuation(str, symbol):
  regex = re.compile('[%s]' % re.escape(string.punctuation))
  return regex.sub(symbol, str)

def init(path=CONFIG_FILE):
  global MODEL_DIR
  global PLOT_DIR
  global VOCAB_PATH
  global EPOCH
  global PASSES
  global ALPHA

  with open(path, 'rb') as file:
    content = file.read()
  soup = BeautifulSoup(content, 'lxml')
  all = soup.find('all')
  d2v = soup.find('config', {'name':'doc2vec'})

  MODEL_DIR = all.find('models').text.strip()
  PLOT_DIR = os.path.join(all.find('plots').text.strip(), 'models')
  VOCAB_PATH = os.path.join(all.find('vocabs').text.strip(), d2v.find('vocab').text.strip())

  EPOCH = int(d2v.find('epoch').text)
  ALPHA = float(d2v.find('alpha').text)
  PASSES = int(d2v.find('passes').text)  

def save(epoch, passes, alpha):
  with open(CONFIG_FILE, 'rb') as file:
    soup = BeautifulSoup(file, 'html.parser')
    articles = soup.find('config', {'name':'doc2vec'})
    articles.find('epoch').string.replace_with(str(epoch))
    articles.find('passes').string.replace_with(str(passes-epoch))
    articles.find('alpha').string.replace_with(str(alpha))
  with open(CONFIG_FILE, 'wb') as file:
    file.write(soup.prettify('utf-8', 'minimal'))

def load_models(path, docs=None, vocab=True, update=False, delete_old=False, create=True, load=False):
  models = []
  any_models = [file for file in os.listdir(path) 
                if not file.startswith('_') and file.endswith('.bin')]
  if delete_old and any_models:
    for file in any_models:
      os.remove(os.path.join(path, file))
  if load and any_models:
    print(colored('Loading trained models...', 'blue'))
    for file in any_models:
      print(colored('Loaded:', 'blue'), file)
      model = Doc2Vec.load(os.path.abspath(os.path.join(path, file)))
      if vocab and docs != None:
        print(colored('Building vocab for:', 'blue'), str(model), end=' ')
        model.build_vocab(docs, update)
        print(colored('... Done.', 'blue'))
      models.append(model)
  if create and not models:
    print(colored('Creating new models...', 'blue')) 
    # PV-DBOW w/words
    models.append(Doc2Vec(dm=0, dbow_words=1, vector_size=150, window=10, negative=5, epochs=5, hs=0, min_count=2, workers=8))
    # PV-DM w/average
    #models.append(Doc2Vec(dm=1, dm_mean=1, vector_size=150, window=10, negative=5, epochs=5, hs=0, min_count=2, workers=8))
    if docs != None:
      for model in models:
        print(colored('Building vocab for:', 'blue'), str(model), end=' ')
        model.build_vocab(docs, update)
        print(colored('... Done.', 'blue'))
  print(colored('Models loaded.', 'blue'))
  return models

def save_model(model, path):
  print(colored('Saving model:', 'yellow'), str(model), end=' ')
  fname = trim_punctuation(str(model),'_')
  modelPath = os.path.abspath(os.path.join(path, fname+'.bin'))
  model.save(modelPath)
  print(colored('... Saved.', 'yellow'))

def save_models(models, path):
  for model in models:
    save_model(model, path)

def train_models(models, docs):
  alpha, min_alpha, passes = (ALPHA, 0.001, PASSES)
  alpha_delta = (alpha - min_alpha) / passes

  print(colored('Started:', 'cyan'),'%i/%i (%f)' % (EPOCH, EPOCH+passes, alpha))
  for epoch in range(EPOCH, EPOCH+passes):
    shuffle(docs)
    for model in models:
      duration = 'na'
      model.alpha, model.min_alpha = alpha, alpha
      with elapsed_timer() as elapsed:
        model.train(docs, total_examples=model.corpus_count, epochs=model.epochs)
        duration = '%.1f' % elapsed()
      print(colored('%ix%i passes:'%(epoch + 1, model.epochs),'green'), '%s %ss'%(str(model), duration))
      save_model(model, MODEL_DIR)

    print(colored('Completed pass:', 'red'), '%i'%(epoch + 1), colored('alpha:','red'),'%f'%(alpha))
    alpha -= alpha_delta
    save(epoch, passes, alpha)
    
  print(colored('Ended:', 'cyan'),'%s' % str(datetime.datetime.now()))
  return models

def assosiatons(model, words):
  similars = words
  while True:
    topic = [word[0] for word in model.most_similar_cosmul(similars, topn=15) if word[1] > 0.75]
    if not topic:
      return similars
    similars.extend(topic)
  
init(CONFIG_FILE)


if __name__ == '__main__':  
  docs = manager.load_docs(path=VOCAB_PATH, random_docs=False, count=-1)
  models = load_models(docs=docs, path=MODEL_DIR, vocab=False, update=False, delete_old=False, create=False, load=True)

  models = train_models(models, docs)
  save_models(models, MODEL_DIR)
'''  
  words = 'рак онкология'.split()
  stemmer = SnowballStemmer('russian')
  stems = [stemmer.stem(word) for word in words]
  doc_id = random.randint(0, len(docs) - 1)
  doc = docs[doc_id]

  for model in models:
    print(colored('Model:','green'), str(model))
    doc_words = model.infer_vector(doc.words)
    search_words = model.infer_vector(stems)
    similar_docs = model.docvecs.most_similar([doc_words])
    similar_docs_by_sentnces = model.docvecs.most_similar([search_words])
    similar_words = model.wv.most_similar([stems[0]])
    print(colored('Similar by tag:','yellow'), doc.tags[0])
    print(*similar_docs, sep='\n')
    print(colored('Similar by sentence:','red'),' '.join(stems))
    print(*similar_docs_by_sentnces, sep='\n')
    print(colored('Similar words:','cyan'),stems[0])
    print(*similar_words, sep='\n')
    print()
'''