# coding: utf8

import pymysql
import sys
import logging

reload(sys)
sys.setdefaultencoding('utf8')

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DB_HOST = "nlpbraindev.cxnmh9x3nt11.us-east-1.rds.amazonaws.com"
DB_USER = "nlpbraindev"
DB_PASSWORD = "UFDnc5Q94TptdUER"
DB_TABLE = "nlpbraindev"

class nlp_DB(object):
	# class for all database related tasks
	def __init__(self):
		super(nlp_DB, self).__init__()
		try:
			self.db = pymysql.connect(DB_HOST,
                                      DB_USER,
                                      DB_PASSWORD,
                                      DB_TABLE)
		except Exception as e:
			logger.debug(e)
			self.db = ""

	def add_user(self , Name, Email, Password, api_key, api_secret):
		query = """INSERT INTO user_details (Name ,Email, Password, api_key,api_secret)VALUES('{}','{}','{}','{}','{}')""".format(Name,Email,Password, api_key, api_secret)
		try:
		    data = self.excute_query(query)
		    return "success"
		except Exception as e:
		    logger.debug(query)
		    logger.error('Exception in Database ', exc_info=True)
		    return 'error'

	def validate_user(self, Email, Password):
		try:
		    query =  "SELECT id_user_detail FROM user_details WHERE email = '{}' and password = '{}'".format(Email,Password)
		    data = self.excute_query(query)
		    if len(data) != 0:
		        user_id = data[0][0]
		        return user_id
		    if len(data) == 0:
		        return False     
		except Exception as e:
		    return 'error'

	def excute_query(self, query):
		# excute Query
		cursor = self.db.cursor()
		try:
			logger.debug(query)
			cursor.execute(query)
			data = cursor.fetchall()
			# logger.debug(data)
			self.db.commit()
			return data
		except Exception as e:
			self.db.rollback()
			print (e)
			return 'Error'
			
	def regex_classes(self, project_id):
		return_dict = {}
		try:
			query = 'select id_rule_classes, class_name from rule_classes where id_user_category ={}'.format(project_id)
			data = self.excute_query(query)
			regex_classes = {}
			
			for i in data:
				class_id, class_name = i
				regex_classes[class_id] = class_name.encode("utf8")
			
			for class_id , class_name in regex_classes.iteritems():
				return_dict[class_name] = []
				query = "select regex from rule_regex where id_rule_classes= {} and id_user_category={} ORDER BY regex DESC".format(class_id, project_id)
				data = self.excute_query(query)
				for i in data:
					regex = i
					return_dict[class_name].append(regex[0])

			return return_dict
		except Exception as e:
			print (e)
			return 'Error'

	''' Add relationship into database'''
	def add_relationship(self, project_id, relationship_name, head_entity_id, tail_entity_id):
		query = """INSERT INTO user_relationship (id_user_category ,relationship_name, head_entity_id, tail_entity_id)VALUES({},'{}',{},{})""".format(project_id, relationship_name, head_entity_id, tail_entity_id)
		try:
		    data = self.excute_query(query)
		    return "success"
		except Exception as e:
		    logger.debug(query)
		    logger.error('Exception in Database ', exc_info=True)
		    return 'error'

	'''Add human annotated relationship into database'''
	def add_relationship_annotation(self, id_user_contain, id_relationship, head_entity_word, head_entity_start, head_entity_end, tail_entity_word, tail_entity_start, tail_entity_end):
		
		query = """INSERT INTO user_relationship_annotation (id_user_contain, id_relationship, head_entity_word, head_entity_start, head_entity_end, tail_entity_word, tail_entity_start, tail_entity_end)VALUES({},{},'{}',{},{},'{}',{},{})""".format(id_user_contain, id_relationship, head_entity_word, head_entity_start, head_entity_end, tail_entity_word, tail_entity_start, tail_entity_end)
		try:
		    data = self.excute_query(query)
		    return "success"
		except Exception as e:
		    logger.debug(query)
		    logger.error('Exception in Database ', exc_info=True)
		    return 'error'
	
	def __get_entity_name_by_id(self, entity_id):
		'''return Entity name for given entity id'''
		query = "select entity_name from user_entity where id_user_entity = {}".format(entity_id)
		try:
			data = self.excute_query(query)
			return data[0][0]
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'	    
	
	def get_all_relationship_name(self, project_id):
		returned_relationship = []
		query ="select id_relationship, relationship_name from user_relationship where id_user_category ={}".format(project_id)
		try:
			all_records = self.excute_query(query)
			for record in all_records:
				relationship_id, relationship_name = record
				relationship_dict = {}
				relationship_dict["id"] = relationship_id
				relationship_dict["name"] = relationship_name
				returned_relationship.append(relationship_dict)
				
			return returned_relationship

		except Exception as e:
			raise e

	'''Get the relationship name and head and tail entity name'''
	def get_all_relationship(self, project_id):
		return_relationships = []
		query = 'select relationship_name, head_entity_id, tail_entity_id from user_relationship where id_user_category ={}'.format(project_id)
		entity_mapping = self.__get_entity_name_mapping(project_id)
		try:
			all_records = self.excute_query(query)
			for record in all_records:
				relationship_name, head_entity_id, tail_entity_id = record 
				returned_relationship_dict = {}
				returned_relationship_dict["relationship_name"] = relationship_name

				head_entity = {}
				head_entity["name"] = entity_mapping[head_entity_id]
				head_entity["entity_id"] = head_entity_id
				returned_relationship_dict["head_entity"] = head_entity

				tail_entity = {}
				tail_entity["name"] = entity_mapping[tail_entity_id]
				tail_entity["entity_id"] = tail_entity_id
				returned_relationship_dict["tail_entity"] = tail_entity
				return_relationships.append(returned_relationship_dict)
			return return_relationships
		except Exception as e:
			logger.debug(query)
			logger.error('Exception in Database ', exc_info=True)
			return 'error'

	def get_all_content(self, project_id):
		import nltk
		content_mapping = self.__get_content_text_id_mapping(project_id)
		returned_content = []
		for id_user_contain, content in content_mapping.iteritems():
			returned_content.append(nltk.word_tokenize(content))
		return returned_content	
			
			
	def __get_relationship_name_id_mapping(self, project_id):
		# return Dictionay of relationship Id as a key and name as value
		return_relationship = {}
		relationship_head_and_tail = {}
		query= "select id_relationship, relationship_name, head_entity_id, tail_entity_id from user_relationship where id_user_category = {}".format(project_id)
		try:
			all_records = self.excute_query(query)
			for record in all_records:
				relationship_id, relationship_name, head_entity_id, tail_entity_id = record
				return_relationship[relationship_id] = relationship_name
				relationship_head_and_tail[relationship_id] = (head_entity_id, tail_entity_id)
				
			return return_relationship, relationship_head_and_tail

		except Exception as e:
			raise e	

	def __get_content_text_id_mapping(self, project_id):
		# return Dictionay of relationship Id as a key and name as value
		return_content_text_id = {}
		query= "select id_user_content, raw_content from user_content where id_user_category = {}".format(project_id)
		try:
			all_records = self.excute_query(query)
			for record in all_records:
				content_id, raw_text = record
				return_content_text_id[content_id] = raw_text
				
			return return_content_text_id

		except Exception as e:
			raise e	

		return return_content_text_id
	
	def __get_entity_name_mapping(self, project_id):
		return_entity_id = {}
		query= "select id_user_entity, entity_name from user_entity where id_user_category = {}".format(project_id)
		try:
			all_records = self.excute_query(query)
			for record in all_records:
				entity_id, entity_name = record
				return_entity_id[entity_id] = entity_name
				
			return return_entity_id

		except Exception as e:
			raise e	

		return return_entity_id
	
	def get_rel2id(self, project_id):
		# return Dictionay of relationship Id as a key and name as value
		return_relationship = {}
		query= "select id_relationship, relationship_name from user_relationship where id_user_category = {}".format(project_id)
		try:
			all_records = self.excute_query(query)
			i = 1
			return_relationship["NA"] = 0
			for record in all_records:
				relationship_id, relationship_name = record
				return_relationship[relationship_name] = i
				i += 1
			return return_relationship
		except Exception as e:
			raise e		
		
	'''Extract Relationship from database and convert it into JSON formate'''
	def extract_relationship(self, project_id):
		# need four things 
		# 1. Head entity word
		# 2. Relationship_name
		# 3. tail entity word
		# 4. Content

		final_data = []
		relationship_mapping, relationship_head_and_tail = self.__get_relationship_name_id_mapping(project_id)
		content_mapping = self.__get_content_text_id_mapping(project_id)
		entity_mapping = self.__get_entity_name_mapping(project_id)
		query ="select id_user_contain, id_relationship, head_entity_word, tail_entity_word from user_relationship_annotation where id_user_contain in (select id_user_content from user_content where id_user_category = {})".format(project_id)
		try:
			all_records = self.excute_query(query)
			for record in all_records:
				id_user_contain, id_relationship, head_entity_word, tail_entity_word = record
				final_dict = {}
				head_entity = {}
				tail_entity = {}
				if id_user_contain in content_mapping:
					final_dict["sentence"] = content_mapping[id_user_contain]
				if id_relationship in relationship_mapping:
					final_dict["relation"] = relationship_mapping[id_relationship]
				if id_relationship in relationship_head_and_tail:
					head_entity_id, tail_entity_id = relationship_head_and_tail[id_relationship]	
					head_entity["id"] = str(head_entity_id)
					tail_entity["id"] = str(tail_entity_id)
					if head_entity_id in entity_mapping:
						head_entity["type"] = entity_mapping[head_entity_id]
					if tail_entity_id in entity_mapping:
						tail_entity["type"] = entity_mapping[tail_entity_id]
				
				head_entity["word"] = head_entity_word
				tail_entity["word"] = tail_entity_word
				
				final_dict["head"] = head_entity
				final_dict["tail"] = tail_entity

				final_data.append(final_dict)
				
			return final_data

		except Exception as e:
			raise e	

	def regex_classes_all(self, project_id):
		return_list = []
		try:
			query = 'select id_rule_classes, class_name from rule_classes where id_user_category ={}'.format(project_id)
			data = self.excute_query(query)

			regex_classes = {}
			for i in data:
				return_class_dict = {}
				class_id, class_name = i
				return_class_dict['class_id'] = class_id
				return_class_dict['class_name'] = class_name.encode("utf8")
				return_class_dict['all_regex'] = []
				
				query = "select regex from rule_regex where id_rule_classes= {} and id_user_category={} ORDER BY regex DESC".format(class_id, project_id)
				data = self.excute_query(query)
				for i in data:
					regex = i
					return_class_dict['all_regex'].append(regex[0])
				return_list.append(return_class_dict)	
			return return_list
		except Exception as e:
			print (e)
			return 'Error'			
	
	def all_rules_regex(self, project_id):
		return_list = []
		try:
			query = 'SELECT id_rule_rules, rule_name from rule_rules where id_user_category = {}'.format(project_id)
			data = self.excute_query(query)
			regex_classes = {}
			for i in data:
				return_class_dict = {}
				rule_id, rule_name = i
				return_class_dict['rule_id'] = rule_id
				return_class_dict['rule_name'] = rule_name.encode("utf8")
				return_class_dict['rule_regex'] = []
				
				query = "select * from user_rule_collections where id_rule_rules= {} and id_user_category={} ".format(rule_id, project_id)
				data = self.excute_query(query)
				for i in data:
					(rule_collection_id, id_tab_project, rule_id, position, text, is_regex, class_id, is_assigned, assigned_class_id) = i
					# print(i)
					rule_dict = {}
					rule_dict['position'] = position
					rule_dict['text'] = text
					if is_assigned == 0:
						rule_dict['is_assigned'] = False
					if is_assigned == 1:
						rule_dict['is_assigned'] = True
					rule_dict['assigned_class_id'] = assigned_class_id
					if is_regex == 0:
						rule_dict['is_regex'] = False
					if is_regex == 1:
						rule_dict['is_regex'] = True	
					rule_dict['class_id'] = class_id
					return_class_dict['rule_regex'].append(rule_dict)
				return_list.append(return_class_dict)	
			return return_list
		except Exception as e:
			print (e)
			return 'Error'			
	
	def all_classes(self, project_id):
		# fetch all data from database
		content_all_data = []
		try:
			query = "select id_rule_classes, class_name from rule_classes where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			for dat in data:
				class_id, class_name = dat
				dic_content = {}
				dic_content['class_id'] = class_id
				dic_content['class_name'] = class_name.encode("utf8")
				content_all_data.append(dic_content)
			return content_all_data
		except Exception as e:
			print (e)
			return 'Error'
		
	def all_regex_by_class(self, project_id, class_id):
		# fetch all data from database
		content_all_data = []
		try:
			query = "select id_rule_regex,regex from rule_regex where id_user_category = {} and id_rule_classes = {}".format(project_id, class_id)
			data = self.excute_query(query)
			for dat in data:
				regex_id, regex = dat
				dic_content = {}
				dic_content['regex_id'] = regex_id
				dic_content['regex'] = regex.encode("utf8")
				content_all_data.append(dic_content)
			return content_all_data
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
	
	def all_rules(self, project_id):
		# fetch all data from database
		content_all_data = []
		try:
			query = "select id_rule_rules, rule_name from rule_rules where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			for dat in data:
				rule_id, rule_name = dat
				dic_content = {}
				dic_content['rule_id'] = rule_id
				dic_content['rule_name'] = rule_name.encode("utf8")
				content_all_data.append(dic_content)
			return content_all_data
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def rule_based_add_class(self, project_id, class_name):
		# add rules in database
		query = """INSERT INTO rule_classes (id_user_category, class_name) VALUES ({}, '{}')""".format(project_id, class_name)
		try:
			data = self.excute_query(query)
			return "success"
		except Exception as e:
			logger.debug(query)
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'

	def get_class_name(self, project_id, class_id):
		# Get class name from classid 
		try:
			query = "select class_name from rule_classes where id_user_category = {} and id_rule_classes = {}".format(project_id, class_id)
			data = self.excute_query(query)
			return data[0][0]
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def rule_based_add_regex(self, project_id, class_id, regex):
		# get regex of given class id from database
		query = """INSERT INTO rule_regex (id_user_category, id_rule_classes, regex) VALUES ({}, {},'{}')""".format(project_id, class_id, regex)
		try:
			data = self.excute_query(query)
			return "success"
		except Exception as e:
			logger.debug(query)
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
	
	def update_training_data_classification(self, url, category):
		# get the updated traning data for classification
		try:
			query = "UPDATE classification_data SET category = '" + category + "' WHERE url = '" + url + "'"
			data = self.excute_query(query)
			return "success"
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def insert_training_data_classification(self, raw_text, category, user_id):
		# insert traning data for classfication
		
		raw_text = raw_text.encode('ascii', 'ignore')
		raw_text = raw_text.replace("'","")
		query = """INSERT INTO classification_data (raw_text, category, id_user_detail) VALUES ('{}', '{}', {})""".format(raw_text, category, user_id)
		try:
			data = self.excute_query(query)
			return "success"
		except Exception as e:
			logger.debug(query)
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def check_traning_data_classifcation(self, raw_text):
		try:
			query= "select * from classification_data where raw_text = '{}'".format(raw_text)
			data = self.excute_query(query)
			length = int(len(data))
			if length == 0:
				return True
			if length >= 1:
				return False
			
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)

		return True
			
	def add_training_data_classification(self, url, raw_text, category, user_id):
		cursor = self.db.cursor()
		if self.check_traning_data_classifcation(url):
			try:
				query = "INSERT INTO classification_data (url, raw_text, category, id_user_detail) VALUES ('{}', '{}', '{}', {})".format(url, raw_text, category, user_id)
				data = self.excute_query(query)
				return "success"
			except Exception as e:
				logger.error('Exception in Database ', exc_info=True)
				return 'Error'
		
	def get_training_data_classification(self, user_id):
		try:
			query = "select raw_text, category from classification_data where id_user_detail = {}".format(user_id)
			data = self.excute_query(query)
			
		except Exception as e:
			self.db.rollback()
			logger.error('Exception in Database ', exc_info=True)

		all_raw_text = []
		all_categorys = []
		key = 0
		for dat in data:
			raw_text, category = dat
			all_raw_text.append(raw_text.decode('unicode_escape'))
			all_categorys.append(category)
			
		return all_raw_text, all_categorys

	def show_project_records(self, user_id):
		entity_list=[]
		try:
			query = 'select id_user_category, category_name, description  from user_category where id_user_detail = {}'.format(user_id)
			data = self.excute_query(query)
			return data		
		except:
			return "Exception in record insertion"

	def get_project_name(self, project_id):
		entity_list=[]
		try:
			query = "select category_name from user_category where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			return data[0][0]		
		except:
			# print ("Exception in record insertion")		
			return "Exception in record insertion"   

	def get_project_id(self, project_name, project_description):
		cursor = self.db.cursor()
		entity_list=[]
		try:
			query = "select id_user_category from user_category where category_name = '{}' and description = '{}'".format(project_name, project_description)
			data = self.excute_query(query)
			return data[0][0]		
		except:
			return "Exception in record insertion"   

	def get_project_id_by_name(self, project_name):
		cursor = self.db.cursor()
		entity_list=[]
		try:
			query = "select id_user_category from user_category where category_name = '{}'".format(project_name)
			data = self.excute_query(query)
			return data[0][0]		
		except:
			return "Exception in record insertion"   

	def add_human_annotation_data(self, project_id, content_id, entity_offset):
		try:
			for key, value in entity_offset.iteritems():
				query= "INSERT INTO human_annotation (id_user_category, id_user_content, id_user_entity, start_position, end_position, keyword) VALUES({}, {},{},{},{},'{}')".format(project_id, content_id, value['tag'], value['start_position'], value['end_position'], '')
				data = self.excute_query(query)
			return len(data)
		except Exception as e:
				logger.error('Exception in Database ', exc_info=True)

	# get the human annotation dataset
	def get_annotated_data(self, content_id):

		all_annoted_entity_list = []
		query = "select id_user_entity, start_position, end_position from human_annotation where id_user_content = {} ".format(content_id)
		try:
			all_data = self.excute_query(query)
			content_all_data = self.get_contain_detail(content_id)
			raw_text = content_all_data[0]["raw_content"]
			for data in all_data:
				id_user_entity, start_position, end_position = data
				annoted_dict = {}
				annoted_dict["id"] = id_user_entity
				annoted_dict["name"] = str(raw_text[start_position:end_position])
				annoted_dict["entity_name"] = self.__get_entity_name_by_id(id_user_entity)
				annoted_dict["start"] = start_position
				annoted_dict["end"] = end_position
				all_annoted_entity_list.append(annoted_dict)
			return all_annoted_entity_list	
		except Exception as e:
			raise e

    # Retirve Humman annotation dataset from Database 
	def get_humman_annotation_data(self, project_id):
		entity_list = self.get_entity_list(project_id)
		content_list = self.get_content_list(project_id) 
		final_result = {}
		try:
			query = "select id_user_content, id_user_entity, start_position,end_position from human_annotation where id_user_content in (select id_user_content from user_content where id_user_category = {})".format(project_id)
			all_data = self.excute_query(query)
			for data in all_data:
				id_tab_content, id_entity, start_pos,end_pos = data
				if content_list[id_tab_content] not in final_result:
					final_result[content_list[id_tab_content]] = []
					insert_tuple = (start_pos, end_pos, entity_list[id_entity])
					final_result[content_list[id_tab_content]].append(insert_tuple)
				else:
					insert_tuple = (start_pos, end_pos, entity_list[id_entity])
					final_result[content_list[id_tab_content]].append(insert_tuple)
			finalll_list = []	
			for key, value in final_result.iteritems():
				entity_dic = {}
				entity_dic['entities'] = value
				final_tupple = (key, entity_dic)
				finalll_list.append(final_tupple)
						
			return finalll_list
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'

	def add_project(self, project_name, project_description, user_id):
		try:
			query= "INSERT INTO user_category (category_name, description, id_user_detail) VALUES ('{}', '{}', {})".format(project_name, project_description, user_id)
			data = self.excute_query(query)
			return len(data)
		except Exception as e:
				logger.error('Exception in Database ', exc_info=True)
	
	def get_contain_detail(self, content_id):
		content_all_data = []
		query = "select id_user_content, content_title, raw_content from user_content where id_user_content = {}".format(content_id)
		try:
			data = self.excute_query(query)
			for dat in data:
					id_tab_content, content_title, raw_content = dat
					dic_content = {}
					dic_content['id_tab_content'] = id_tab_content
					dic_content['content_title'] = content_title.encode("ascii","ignore")
					dic_content['raw_content'] = raw_content.encode("ascii","ignore")
					content_all_data.append(dic_content)
			return content_all_data
		except Exception as e:
				logger.error('Exception in Database ', exc_info=True)	

	def get_pre_annotation_data(self, project_id, content_id = None):
		# Retive pre-annotation data 
		if content_id != None:
			entity_offset = []
			try:
				content_all_data = self.get_contain_detail(content_id)
				query = "select keyword, tag, start_position, end_position from pre_annotation where id_user_category = {} and id_user_content = {} order by start_position".format(project_id, content_id)
				data = self.excute_query(query)
				for dat in data:
					keyword, tag, start_position, end_position= dat
					dic_content = {}
					dic_content['keyword'] = keyword
					dic_content['tag'] = tag
					dic_content['start_position'] = start_position
					dic_content['end_position'] = end_position
					entity_offset.append(dic_content)

				return content_all_data, entity_offset
			except Exception as e:
				logger.error('Exception in Database ', exc_info=True)
				return 'Error'
			
	def get_regex_class(self, project_id):
		content_all_data = []
		query = """SELECT rule_classes.class_name, rule_regex.regex
					FROM rule_regex
					INNER JOIN rule_classes ON rule_classes.id_rule_classes = rule_regex.id_rule_classes
					where rule_regex.id_user_category={}""".format(project_id)
		try:
			data = self.excute_query(query)
			dic_content = {}
			for dat in data:
				class_name, regex = dat
				if class_name not in dic_content:
					dic_content[class_name] = []
					dic_content[class_name].append(regex)
				else:
					dic_content[class_name].append(regex)
			content_all_data.append(dic_content)
			return content_all_data
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def content_all_data(self, project_id):
		# fetch all data from database
		content_all_data = []
		try:
			query = "select id_user_content, content_title, raw_content from user_content where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			for dat in data:
				id_tab_content, content_title, raw_content = dat
				dic_content = {}
				dic_content['id_tab_content'] = id_tab_content
				dic_content['content_title'] = content_title.encode("utf8")
				dic_content['raw_content'] = str(raw_content.encode("ASCII", 'ignore'))
				content_all_data.append(dic_content)
			return content_all_data
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def get_content_list(self, project_id):
		# fetch all data from database
		content_list = {}
		try:
			query = "select id_user_content,raw_content  from user_content where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			for entity_name in data:
				id_tab_content, raw_content = entity_name
				content_list[id_tab_content] = raw_content
			return content_list
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
		
	def get_entity_list(self, project_id):
		# fetch all data from database
		entity_list = {}
		try:
			query = "select id_user_entity, entity_name from user_entity where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			for entity_name in data:
				entity_id, entity_name = entity_name
				entity_list[entity_id] = entity_name
			return entity_list
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
	
	def insert_ner_result_in_training(self, project_id, title, raw_text, entity_offset):
		# add ner result in Database
		try:
			# add raw text in database
			content_id = db_obj.insert_record_content(project_id, title, text)
			return len(data)
			# add entity_offset in Database


		except Exception as e:
				logger.error('Exception in Database ', exc_info=True)

		pass

	def insert_record_content(self, project_id, title, raw_text):
		try:
			query= "INSERT INTO user_content (id_user_category, content_title, raw_content) VALUES({}, '{}','{}')".format(project_id, title, raw_text)
			data = self.excute_query(query)
			return len(data)
		except Exception as e:
				logger.error('Exception in Database ', exc_info=True)

	def add_entity_record(self, project_id, entity_name):
		try:
			query= "INSERT INTO user_entity(id_user_category,entity_name) VALUES({},'{}')".format(project_id, entity_name)
			data = self.excute_query(query)
			return len(data)
		except Exception as e:
				logger.error('Exception in Database ', exc_info=True)

	def show_entiy_records(self, project_id):
		entity_list=[]
		try:
			query = 'SELECT entity_name FROM user_entity where id_user_category = {}'.format(project_id)
			data = self.excute_query(query)
			return data		
		except:
			return "Exception in record insertion"    

	def insert_record_pre_annotation(self, project_id, content_id, entity_offset):
		# self.insert_record_pre_annotation_(project_id, content_id)
		for entity in entity_offset:
			keyword = entity['keyword']
			start_position = entity['start_position']
			end_position = entity['end_position']
			tag = entity['tag']
			try:
				query= "INSERT INTO pre_annotation(id_user_category, id_user_content,keyword,tag, start_position, end_position) VALUES({},{},'{}','{}', {}, {})".format(project_id, content_id, keyword, tag, start_position, end_position)
				data = self.excute_query(query)
			except Exception as e:
				logger.error('Exception in Database ', exc_info=True)
		
	def check_record_pre_annotation(self, project_id, content_id):
		try:
			query= "SELECT count(*) from pre_annotation where id_user_category = {} and id_user_content = {}".format(project_id, content_id)
			data = self.excute_query(query)
			print(data)
			length = int(data[0][0])
			print(length)
			if length == 0:
				return True
			if length >= 1:
				return False
			
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)

	def add_rule_name(self, project_id, rule_name):
		try:
			query= "INSERT INTO rule_rules(id_user_category, rule_name) VALUES({},'{}')".format(project_id, rule_name)
			data = self.excute_query(query)
			length = int(len(data))
			if length == 0:
				return True
			if length >= 1:
				return False
			
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)		

	def insert_rule_db(self, project_id, rule_json):
		rule_id = rule_json['rule_id']
		for rule in rule_json['rule_regex']:
			try:
				position = rule['position']
				text_ = rule['text']
				is_regex = rule['is_regex']
				class_id = rule['class_id']
				is_assigned = rule['is_assigned']
				assigned_class_id = rule['assigned_class_id']

				query = "INSERT INTO user_rules(id_user_category, id_rule_rules, position, collection_text, is_regex, id_rule_classes, is_assigned, assigned_class_id) VALUES({},{}, {},'{}',{}, {},{},{})".format(project_id, rule_id, position, text_, is_regex, class_id, is_assigned, assigned_class_id)
				data = self.excute_query(query)
				
			except Exception as e:
				logger.error('Exception in Database ', exc_info=True)		
	
	def insert_entity_rule_mapping(self, project_id, entity_class_mapping):
		for entity_id, class_id in entity_class_mapping.iteritems():
			try:
				query = "INSERT INTO entity_class(id_user_category, id_user_entity, id_rule_classes) VALUES({},{}, {})".format(project_id, entity_id, class_id)
				data = self.excute_query(query)
				
			except Exception as e:
				logger.error('Exception in Database ', exc_info=True)			

	def get_entity_rule_mapping(self, project_id):
		entity_list = {}
		try:
			query = "select id_user_entity, id_rule_classes from entity_class where id_user_category = {}".format(project_id)
			data = self.excute_query(query)
			for entity_name in data:
				entity_id, class_id = entity_name
				entity_list[entity_id] = class_id
			return entity_list
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'

	def get_user_id_from_api_key(self, api_key, api_secret):
		try:
			query = "select user_id from user_details where api_key = '{}' and api_secret = '{}'".format(api_key, api_secret)
			data = self.excute_query(query)
			print(data)
			if len(data) > 0:
				return data[0][0]
			if len(data) == 0:
				return False
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'

	def get_api_key_secret_by_user_id(self, user_id):
		try:
			query = "select api_key, api_secret from user_details where  id_user_detail = {}".format(user_id)
			data = self.excute_query(query)
			print(data)
			if len(data) > 0:
				api_key, api_secret = data[0]
				return api_key, api_secret
			if len(data) == 0:
				return False
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)
			return 'Error'
	
	def fetch_record(self, content_id):
		# this is been used to fetch all recod from database
		try:
			query = "SELECT content_title, raw_content FROM user_content WHERE id_user_content={}".format(content_id)
			data = self.excute_query(query)
			return data[0][0], data[0][1]			
		except Exception as e:
			logger.error('Exception in Database ', exc_info=True)

if __name__ == '__main__':
	nlp_obj = nlp_DB()
	project_id = 43
	relationship_extraction = nlp_obj.get_rel2id(project_id)
	import json

	with open('rel2id.json', 'w') as fp:
		json.dump(relationship_extraction, fp, indent=4)