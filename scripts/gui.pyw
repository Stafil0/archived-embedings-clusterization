import form
import numpy as np
import gzip
import os
import sys
import datetime
import time 
import string
import re
import pandas as pd
import random
import doc2vec
import clusterization
import plotter
import sys
import converter
import manager
from PyQt5 import QtWidgets, QtCore
from nltk.stem.snowball import SnowballStemmer

class MainWindow(QtWidgets.QMainWindow, form.Ui_MainWindow):
  def __init__(self):
    super().__init__()
    self.setupUi(self)
        
    vocab_dir = os.path.join(manager.VOCAB_DIR, 'vocab100.data')
    vectors_pkl = os.path.join(manager.PICKLES_DIR, 'vectors.pkl')
    docs_pkl = os.path.join(manager.PICKLES_DIR, 'docs.pkl')
    vocab_pkl = os.path.join(manager.PICKLES_DIR, 'vocab.pkl')
    clusters_pkl = os.path.join(manager.PICKLES_DIR, 'clusters.pkl')
    topics_pkl = os.path.join(manager.PICKLES_DIR, 'topics.pkl')
    self.model = doc2vec.load_models(doc2vec.MODEL_DIR, vocab=False, create=False, load=True)[0]
    self.clusterers = manager.load(clusters_pkl)
    self.docs = manager.load(docs_pkl)
    self.vocab = manager.load(vocab_pkl)  
    self.vectors = manager.load(vectors_pkl)
    self.topics = manager.load(topics_pkl)
    self.labels = list(self.model.docvecs.doctags.keys())
    self.stemmer = SnowballStemmer('russian')

    #self.clusterers[0] = clusterization.affinity(self.vectors)
    #self.clusterers[1] = clusterization.kmeans(self.vectors)
    #self.clusterers[2] = clusterization.agglomerative(self.vectors)
    #self.clusterers[3] = clusterization.meanshift(self.vectors)
    #self.clusterers[4] = clusterization.birch(self.vectors)
    #self.clusterers[5] = None
    #self.clusterers[6] = None
    #manager.save(self.clusterers, clusters_pkl)
   
    raw_vectors = clusterization.raw(self.model)
    self.completer = QtWidgets.QCompleter()
    self.completer.setModel(QtCore.QStringListModel(self.labels))
    self.completer.setFilterMode(QtCore.Qt.MatchContains)
    self.searchLine.setCompleter(self.completer)

    self.searchButton.clicked.connect(self.search)
    self.clusterButton.clicked.connect(self.show_clusters)
    self.searchMethod.currentIndexChanged.connect(self.search_method_changed)
    self.clusterMethod.currentIndexChanged.connect(self.clusterer_changed)
    self.rightList.itemSelectionChanged.connect(self.draw_clusters)
    self.themeBox.currentIndexChanged.connect(self.group_changed)

    self.lastSearch = ''
    self.plotHidden = True
    self.plotted = False
    self.searched = False
    self.allgroups = 'Все группы'
    
    self.plotWidget.hide()
    self.clusterMethod.setCurrentIndex(1)
    self.searchMethod.setCurrentIndex(0)
    self.search_method_changed()

    header = self.leftTable.horizontalHeader()
    header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
    header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)

  def search(self):
    self.searched = True
    searchMethod = self.searchMethod.currentIndex()
    clusterMethod = self.clusterMethod.currentIndex()
    text = self.searchLine.text().strip()
    if searchMethod == 0:
      words = text.split()
      if not words or text == self.lastSearch:
        return 
    
      self.lastSearch = text
      stems = [self.stemmer.stem(word) for word in words]
      try:
        search_words = self.model.infer_vector(stems)
        similar_docs = self.model.docvecs.most_similar([search_words], topn=50)
        similar_words = self.model.most_similar_cosmul(stems, topn=50)
      except:
        return
      self.similar_docs = list(zip(*similar_docs))[0]

      assosiation = doc2vec.assosiatons(self.model, stems)
      vocab_assosiations = [self.vocab[ass] for ass in assosiation]

      self.rightList.clear()
      self.leftTable.clear()
      self.leftTable.setRowCount(0)
      self.themeText.setText(' '.join(vocab_assosiations))    
      self.rightList.addItems(self.similar_docs)
      self.leftTable.setHorizontalHeaderLabels(['Слово', 'Близость'])
      for word in similar_words:
        row = self.leftTable.rowCount()
        self.leftTable.insertRow(row)
        self.leftTable.setItem(row, 0, QtWidgets.QTableWidgetItem(self.vocab[word[0]]))
        self.leftTable.setItem(row, 1, QtWidgets.QTableWidgetItem(str(word[1])[:4]))

    elif searchMethod == 1:
      try:
        doc = [document for document in self.docs if text in document.tags][0]
        words = self.model.infer_vector(doc.words)
        similar_docs = self.model.docvecs.most_similar([words], topn=50)
      except:
        return

      self.similar_docs = list(zip(*similar_docs))[0][1:]

      clusters = self.clusterers[clusterMethod].labels_
      self.clusters_docs = clusterization.docs2clusters(self.labels, clusters)
      self.cluster = [c for d,c in self.clusters_docs if text == d][0]
      top_words = self.topics[clusterMethod][self.cluster]
      docs = clusterization.cluster_docs(self.cluster, self.clusters_docs)
      words = [self.vocab[word] for word in list(zip(*top_words))[0][:10]]
      self.themeText.setText(' '.join(words))

      self.rightList.clear()
      self.rightList2.clear()
      self.rightList.addItems(self.similar_docs)
      self.rightList2.addItems(docs)

    self.draw_clusters()

  def draw_clusters(self):    
    if self.plotHidden or not self.searched:
      return

    self.plotted = True
    canvas = self.plotWidget.canvas
    canvas.ax.clear()
    canvas.ax.axis('off')
    canvas.fig.tight_layout()

    searchMethod = self.searchMethod.currentIndex()
    clusterMethod = self.clusterMethod.currentIndex()
    clusterer = self.clusterers[clusterMethod]
    if searchMethod == 0:
      selected = [item.text() for item in self.rightList.selectedItems()]
      plotter.doc2vec(canvas, self.labels, self.similar_docs, selected, self.vectors)
    elif searchMethod == 1:
      selected = [self.rightList.item(i).text() for i in range(self.rightList.count())]
      text = self.searchLine.text().strip()
      plotter.articles(canvas, clusterer, self.cluster, selected, text, self.labels, self.vectors)
    elif searchMethod == 2:
      if clusterMethod == 0:
        plotter.affinity(canvas, clusterer, self.vectors, self.cluster)
      elif clusterMethod == 1:
        plotter.kmeans(canvas, clusterer, self.vectors, self.cluster)
      elif clusterMethod == 2:
        plotter.agglomerative(canvas, clusterer, self.vectors, self.cluster)
      elif clusterMethod == 3:
        plotter.meanshift(canvas, clusterer, self.vectors, self.cluster)
      elif clusterMethod == 4:
        plotter.birch(canvas, clusterer, self.vectors, self.cluster)

  def show_clusters(self):
    if self.plotHidden:
      self.plotHidden = False
      self.clusterButton.setText('Скрыть кластеры')
      self.plotWidget.show()      
      if not self.plotted:
        self.draw_clusters()
    else:
      self.plotHidden = True
      self.clusterButton.setText('Показать кластеры')
      self.plotWidget.hide()

  def clusterer_changed(self):
    searchMethod = self.searchMethod.currentIndex() 
    clusterMethod = self.clusterMethod.currentIndex() 
    clusters = self.clusterers[clusterMethod].labels_
    self.clusters_docs = clusterization.docs2clusters(self.labels, clusters)
    if searchMethod == 2:
      groups = [self.allgroups]
      top_words = self.topics[clusterMethod]
      for topic in top_words:
        words = [self.vocab[word] for word in list(zip(*topic))[0][:10]]
        groups.append(' '.join(words))
      self.themeBox.clear()
      self.themeBox.addItems(groups)
      self.themeBox.setCurrentIndex(0)
    if searchMethod == 1 and self.searched:
      text = self.searchLine.text().strip()
      self.cluster = [c for d,c in self.clusters_docs if text == d][0]
      top_words = self.topics[clusterMethod][self.cluster]
      words = [self.vocab[word] for word in list(zip(*top_words))[0][:10]]
      self.themeText.setText(' '.join(words))
    self.draw_clusters()   

  def group_changed(self):
    self.rightList.clear()
    self.leftTable.clear()
    self.leftTable.setRowCount(0)
    self.leftTable.setHorizontalHeaderLabels(['Слово', 'Количество'])

    self.cluster = self.themeBox.currentIndex()-1
    clusterMethod = self.clusterMethod.currentIndex()    
    clusters = self.clusterers[clusterMethod].labels_
    self.clusters_docs = clusterization.docs2clusters(self.labels, clusters)
    top_words = self.topics[clusterMethod][self.cluster]
    for word in top_words:
      row = self.leftTable.rowCount()
      self.leftTable.insertRow(row)
      self.leftTable.setItem(row, 0, QtWidgets.QTableWidgetItem(self.vocab[word[0]]))
      self.leftTable.setItem(row, 1, QtWidgets.QTableWidgetItem(str(word[1])))
    self.rightList.addItems(clusterization.cluster_docs(self.cluster, self.clusters_docs))
    self.searched = True
    self.draw_clusters()

  def search_method_changed(self):
    self.searched = False
    index = self.searchMethod.currentIndex()
    if index == 0:
      self.completer.setModel(QtCore.QStringListModel([]))
      self.rightList.clear()
      self.leftTable.clear()
      self.leftTable.setRowCount(0)
      self.leftTable.setHorizontalHeaderLabels(['Слово', 'Близость'])

      self.leftTable.show()
      self.leftLabel.show()
      self.rightList.show()
      self.rightLabel.show()
      self.rightList2.hide()
      self.rightLabel2.hide()
      self.clusterLabel.hide()
      self.clusterMethod.hide()
      self.themeBox.hide()
      self.themeText.show()
      self.themeLabel.show()
      self.themeLabel2.hide()
      self.searchLabel.show()
      self.searchLine.show()
      self.searchButton.show()
    else:
      self.clusterLabel.show()
      self.clusterMethod.show()
      if index == 1:
        self.leftTable.hide()
        self.leftLabel.hide()
        self.rightList2.show()
        self.rightLabel2.show()
        self.themeBox.hide()
        self.themeText.show()
        self.themeLabel.show()
        self.themeLabel2.hide()
        self.rightList.show()
        self.rightLabel.show()
        self.searchLabel.show()
        self.searchLine.show()
        self.searchButton.show()

        self.completer.setModel(QtCore.QStringListModel(self.labels))
        self.rightList.clear()
        self.rightList2.clear()
      elif index == 2:
        self.themeBox.show()
        self.themeText.hide()
        self.leftTable.show()
        self.leftLabel.show()
        self.rightList2.hide()
        self.rightLabel2.hide()
        self.rightList.show()
        self.rightLabel.show()
        self.themeLabel2.show()
        self.themeLabel.hide()
        self.leftLabel.show()
        self.searchLabel.hide()
        self.searchLine.hide()
        self.searchButton.hide()

        self.clusterer_changed()
        self.rightList.clear()
        self.leftTable.clear()
        self.leftTable.setRowCount(0)
        self.leftTable.setHorizontalHeaderLabels(['Слово', 'Количество'])

def init_window():
  app = QtWidgets.QApplication(sys.argv)
  window = MainWindow()  
  window.show() 
  app.exec_() 

if __name__ == '__main__':  
  init_window()