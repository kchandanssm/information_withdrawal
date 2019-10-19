# coding: utf8
import plac
import random
from pathlib import Path
import spacy
import logging
from spacy.matcher import Matcher
from NER_DB import nlp_DB as DB
import en_core_web_sm

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load the default model 
db_obj = DB()
		
class NER_Model(object):
	"""docstring for NER_Model"""
	def __init__(self):
		super(NER_Model, self).__init__()
		self.number_of_iteration = 30
	
	def load_model(self, output_dir = None):
		if output_dir == None:
			self.nlp = en_core_web_sm.load()
			logger.debug("Load model form en_core_web_sm")
		if output_dir != None:
			self.nlp = spacy.load(output_dir)
		logger.debug(self.nlp)

		if 'ner' not in self.nlp.pipe_names:
			self.ner = self.nlp.create_pipe('ner')
			self.nlp.add_pipe(self.ner)
    		# otherwise, get it, so we can add labels to it
		else:
			self.ner = self.nlp.get_pipe('ner')	

	def get_traning_data(self, project_id):
		# get the traning Data for creating Model
		train_data = db_obj.get_humman_annotation_data(project_id)
		return train_data
	
	def get_entity(self, project_id):
		# get entity from database and add it in ner model
		entity_list = db_obj.get_entity_list(project_id)
		
		for key, entity in entity_list.iteritems():
			self.add_entity(entity)
		
	def add_entity(self, entity_label):
		# add entity to NLP Model
		self.ner.add_label(entity_label)

	def create_NER_model(self, train_data, output_dir = None, ner_model_name ='NLP_brain'):
		number_of_iteration = int(self.number_of_iteration)
		other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != 'ner']
		with self.nlp.disable_pipes(*other_pipes):  # only train NER
			optimizer = self.nlp.begin_training()
			for itn in range(number_of_iteration):
				random.shuffle(train_data)
				losses = {}
				for text, annotations in train_data:
					text = unicode(text, "utf-8")
					self.nlp.update([text], [annotations], sgd=optimizer, drop=0.25,
	                           losses=losses)
				logger.debug("Epoch:{}/{}".format(itn, number_of_iteration))
				logger.debug(losses)
		output_dir = 'NER_Model/'+output_dir
		if output_dir is not None:
			output_dir = Path(output_dir)

			if not output_dir.exists():
				output_dir.mkdir()
			self.nlp.meta['name'] = ner_model_name  # rename model
			self.nlp.to_disk(output_dir)
			logger.debug("Saved model to {}".format(output_dir))


	def predict_NER_model(self, input_text, output_dir, model_name, natural_entity = True):
		# predict the Entity from NER Models
		predicted_result = []
		
		self.load_model('NER_Model/'+output_dir)
		input_text = unicode(str(input_text), "utf-8")
		doc = self.nlp(input_text)
		for ent in doc.ents:
			entity_offset_dic = {}
			entity_offset_dic['keyword'] = str(ent.text)
			entity_offset_dic['tag'] = str(ent.label_)
			entity_offset_dic['start_position'] = int(ent.start_char)
			entity_offset_dic['end_position'] = int(ent.end_char)
			predicted_result.append(entity_offset_dic)
		
		if natural_entity == True:
			self.load_model()
			doc = self.nlp(input_text)
			for ent in doc.ents:
				entity_offset_dic = {}
				entity_offset_dic['keyword'] = str(ent.text)
				entity_offset_dic['tag'] = str(ent.label_)
				entity_offset_dic['start_position'] = int(ent.start_char)
				entity_offset_dic['end_position'] = int(ent.end_char)
				predicted_result.append(entity_offset_dic)
		
		return predicted_result

	def main(self, project_id, output_dir, model_name):
		# main function 
		# load NLP Model
		self.project_id = project_id
		self.load_model()
		# get/add Entity to NLP Model
		self.get_entity(self.project_id)
		# get traning date
		traning_data = self.get_traning_data(project_id)
		# create Model
		self.create_NER_model(traning_data, output_dir, model_name)
		return 'success'

if __name__ == '__main__':
	project_id = 9
	ner_model = NER_Model()
	ner_model.main(project_id,"dsd","abbc")