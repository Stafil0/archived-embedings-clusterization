import logging
import os
import nltk 
import pandas
import re
import pickle
import gzip
import colorama
import string
import manager
from termcolor import colored
from tika import parser
from nltk.stem.snowball import SnowballStemmer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
SAMPLES_DIR = os.path.join(DATA_DIR, 'samples')
VOCAB_DIR = os.path.join(DATA_DIR, 'vocabs')
VOCAB_PATH = os.path.join(VOCAB_DIR, 'vocab100.data')

colorama.init()
# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def pdf2text(raw):
  text = None
  try:
    content = parser.from_buffer(raw)
    if content['status'] == 200:
      text = content['content']
  except: text = None
  return text

def text2neural_data(text, language='russian'):
  tokens = stem_and_tokenize(text, language)
  if tokens == None or len(tokens) < 20: 
    return None
  return tokens

def text2neural_data2(text, language='russian'):
  tokens = tokenize(text, language)
  if tokens == None or len(tokens) < 20: 
    return None  
  stemmed_tokens = stem(tokens, language)
  vocab = tuple(zip(stemmed_tokens, tokens))
  return vocab

def stem(tokens, language):
  stemmer = SnowballStemmer(language)
  stopwords = nltk.corpus.stopwords.words(language)
  stems = [stemmer.stem(t) for t in tokens]
  return stems

def tokenize(text, language):
  if text == None: return None
  stopwords = nltk.corpus.stopwords.words(language)
  ftext = re.sub('-\s+', '', text).lower()
  translator = str.maketrans('', '', string.punctuation)
  tokens = [word.translate(translator) 
            for sent in nltk.sent_tokenize(ftext) for word in nltk.word_tokenize(sent) 
            if word not in stopwords and len(word)>3 and re.search('[а-яА-Я\-\.]', word)]
  return tokens

def stem_and_tokenize(text, language):
  if text == None: return None
  stopwords = nltk.corpus.stopwords.words(language)
  stemmer = SnowballStemmer(language)
  ftext = re.sub('-\s+', '', text).lower()
  translator = str.maketrans('', '', string.punctuation)
  tokens = [(stemmer.stem(word.translate(translator)), word.translate(translator))
           for sent in nltk.sent_tokenize(ftext) for word in nltk.word_tokenize(sent) 
           if word not in stopwords and stemmer.stem(word) not in stopwords 
           and len(word)>3 and re.search('[а-яА-Я]{2,}', word)]
  return tokens

def pdfs2neural_data(pdfDir, dataPath, language='russian'):
  if os.path.exists(dataPath): converted = manager.read_vocab(dataPath)
  else: converted = []
  not_converted = [name for name in os.listdir(pdfDir) if name not in converted]
  print(
    colored('Loaded vocab data.','green'),'\n',
    colored('Converted:','green'),len(converted),'\n',
    colored('Not converted:', 'green'), len(not_converted), '\n',
    colored('Done:','green'), len(converted)/len(os.listdir(pdfDir))*100,'%')

  if os.path.exists(pdfDir):
    for pdf in not_converted:
      # if len(vocab) > 200: break
      extension = pdf.split('.')[-1]
      if extension == 'pdf':
        print(colored('Converting:', 'blue'), pdf, end=' ')
        pdfPath = os.path.abspath(os.path.join(pdfDir, pdf))
        raw = manager.read(pdfPath)
        text = pdf2text(raw)
        data = text2neural_data(text)
        if data != None: 
          print(colored('Converted.', 'blue'))
          manager.save_multi((pdf, data), dataPath)
        else:
          print('\n',colored('Error converting. Deleting:','red'), pdf)
          os.remove(pdfPath)

if __name__ == '__main__':
  pdfs2neural_data(SAMPLES_DIR, VOCAB_PATH)
