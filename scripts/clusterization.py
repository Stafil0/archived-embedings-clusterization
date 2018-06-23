import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import random
import numpy as np
import gzip
import pickle
import re
from collections import Counter
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from termcolor import colored
from sklearn.cluster import SpectralClustering
from sklearn.cluster import Birch
from sklearn.cluster import DBSCAN
from sklearn.cluster import KMeans
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.metrics import silhouette_score, calinski_harabaz_score
from scipy.spatial.distance import pdist 
from itertools import cycle

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(os.path.join(CURRENT_DIR, '..'), 'data'))
MODEL_DIR = os.path.join(DATA_DIR, 'models')

# logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def pca(model):
  data = model.docvecs.doctag_syn0
  data = PCA(n_components=2).fit_transform(data)
  result = np.asarray(data)
  return result

def raw(model):
  data = model.docvecs.doctag_syn0
  result = np.asarray(data)
  return result

def tsne(model):
  data = model.docvecs.doctag_syn0
  data = TSNE(n_components=2).fit_transform(data)
  result = np.asarray(data)
  return result

def dbscan(X):
  db = DBSCAN(eps=0.05, min_samples=1).fit(X)
  return db

def affinity(X):
  pref = -1*(np.max(pdist(X))**2)
  af = AffinityPropagation(preference=pref, damping=0.9).fit(X)
  print('af')
  print(silhouette_score(X, af.labels_))
  print(calinski_harabaz_score(X, af.labels_))
  return af

def birch(X):
  br = Birch(n_clusters=None, threshold=10).fit(X)  
  print('br')
  print(silhouette_score(X, br.labels_))
  print(calinski_harabaz_score(X, br.labels_))
  return br

def kmeans(X):
  clusters = 3
  max = 0
  for k in range(3, 30):
    kmeans = KMeans(n_clusters=k).fit(X)
    labels = kmeans.labels_
    #avg = silhouette_score(X, labels)
    avg = calinski_harabaz_score(X, labels)
    if max < avg:
      max = avg
      clusters = k
  kmeans = KMeans(n_clusters=clusters, init='k-means++').fit(X)
  print('km')
  print(silhouette_score(X, kmeans.labels_))
  print(calinski_harabaz_score(X, kmeans.labels_))
  return kmeans

def agglomerative(X):
  clusters = 3
  max = 0
  for k in range(3, 30):
    ward = AgglomerativeClustering(n_clusters=k).fit(X)
    labels = ward.labels_
    #avg = silhouette_score(X, labels)
    avg = calinski_harabaz_score(X, labels)
    if max < avg:
      max = avg
      clusters = k
  ward = AgglomerativeClustering(n_clusters=clusters).fit(X)  
  print('wrd')
  print(silhouette_score(X, ward.labels_))
  print(calinski_harabaz_score(X, ward.labels_))
  return ward

def meanshift(X):
  samples = int(X.shape[0]/10)
  bandwidth = estimate_bandwidth(X, quantile=samples/X.shape[0], n_samples=samples)
  ms = MeanShift(bandwidth=bandwidth, bin_seeding=True).fit(X)
  print('ms')
  #print(silhouette_score(X, ms.labels_))
  #print(calinski_harabaz_score(X, ms.labels_))
  return ms
 
def docs2clusters(labels, clusters):
  docs = list(zip(labels, clusters.tolist()))
  return docs

def cluster_docs(cluster, clusters_docs):
  if cluster < 0: return [d for d, c in clusters_docs]
  else: return [d for d, c in clusters_docs if c == cluster]

def cluster_words(cluster, clusters_docs, docs, count=10):
  clust_docs = cluster_docs(cluster, clusters_docs)
  tagged_docs = [d for d in docs if d.tags[0] in clust_docs]
  words = [word for d in tagged_docs for word in d.words]
  topic_words = Counter(words).most_common(count)
  return topic_words

if __name__ == '__main__':
  import manager
  import doc2vec
  vectors = manager.load(os.path.join(manager.PICKLES_DIR, 'vectors.pkl'))
  manager.save(clusterers, clusters_pkl)