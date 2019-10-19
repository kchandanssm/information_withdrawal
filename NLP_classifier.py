# coding: utf8

import os
import requests
import logging
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from NER_DB import nlp_DB
from sklearn.linear_model import SGDClassifier
import numpy as np
import pickle
from goose import Goose
import random
import sys
import nltk
from nltk.stem.lancaster import LancasterStemmer
import tflearn
import tensorflow as tf
from sklearn.model_selection import train_test_split
import json
import ast
from sklearn.model_selection import train_test_split

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

gooser = Goose()
nlp_DB_obj = nlp_DB()
count_vect = CountVectorizer()
tfidf_transformer = TfidfTransformer()
ignore_words = ['?']
stemmer = LancasterStemmer()

class nlp_classifer(object):
	"""docstring for nlp_classifer"""

	def __init__(self):
		self.fileName = 'finalized_model.sav'
	
	def retrain_model(self, user_id):
		# start re- traning the model
		accuray = self.SGD_classifer(user_id)
		return accuray
		
	def tfidf_transform(self, train_data):
		X_train_counts = count_vect.fit_transform(train_data)
		X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
		return X_train_tfidf

	def SGD_classifer(self, user_id):
		train_data, train_data_category, test_data, test_data_category = self.getData(user_id)
		X_train_tfidf = self.tfidf_transform(train_data)
		clf = SGDClassifier().fit(X_train_tfidf, train_data_category)
		pickle.dump(clf, open('classification_model/'+str(user_id), 'wb'))

		X_new_counts = count_vect.transform(test_data)
		X_test_tfidf = tfidf_transformer.transform(X_new_counts)
		predicted = clf.predict(X_test_tfidf)
		logger.debug("SGD Classifier Result")

		result = str(np.mean(predicted == test_data_category))

		return result
	
	def SGD_prediction(self, text, user_id):
		clf = pickle.load(open('classification_model/'+str(user_id), 'rb'))
		docs_new = []
		docs_new.append(text)
		X_new_counts = count_vect.transform(docs_new)
		X_test_tfidf = tfidf_transformer.transform(X_new_counts)		
		predicted = clf.predict(X_test_tfidf)
		logger.debug(predicted)
		return predicted[0]

	def prediction(self, url, predicted_text, user_id):
		# predict the category for given text
		
		predicted_result = self.SGD_prediction(predicted_text, user_id)
		nlp_DB_obj.add_training_data_classification(url, predicted_text, predicted_result, user_id)
		return predicted_result
	
	def getData(self, user_id):
		raw_text, all_category = nlp_DB_obj.get_training_data_classification(user_id)
		train_data, test_data, train_data_category, test_data_category = train_test_split(raw_text, all_category, test_size=0.22, random_state=42)
		return train_data, train_data_category, test_data, test_data_category

	def predict_tf_model(self, predicted_text, user_id):
		# load model and predicted the text
		words_new, X_dim, y_dim = nlp_DB_obj.get_BOW(user_id)
		net = tflearn.input_data(shape=[None, X_dim])
		net = tflearn.fully_connected(net, 8)
		net = tflearn.fully_connected(net, 8)
		net = tflearn.fully_connected(net, y_dim, activation='softmax')
		net = tflearn.regression(net)

		# Define model and setup tensorboard
		model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
		model.load(str(user_id))

		words = ast.literal_eval(words_new)
		bag = []
		pattern_words = predicted_text
		pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
		# create our bag of words array
		for w in words:
		    bag.append(1) if w in pattern_words else bag.append(0)
		return model.predict_label(bag)

	def train_tflearn_model(self, user_id):
		X_train, X_test, y_train, y_test = self.getData_tf(user_id)
		tf.reset_default_graph()
		# Build neural network
		net = tflearn.input_data(shape=[None, len(X_train[0])])
		net = tflearn.fully_connected(net, 8)
		net = tflearn.fully_connected(net, 8)
		net = tflearn.fully_connected(net, len(y_train[0]), activation='softmax')
		net = tflearn.regression(net)

		# Define model and setup tensorboard
		model = tflearn.DNN(net, tensorboard_dir='tflearn_logs')
		# Start training (apply gradient descent algorithm)
		model.fit(X_train, y_train, n_epoch=50, batch_size=8, show_metric=True, validation_set=(X_test, y_test))
		model.save(str(user_id))
		print("Model Saved at {}".format(str(user_id)))
		model.load(str(user_id))

		return 
		
	def getData_tf(self, user_id):
		raw_text, all_category = nlp_DB_obj.get_training_data_classification(user_id)
		c = list(zip(raw_text, all_category))
		random.shuffle(c)
		raw_text, all_category = zip(*c)
		words = []
		classes = []
		documents = []

		# loop through each sentence in our intents patterns and store data in documents and classes
		for data in c:
			raw_text, category =  data
			w = nltk.word_tokenize(raw_text)
			documents.append((w, category))
			if category not in classes:
				classes.append(category)
			words.extend(w)
		
		# stem and lower each word and remove duplicates
		words = [stemmer.stem(w.lower()) for w in words if w not in ignore_words]
		words = sorted(list(set(words)))
		classes = sorted(list(set(classes)))
		
		
		print(len(documents), "documents")
		print(len(classes), "classes", classes)
		print(len(words), "unique stemmed words", words)

		# create our training data
		training = []
		output = []
		output_empty = [0] * len(classes)

		# training set, bag of words for each sentence
		for doc in documents:
		    bag = []
		    pattern_words = doc[0]
		    pattern_words = [stemmer.stem(word.lower()) for word in pattern_words]
		    # create our bag of words array
		    for w in words:
		        bag.append(1) if w in pattern_words else bag.append(0)

		    # output is a '0' for each tag and '1' for current tag
		    output_row = list(output_empty)
		    output_row[classes.index(doc[1])] = 1

		    training.append([bag, output_row])

		# shuffle our features and turn into np.array
		random.shuffle(training)
		training = np.array(training)
		X = list(training[:, 0])
		y = list(training[:, 1])
		X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
		response = nlp_DB_obj.add_BOW(user_id, str(words), len(X_train[0]), len(y_train[0]))
		return X_train, X_test, y_train, y_test

if __name__ == '__main__':
	nlp_api_obj = nlp_classifer()
	user_id = 37
	response = nlp_api_obj.train_tflearn_model(user_id)
	check_text = "Show me the campaign name whose amount is 40000"
	print nlp_api_obj.predict_tf_model(check_text, user_id)


	# url = "http://www.thehindubusinessline.com/money-and-banking/oaknorth-bank-gets-rs-1328-cr-investment/article9902032.ece"
	# response = nlp_api_obj.retrain_model()
	# response = nlp_api_obj.prediction(url)
	# print response