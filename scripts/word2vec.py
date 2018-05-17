import gensim
import logging
import gzip
import os
import sys

# Path params
MODEL_FILE = 'model.bin'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
SENTENCES_DIR = os.path.join(DATA_DIR, 'sentences')
MODEL_PATH = os.path.join(DATA_DIR, MODEL_FILE)

# Model params
MODEL_SIZE = 100
MODEL_WINDOW = 5
MODEL_MIN_COUNT = 3
MODEL_WORKERS = 16
MODEL_EPOCHS = 500
MODEL_SKIPGRAM = 1

# Training params
TRAINING_UPDATE = False

def load_sentences():
  print('Loading sentences')
  if (os.path.isdir(SENTENCES_DIR)):
    sentences = gensim.models.word2vec.PathLineSentences(SENTENCES_DIR)
    return sentences
  else:
    print('No sentence folder!')
    return None  

def load_model():
  global TRAINING_UPDATE
  print('Loading model')
  if (os.path.isfile(MODEL_PATH)):
    TRAINING_UPDATE = True
    model = gensim.models.Word2Vec.load(MODEL_PATH)
    print('Model loaded')
  else:
    TRAINING_UPDATE = False
    model = gensim.models.Word2Vec(size = MODEL_SIZE,
                                   min_count = MODEL_MIN_COUNT,
                                   workers = MODEL_WORKERS,
                                   sg = MODEL_SKIPGRAM,
                                   iter = MODEL_EPOCHS,
                                   window = MODEL_WINDOW)
    print('New model created')
  return model

def train(model, sentences):
  print('Start training model')

  bigrams = gensim.models.Phrases(sentences)
  phrases = bigrams[sentences]
  model.build_vocab(phrases, update=TRAINING_UPDATE)
  model.train(phrases, 
              total_examples=model.corpus_count,
              epochs=model.epochs)
  print('Training done!')

  print('Saving model')
  model.save(MODEL_PATH)
  return model

def similar_by_words(model, positive, negative = None):
  similar = model.wv.most_similar(positive=positive, negative=negative)
  print(similar)

def similar_by_word(model, word):
  similar = model.wv.similar_by_word(word)
  print(similar)

if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
  
  # sentences = load_sentences()
  model = load_model()

  #if (model == None or sentences == None):
   # print('Bad load of model or sentences!')
   # sys.exit(1)

  # model = train(model, sentences)
  similar_by_words(model, 'какие препараты назначают для лечения бронхита'.split())