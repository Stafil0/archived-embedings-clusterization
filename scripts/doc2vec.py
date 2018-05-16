import logging
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
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec
from collections import OrderedDict
from random import shuffle
from contextlib import contextmanager
from timeit import default_timer

# Path params
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
MODEL_DIR = os.path.join(DATA_DIR, 'models')
SAMPLES_DIR = os.path.join(DATA_DIR, 'samples')
VOCAB_PATH = os.path.join(DATA_DIR, 'vocab.data')

# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

@contextmanager
def elapsed_timer():
  start = default_timer()
  elapser = lambda: default_timer() - start
  yield lambda: elapser()
  end = default_timer()
  elapser = lambda: end-start

def load(path):
  file = gzip.open(path,'rb')
  object = pickle.load(file)
  file.close()
  return object

def save(object, path):
  file = gzip.open(path,'wb')
  pickle.dump(object, file)
  file.close()

def load_docs(path):
  if os.path.exists(path):
    vocab = load(path)
    documents = [TaggedDocument(doc.index.tolist(), doc.name) for doc in vocab]
    return documents

def load_models(docs, path=None):
  update = False
  if not os.listdir(path):
    simple_models = [
      # PV-DBOW w/words
      Doc2Vec(dm=0, dbow_words=1, vector_size=100, window=10, negative=5, hs=0, min_count=2, workers=8),
      # PV-DM w/average
      Doc2Vec(dm=1, dm_mean=1, vector_size=100, window=10, negative=5, hs=0, min_count=2, workers=8)]
  else: 
    simple_models = []
    update = True
    for file in os.listdir(path):
      simple_models.append(Doc2Vec.load(os.path.abspath(os.path.join(path, file))))

  for model in simple_models:
      model.build_vocab(docs, update)
  return OrderedDict((str(model), model) for model in simple_models)

def train(models, docs):
  alpha, min_alpha, passes = (0.025, 0.001, 5)
  alpha_delta = (alpha - min_alpha) / passes

  for epoch in range(passes):
    shuffle(docs)

    for name, train_model in models.items():
      duration = 'na'
      train_model.alpha, train_model.min_alpha = alpha, alpha
      with elapsed_timer() as elapsed:
        train_model.train(docs, total_examples=train_model.corpus_count, epochs=train_model.epochs)
        duration = '%.1f' % elapsed()
      print("%i passes : %s %ss" % (epoch + 1, name, duration))

    print('Completed pass %i at alpha %f' % (epoch + 1, alpha))
    alpha -= alpha_delta
    
  print("END %s" % str(datetime.datetime.now()))
  return models

def save_models(models, path):
  for name, train_model in models.items():
    regex = re.compile('[%s]' % re.escape(string.punctuation))
    fname = regex.sub('_',name)
    modelPath = os.path.abspath(os.path.join(path, fname+'.bin'))
    train_model.save(modelPath)

if __name__ == '__main__':  
 docs = load_docs(VOCAB_PATH)
 models = load_models(docs, MODEL_DIR)
 models = train(models, docs)
 save_models(models, MODEL_DIR)

 print(models['Doc2Vec(dbow+w,d100,n5,w10,mc2,s0.001,t8)'].most_similar('бронхит', topn=20))
 print(models['Doc2Vec(dm/m,d100,n5,w10,mc2,s0.001,t8)'].most_similar('бронхит', topn=20))
