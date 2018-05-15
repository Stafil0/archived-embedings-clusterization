import logging
import os
import nltk 
import pandas
import re
import pickle
from tika import parser
from nltk.stem.snowball import SnowballStemmer

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
SAMPLES_DIR = os.path.join(DATA_DIR, 'samples')
VOCAB_DIR = os.path.join(DATA_DIR, 'vocab.data')

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def pdf2text(path):
  content = parser.from_file(path)
  text = content['content']
  return text

def text2neural_data(text, language):
  tokens = tokenize(text, language)
  stemmed_tokens = stem(tokens, language)
  vocab = pandas.DataFrame({'words': tokens}, index = stemmed_tokens)
  return vocab

def stem(tokens, language):
  stemmer = SnowballStemmer(language)
  stems = [stemmer.stem(t) for t in tokens]
  return stems

def tokenize_and_stem(text, language):
  stemmer = SnowballStemmer(language)
  filtered_tokens = tokenize(text, language)
  stems = [stemmer.stem(t) for t in filtered_tokens]
  return stems

def tokenize(text, language):
  stopwords = nltk.corpus.stopwords.words(language)
  ftext = re.sub('-\s+', '', text).lower()
  tokens = [word for sent in nltk.sent_tokenize(ftext) for word in nltk.word_tokenize(sent) if word not in stopwords and re.search('[a-zA-Zа-яА-Я]', word)]
  return tokens

def pdfs2neural_data(pdfDir, dataPath, language='russian'):
  if os.path.exists(dataPath):
    with open(dataPath, 'rb') as file:
      tokens = pickle.load(file)
  else:
    tokens = []

  if os.path.exists(pdfDir):
    for pdf in os.listdir(pdfDir):
      extension = pdf.split('.')[-1]
      if extension == 'pdf':
        pdfPath = os.path.abspath(os.path.join(pdfDir, pdf))
        text = pdf2text(pdfPath)
        tokens.append(tokenize_and_stem(text, language))

  with open(dataPath, 'wb') as file:
    pickle.dump(tokens, file)

if __name__ == '__main__':
  pdfs2neural_data(SAMPLES_DIR, VOCAB_DIR)
