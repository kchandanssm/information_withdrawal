# coding: utf8
import spacy
import logging
from NER_DB import nlp_DB as DB
import en_core_web_sm

db_obj = DB()
nlp =  en_core_web_sm.load()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class pre_annotation(object):
	"""docstring for pre_annotation"""
	def generate_pre_annotation(self, text):
		# this file been used to recoginised natural entity from given text
		text = unicode(text, "utf-8")
		doc = nlp(text)
		return_data = {}
		return_data['raw_text'] = str(text)
		return_data['entity_offset'] = []
		for ent in doc.ents:
			entity_offset_dic = {}
			entity_offset_dic['keyword'] = str(ent.text)
			entity_offset_dic['tag'] = str(ent.label_)
			entity_offset_dic['start_position'] = int(ent.start_char)
			entity_offset_dic['end_position'] = int(ent.end_char)
			return_data['entity_offset'].append(entity_offset_dic)
		return return_data      

if __name__ == "__main__":
	# text = db_obj.fetch_record(136)
	pre_annotation_obj =pre_annotation()
	text = "London is a big city in the United Kingdom."
	logger.debug(pre_annotation_obj.generate_pre_annotation(text))
	


