import clusterization
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import SpectralClustering
from sklearn.cluster import Birch
from sklearn.cluster import MeanShift, estimate_bandwidth
from sklearn.metrics import silhouette_score
from itertools import cycle

def doc2vec(canvas, labels, docs, selected, X):
  red = np.asarray([X[i] for i, label in enumerate(labels) if label in docs])  
  black = np.asarray([X[i] for i, label in enumerate(labels) if label not in docs]) 
  canvas.ax.scatter(black[:,0], black[:,1], c='black', s=2)
  canvas.ax.scatter(red[:,0], red[:,1], c='red', s=30)
  if selected:
    green = np.asarray([X[i] for i, label in enumerate(labels) if label in selected])
    canvas.ax.scatter(green[:,0], green[:,1], c='green', s=60)
  canvas.draw()

def articles(canvas, cl, cluster, similar_docs, doc, docs, X):
  if cl != None:
    labels = cl.labels_
    red = labels == cluster
    black = labels != cluster
  else:
    red = labels == False
    black = labels == True
  blue = np.asarray([X[i] for i, label in enumerate(docs) if label in similar_docs]) 
  green = np.asarray([X[i] for i, label in enumerate(docs) if label == doc]) 
  canvas.ax.plot(X[red, 0], X[red, 1], 'r.', markersize=8)
  canvas.ax.plot(X[black, 0], X[black, 1], 'k.', markersize=4)
  canvas.ax.plot(blue[:,0], blue[:,1], 'b.', markersize=6)
  canvas.ax.plot(green[:, 0], green[:, 1], 'g.', markersize=10)
  canvas.draw()

def raw(canvas, X):
  canvas.ax.scatter(X[:,0], X[:,1], c='black', s=7)
  canvas.draw()

def affinity(canvas, af, X, cluster=-1):
  labels = af.labels_
  cluster_centers_indices = af.cluster_centers_indices_
  n_clusters_ = len(cluster_centers_indices)
  colors = cycle('bgrcmybgrcmybgrcmybgrcmy')
  marker = cycle('v^<>sp*hHDv^<>sp*hHD')
  for k, col, m in zip(range(n_clusters_), colors, marker):
    if cluster >= 0 and k != cluster: col = 'k'
    class_members = labels == k
    cluster_center = X[cluster_centers_indices[k]]
    canvas.ax.plot(X[class_members, 0], X[class_members, 1], col + m, markersize=5)
    canvas.ax.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=10)
  canvas.draw()

def kmeans(canvas, km, X, cluster=-1):
  labels = km.labels_
  predict = km.predict(X)    
  centers = km.cluster_centers_
  if cluster < 0:
    canvas.ax.scatter(X[:,0], X[:,1], c=predict, s=9)
    canvas.ax.scatter(centers[:, 0], centers[:, 1], c='black', s=200, alpha=0.5)
  else:
    class_members = labels == cluster
    non_class = labels != cluster
    canvas.ax.plot(X[class_members,0], X[class_members,1], 'g.', markersize=7)
    canvas.ax.plot(X[non_class,0], X[non_class,1], 'k.', markersize=7)
    canvas.ax.plot(centers[:, 0], centers[:, 1], 'k.', markersize=25, alpha=0.5)
  canvas.draw()

def dbscan(canvas, db, X, cluster=-1):
  core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
  core_samples_mask[db.core_sample_indices_] = True
  labels = db.labels_
  unique_labels = set(labels)
  colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
  for k, col in zip(unique_labels, colors):
    if k == -1 or k != cluster:
      col = [0, 0, 0, 1]
    class_member_mask = (labels == k)
    xy = X[class_member_mask & core_samples_mask]
    canvas.ax.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col), markeredgecolor='k', markersize=8)
    xy = X[class_member_mask & ~core_samples_mask]
    canvas.ax.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=tuple(col), markeredgecolor='k', markersize=4)
  canvas.draw()

def birch(canvas, br, X, cluster=-1):
  predict = br.predict(X)
  centers = br.subcluster_centers_
  labels = br.labels_
  if cluster < 0:
    canvas.ax.scatter(X[:,0], X[:,1], c=predict, s=9)
    canvas.ax.scatter(centers[:, 0], centers[:, 1], c='k', s=200, marker='+')
  else:
    class_members = labels == cluster
    non_class = labels != cluster
    canvas.ax.plot(X[class_members,0], X[class_members,1], 'g.', markersize=7)
    canvas.ax.plot(X[non_class,0], X[non_class,1], 'k.', markersize=7)
    canvas.ax.plot(centers[:, 0], centers[:, 1], 'k+', markersize=25, alpha=0.5)  
  canvas.draw()

def agglomerative(canvas, ward, X, cluster=-1):
  labels = ward.labels_
  predict = ward.fit_predict(X)
    
  unique_labels = np.unique(labels)
  colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
  for k, col in zip(range(len(unique_labels)), colors):
    if cluster >= 0 and k != cluster: col = [0, 0, 0, 1]
    class_member_mask = (labels == k)
    canvas.ax.plot(X[class_member_mask, 0], X[class_member_mask, 1], 'o', markerfacecolor=tuple(col), markeredgecolor='k', markersize=5)
  canvas.draw()

def meanshift(canvas, ms, X, cluster=-1):
  labels = ms.labels_
  cluster_centers = ms.cluster_centers_
  labels_unique = np.unique(labels)
  n_clusters_ = len(labels_unique)
  colors = cycle('bgrcmybgrcmybgrcmybgrcmy')
  for k, col in zip(range(n_clusters_), colors):
    if cluster >= 0 and k != cluster: col = 'k'
    my_members = labels == k
    cluster_center = cluster_centers[k]
    canvas.ax.plot(X[my_members, 0], X[my_members, 1], col + '.')
    canvas.ax.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=10)
  canvas.draw()