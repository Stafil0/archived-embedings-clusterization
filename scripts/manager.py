import gzip
import pickle
import os
from gensim.models.doc2vec import TaggedDocument

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
MODEL_DIR = os.path.join(DATA_DIR, 'models')
VOCAB_DIR = os.path.join(DATA_DIR, 'vocabs')
PICKLES_DIR = os.path.join(DATA_DIR, 'pickles')

def read(path):
  with open(path, 'rb') as file:
    raw = file.read()
  return raw

def load(path):
  file = gzip.open(path,'rb')
  obj = pickle.load(file)
  file.close()
  return obj

def save(object, path):
  file = gzip.open(path,'wb')
  pickle.dump(object, file)
  file.close()

def load_multi(path):
  file = gzip.open(path,'rb')
  objs = []
  while True:
    try: objs.append(pickle.load(file))
    except EOFError: break
  file.close()
  return objs

def load_vocab(path):
  file = gzip.open(path,'rb')
  objs = {}
  while True:
    try:
      obj = pickle.load(file)
      vocab = {word[0]:word[1] for word in obj[1]}
      objs.update(vocab)
    except EOFError: break
  file.close()
  return objs

def read_vocab(path):
  file = gzip.open(path,'rb')
  objs = []
  while True:
    try:
      obj = pickle.load(file)
      objs.extend([obj[0]])
    except EOFError: break
  file.close()
  return objs

def save_multi(object, path):
  file = gzip.open(path,'ab')
  pickle.dump(object, file)
  file.close()

def save_subvocab(dir, main_vocab, percents):
  more_half = int(100/(100-percents))
  less_half = int(100/percents)
  name = 'vocab%d.data'%percents
  path = os.path.join(dir, name)
  new = gzip.open(path,'ab')
  main = gzip.open(main_vocab,'rb')
  index = 0
  while True:
    try:
      obj = pickle.load(main)
      if less_half > 1:
        if index % less_half == 0:
          pickle.dump(obj, new)
      else:
        if index % more_half != 0:
          pickle.dump(obj, new)
      index += 1
    except EOFError: break
  main.close()
  new.close()

def load_docs(path, random_docs=False, count=-1, full_word=0):
  file = gzip.open(path,'rb')
  documents = []
  index = 0
  while True:
    try: 
      obj = pickle.load(file)
      name = obj[0]
      words = [word[full_word] for word in obj[1]]
      documents.append(TaggedDocument(words, [name[:-4].strip()]))
      if count >= 0 and index >= count:
        break
      index += 1
    except EOFError: 
      break
  file.close()
  if random_docs:
    shuffle(documents)
  if count >= 0:
    documents = documents[:count]
  return documents