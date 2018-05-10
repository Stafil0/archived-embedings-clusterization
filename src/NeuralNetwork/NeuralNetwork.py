import gensim
import logging
import gzip
import os
import sys

# Path params
MODEL_FILE = 'model.bin'
SENTENCES_FILE = 'sentences.txt'
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLES_DIR = os.path.abspath(os.path.join(os.path.join(__file__, '../../..'), 'samples'))
SENTENCES_PATH = os.path.join(SAMPLES_DIR, SENTENCES_FILE)
MODEL_PATH = os.path.join(CURRENT_DIR, MODEL_FILE)

# Model params
MODEL_SIZE = 100
MODEL_WINDOW = 5
MODEL_MIN_COUNT = 2
MODEL_WORKERS = 8
MODEL_EPOCHS = 1000
MODEL_SKIPGRAM = 1

# Training params
TRAINING_UPDATE = False

def load_sentences():
  print('Loading sentences')
  if (os.path.isfile(SENTENCES_PATH)):
    sentences = gensim.models.word2vec.LineSentence(SENTENCES_FILE)
    return sentences
  else:
    print('No sentence file!')
    return None  

def load_model():
  global TRAINING_UPDATE
  print('Loading model')
  if (os.path.isfile(MODEL_PATH)):
    TRAINING_UPDATE = True
    model = gensim.models.Word2Vec.load(MODEL_FILE)
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

def train_model(model, sentences):
  print('Start training model')

  model.build_vocab(sentences, update=TRAINING_UPDATE)
  model.train(sentences, 
              total_examples=model.corpus_count,
              epochs=model.epochs)
  print('Training done!')

  print('Saving model')
  model.save(MODEL_FILE)
  return model

def test_model(model, word):
  similar = model.wv.most_similar(positive=word)
  print(similar)

if __name__ == '__main__':
  logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
  
  sentences = load_sentences()
  model = load_model()

  if (model == None or sentences == None):
    print('Bad load of model or sentences!')
    sys.exit(1)

  model = train_model(model, sentences)
  test_model(model, 'гистология')