# -*- coding: utf-8 -*-

# standart libraries 
from flask import Flask, request, make_response, render_template, session, url_for, flash
from flask import url_for, redirect, send_from_directory, Response, jsonify
from werkzeug import secure_filename
import logging
import io
import csv
import re
from pprint import pprint
import feedparser
import json
import sys  
from functools import wraps
from gevent.pywsgi import WSGIServer

# custom files
from NER_DB import nlp_DB as DB
from pre_annotation import pre_annotation 
from extracter import text_extractor 
from NER_Model import NER_Model
from NLP_classifier import nlp_classifer as classifer 
from rule_based_model import rule_based_model
from regex_apply import regex_rule_based
import utils

reload(sys)
sys.setdefaultencoding('utf8')

app = Flask(__name__, static_url_path='/static')
app.secret_key = '123456ABC123456'

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# create Object of other classes
rule_baed_model_obj = rule_based_model()
regex_rule_based_obj = regex_rule_based()
ner_model = NER_Model()
extractor_obj = text_extractor()
pre_annotation_obj =pre_annotation()
db_obj = DB()
classifier_obj = classifer()

# Encoded the given CSV data into UTF-8 format
def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

def check_user_session(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('signup_page'))
    return wrap

def get_project_id_session():
	# return current project id in session 
	project_id = ""
	# else return default session id
	return project_id

# NLP Brain Home page
@app.route("/")
def home_page():
	return render_template('signup.html')

@app.route('/signup_page', methods = ['POST', 'GET'])
def signup_page():
	return render_template('signup.html')

@app.route('/signup', methods = ['POST', 'GET'])
def Signup():
	if request.method == 'POST':
		name = request.form['Name']
		email = request.form['Email']
		password = request.form['Password']
		api_key = "123456"
		api_secret = "ABCDEF"
		add_user = db_obj.add_user(name, email, password, api_key, api_secret)
	return render_template('signup.html')

@app.route('/login_page', methods = ['POST', 'GET'])
def login_page():
	return render_template('Login.html')

@app.route('/Login', methods = ['POST' ,'GET'])
def Logined():
	if request.method == 'POST':
		Email = request.form['Email']
		Password = request.form['password']
		validation_response = db_obj.validate_user(Email, Password)
		if validation_response == False:
			print("Invalid user_credential")
			return redirect('login_page')
		
		if validation_response != False:
			user_id = validation_response
			print("user Id: {}".format(user_id))	
			session['user_id'] = user_id
			return redirect('NER_home')

#Logout 
@app.route('/logout', methods =['POST', 'GET'])
def Logout():
	session.clear()
	return redirect('login_page')

# NER Home page
@app.route('/NER_home')
@check_user_session
def show_project():
	user_id = int(session['user_id'])
	project_list=db_obj.show_project_records(user_id)
	return render_template('NER_home.html',project_list=project_list)

@app.route('/user_setting_page')
@check_user_session
def user_setting():
	user_id = int(session['user_id'])
	# get api key and secret from user id
	api_key, api_secret = db_obj.get_api_key_secret_by_user_id(user_id)

	return render_template('user_setting.html',api_key=api_key, api_secret=api_secret)

# Create New project 
@app.route('/project_creation', methods=['POST', 'GET' ])
@check_user_session
def project_creation():
	user_id = int(session['user_id'])
	project_name = str(request.args.get('project_name'))
	description_name = str(request.args.get('project_description'))
	rowcount=db_obj.add_project(project_name, description_name, user_id)
	if rowcount>0:
		logger.debug("Record Inserted")
	project_id = db_obj.get_project_id(project_name, description_name)
	entity_list=db_obj.show_entiy_records(project_id)
	return render_template('show_entity.html',entityList=entity_list)

# Activate previous project in server
@app.route('/active_project')
@check_user_session
def active_project():
	user_id = int(session['user_id'])
	project_id = int(request.args.get('project_id'))
	session['project_id'] = project_id
	entity_list=db_obj.show_entiy_records(project_id)
	entity_name = str(request.args.get('entityName'))
	return render_template('show_entity.html',entityList=entity_list)

# NLP Text classifcation home page
@app.route('/classification_home_page')
@check_user_session
def classification_home_page():
	return render_template('classification_home.html')

# Upload Classifcation data in Database HTML Page
@app.route('/upload_classification_page')
@check_user_session
def classification_upload_data_page():
	return render_template('classification_upload_data.html')

# Upload Classifcation data in Database
@app.route('/classification_upload_data', methods=["POST"])
@check_user_session
def classification_upload_data():
	f = request.files['data_file']
	user_id = int(session['user_id'])
	
	if not f:
		return "No file"
	stream = io.StringIO(f.stream.read().decode("utf8"), newline=None)
	csv_input = csv.reader(utf_8_encoder(stream))
	classification_data = {}
	for row in csv_input:
		raw_text = row[0]
		category = row[1]
		if category in classification_data:
			classification_data[category].append(raw_text)
		if category not in classification_data:
			classification_data[category] = []
			classification_data[category].append(raw_text)	
		db_obj.insert_training_data_classification(row[0], row[1], user_id)
	# pprint(classification_data)
	for key in classification_data:
		db_obj.add_project(key, "", user_id)
	project_list=db_obj.show_project_records(user_id)
	project_dict = {}
	for project in project_list:
		project_id, project_name, project_description = project
		project_dict[project_id] = project_name

	for key, values in project_dict.iteritems():
		project_id = key
		if values in classification_data:
			i = 0
			for raw_text in classification_data[values]:
				i += 1
				title = str(values)+"_"+str(i)
				db_obj.insert_record_content(project_id, title, raw_text)
	return render_template('classification_upload_data.html')

# Train the Classifcation HTML page
@app.route('/train_classification_page')
@check_user_session
def classification_train_model_page():
	return render_template('classification_train_model.html')

# Start text classification model
@app.route('/classification_train_model')
@check_user_session
def classification_train_model():
	user_id = int(session['user_id'])
	response = classifier_obj.retrain_model(user_id)
	return response

# Create New entity in NLP Brain 
@app.route('/entity_creation', methods=['POST', 'GET' ])
@check_user_session
def entity_creation():
	user_id = int(session['user_id'])
	entity_name = str(request.args.get('entityName'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	rowcount=db_obj.add_entity_record(project_id, entity_name)
	if rowcount>0:
		logger.debug("Record Inserted")
	entity_list=db_obj.show_entiy_records(project_id)	
	return render_template('show_entity.html',entityName = entity_name,entityList=entity_list)

# return list of all entities in given project 
@app.route('/show_entity')
@check_user_session
def show_entity():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	entity_list=db_obj.show_entiy_records(project_id)
	return render_template('show_entity.html',entityList=entity_list)

# Upload Data for processing 
# Add raw text in project 
@app.route('/add_data_text')
@check_user_session
def add_data_text():
	user_id = int(session['user_id'])
	title = str(request.args.get('title'))
	content = str(request.args.get('content'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	extractor_obj.add_text_title(project_id, title, content)
	# content_all_data = db_obj.content_all_data(project_id)
	return redirect('all_data_list')

# upload date in database via a URL
@app.route('/add_data_URL')
@check_user_session
def add_data_URL():
	user_id = int(session['user_id'])
	url = str(request.args.get('url'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1

	# Use exractor for fetch data from given url
	extractor_obj.add_text_url(project_id, url)
	content_all_data = db_obj.content_all_data(project_id)
	return redirect('all_data_list')

# upload data in database from RSS feed
@app.route('/add_rss_feed')
@check_user_session
def add_rss_feed():
	user_id = int(session['user_id'])
	rss_url = str(request.args.get('rss_feed'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	extractor_obj.add_text_RSS_Feed(project_id, rss_url)
	content_all_data = db_obj.content_all_data(project_id)
	return redirect('all_data_list')

# Upload CSV data in Database
@app.route('/add_csv_data', methods=["POST"])
@check_user_session
def add_csv_data():
	f = request.files['data_file']
	user_id = int(session['user_id'])
	
	if not f:
		return "No file"
	stream = io.StringIO(f.stream.read().decode("utf8"), newline=None)
	csv_input = csv.reader(utf_8_encoder(stream))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	for row in csv_input:
		title = row[0]
		content = row[1]
		extractor_obj.add_text_title(project_id, title, content)
	return redirect('all_data_list')

# display html page of all data with pre annotation 
@app.route('/all_pre_annotation_list')
@check_user_session
def all_pre_annotation_list():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	content_all_data = db_obj.content_all_data(project_id)
	return render_template("all_pre_annotation_list.html", content_all_data = content_all_data)

# pre annotation of the one article at one time 
@app.route('/pre_annotation')
@check_user_session
def pre_annotation():
	user_id = int(session['user_id'])
	# Fetch pre annotation data for Human annotation
	content_id = str(request.args.get('content_id'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	title, raw_text = db_obj.fetch_record(content_id)
	response = pre_annotation_obj.generate_pre_annotation(raw_text)
	if db_obj.check_record_pre_annotation(project_id, content_id):
		db_obj.insert_record_pre_annotation(project_id, content_id, response['entity_offset'])
	return redirect('human_annotation?content_id={}'.format(content_id))

# return list of all data in given project_id
@app.route('/all_data_list')
@check_user_session
def all_data_list():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	content_all_data = db_obj.content_all_data(project_id)
	return render_template("all_document_list.html", content_all_data = content_all_data)

# return the detail of raw data in given content id
@app.route('/data_detail')
@check_user_session
def data_detail():
	user_id = int(session['user_id'])
	# Fetch pre annotation data for Human annotation
	content_id = str(request.args.get('content_id'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	title, raw_text = db_obj.fetch_record(content_id)
	return render_template("data_detail.html", raw_text = raw_text, title = title)

# list of all human annotation 
@app.route('/all_human_annotation_list')
@check_user_session
def all_document_list():
	user_id = int(session['user_id'])
	# get list of all data for Human annotation
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	content_all_data = db_obj.content_all_data(project_id)
	return render_template("all_document_list.html", content_all_data = content_all_data)

# Human annotation in given content id
@app.route('/human_annotation')
@check_user_session
def human_annotation():
	user_id = int(session['user_id'])
	# Fetch pre annotation data for Human annotation
	content_id = str(request.args.get('content_id'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	raw_text, natural_entity_offset = db_obj.get_pre_annotation_data(project_id, content_id)
	all_text = ''
	entity_list = db_obj.get_entity_list(project_id)
	annoted_entity = db_obj.get_annotated_data(content_id)
	all_relationships = db_obj.get_all_relationship_name(project_id)
	for dat in raw_text:
		all_text = str(dat['raw_content'])
	all_text_copy = all_text	
	start_tag_len = 0
	
	for dat in natural_entity_offset:
		keyword = dat['keyword']
		# print keyword
		tag = dat['tag']
		start_position = dat['start_position'] + start_tag_len
		start_tag = "<mark data-entity='{}'>".format(tag)
		end_tag = "</mark>"
		
		all_text = all_text[:start_position] + start_tag + all_text[start_position:]
		end_position = dat['end_position'] + start_tag_len  + len(start_tag)
		
		all_text = all_text[:end_position] + end_tag+ all_text[end_position:]
		start_tag_len += len(start_tag) + len(end_tag)
		
	return render_template("human_annotation.html", content_id = content_id, raw_text =all_text , content_all_data = raw_text, natural_entity_offset= natural_entity_offset, entity_list = entity_list, all_relationships=all_relationships, annoted_entity=annoted_entity)

# upload human annotation is given contect id and project id
@app.route('/upload_human_annotation', methods=["POST"])
@check_user_session
def upload_human_annotation():
	user_id = int(session['user_id'])
	# upload human annotation data to database
	data = request.form
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	content_id = int(request.form['content_id'])
	entity_offset = {}	
	form_output = {}
	for entity in data:
		form_output[entity] = str(request.form[entity])
	
	for key, value in form_output.iteritems():
		
		if key.startswith('entityId_'):
			logger.debug ('Entity: {} Values{}'.format( key[9:], value))
			if key[9:] not in entity_offset:
				entity_offset[key[9:]] = {}
				entity_offset[key[9:]]['tag'] = value
			else:
				entity_offset[key[9:]]['tag'] = value

		if key.startswith('startPosition_'):
			logger.debug('startWith  {} Values{}'.format(key[14:], value))
			if key[14:] not in entity_offset:
				entity_offset[key[14:]] = {}
				entity_offset[key[14:]]['start_position'] = value
			else:
				entity_offset[key[14:]]['start_position'] = value

		if key.startswith('EndPosition_'):
			logger.debug('End With: {} values: {}'.format(key[12:], value))
			if key[12:] not in entity_offset:
				entity_offset[key[12:]] = {}
				entity_offset[key[12:]]['end_position'] = value
			else:
				entity_offset[key[12:]]['end_position'] = value
				
	db_obj.add_human_annotation_data(project_id, content_id, entity_offset)	
	return redirect('all_pre_annotation_list')

# Train NER model HTML page
@app.route('/train_ner_page')
@check_user_session
def train_ner_page():
	user_id = int(session['user_id'])
	# add data into system 
	return render_template('train_NER_model.html')

# Train NER Model 
@app.route('/train_NER_model')
@check_user_session
def train_classifer():
	user_id = int(session['user_id'])
	# Train NER Model
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	project_name =  db_obj.get_project_name(project_id)
	ner_model.main(project_id, str(project_id), project_name)
	return render_template("trained_NER_model.html")

# Rule Base model home page 
@app.route('/rule_based_home')
@check_user_session
def rule_based_home():
	user_id = int(session['user_id'])
	project_id = 0 
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	
	content_all_data = db_obj.content_all_data(project_id)
	classes = db_obj.all_classes(project_id)
	rules = db_obj.all_rules(project_id)
	
	return render_template('rule_based_home.html', content_all_data = content_all_data, classes = classes, rules = rules)

# Rule based model doctment details
@app.route('/rule_based_home_doc_detail')
@check_user_session
def rule_based_home_doc_detail():
	user_id = int(session['user_id'])
	content_id = str(request.args.get('content_id'))
	project_id = 0 
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	title, raw_text = db_obj.fetch_record(content_id)
	all_regex = db_obj.get_regex_class(project_id)
	makeup = rule_baed_model_obj.regex_markup(raw_text, all_regex)
	start_tag_len = 0	

	for class_name, positions in makeup.iteritems():
		start_tag = "<mark data-entity='{}'>".format(class_name)
		end_tag = "</mark>"
		logger.debug (class_name)
		for position in positions:
			logger.debug(position)
			start_position = position['start'] + start_tag_len
			raw_text = raw_text[:start_position] + start_tag + raw_text[start_position:]

			end_position = position['end'] + start_tag_len  + len(start_tag)
			raw_text = raw_text[:end_position] + end_tag + raw_text[end_position:]
			start_tag_len += len(start_tag) + len(end_tag)
	return render_template('rule_based_home_doc_detail.html', raw_text =raw_text)

# add new class in rule based model 
@app.route('/rule_based_add_class')
@check_user_session
def rule_based_add_class():
	user_id = int(session['user_id'])
	class_name = str(request.args.get('class_name'))
	project_id = 0 
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	
	content_all_data = db_obj.rule_based_add_class(project_id, class_name)
	return redirect('rule_based_home')

# Add new regex in given class 
@app.route('/rule_based_add_regex')
@check_user_session
def rule_based_add_regex_class():
	user_id = int(session['user_id'])
	regex = str(request.args.get('Regex'))
	class_id = str(request.args.get('class_id'))
	project_id = 0 
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	
	content_all_data = db_obj.rule_based_add_regex(project_id, class_id, regex)
	return redirect('rule_based_all_regex_class?class_id='+class_id)

# return list in All regex in given class 
@app.route('/rule_based_all_regex_class')
@check_user_session
def rule_based_all_regex_class():
	user_id = int(session['user_id'])
	class_id = str(request.args.get('class_id'))
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	all_regex =  db_obj.all_regex_by_class(project_id, class_id)
	class_name = db_obj.get_class_name(project_id, class_id)
	classes = db_obj.all_classes(project_id)
	rules = db_obj.all_rules(project_id)
	return render_template('rule_based_all_regex_class.html',classes= classes, class_id = class_id, rules=rules, class_name = class_name, all_regex = all_regex)

@app.route('/regex_apply')
@check_user_session
def regex_apply():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	content_id = str(request.args.get('content_id'))
	title, raw_text = db_obj.fetch_record(content_id)
	rules_apply = regex_rule_based_obj.main(raw_text, project_id)
	regex_classes = db_obj.regex_classes(project_id)
	regex_html_tag = {
				'capital_class' : {
							'start_html_tag':"<mark data-entity='capital_class'>",
							'end_html_tag': '</mark>'
							},

				'MONEY' : {
								'start_html_tag':"<mark data-entity='money'>",
								'end_html_tag': '</mark>'
							},							
				'GPE' : {
							'start_html_tag':"<mark data-entity='gpe'>",
							'end_html_tag': '</mark>'
							}
			}
	classes = db_obj.all_classes(project_id)
	rules = db_obj.all_rules(project_id)

	regex_response = rule_baed_model_obj.regex_applying(rules_apply, regex_classes, regex_html_tag)		
	return render_template("regex_apply.html", raw_text =regex_response, classes = classes, rules = rules, title=title )
		
@app.route('/rules_apply')
@check_user_session
def rules_apply():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	
	content_id = str(request.args.get('content_id'))
	title, raw_text = db_obj.fetch_record(content_id)
	
	rules_apply = regex_rule_based_obj.main(raw_text, project_id)

	# regex_response = rule_baed_model_obj.regex_applying(raw_text, regex_classes, regex_html_tag)		
	return render_template("regex_apply.html", raw_text =rules_apply )

@app.route('/add_new_rule_page', methods=['GET'])
@check_user_session
def add_new_rule_page():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	classes = db_obj.all_classes(project_id)
	rule_id = str(request.args.get('rule_id'))
	return render_template('add_new_rule.html', classes = classes, rule_id = rule_id)

@app.route('/entity_class_mapping_page', methods=['GET'])
@check_user_session
def entity_class_mapping_page():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	classes = db_obj.all_classes(project_id)
	entity_list = db_obj.get_entity_list(project_id)
	print (entity_list)

	return render_template('entity_mapping.html', classes = classes, entity_list = entity_list)

@app.route('/entity_class_mapping', methods=['POST'])
@check_user_session
def entity_class_mapping():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	data = request.form
	form_output = {}
	for entity in data:
		form_output[entity] = str(request.form[entity])

	db_obj.insert_entity_rule_mapping(project_id, form_output)
	return redirect('rule_based_home')

@app.route('/add_rule_name')
@check_user_session
def add_new_rule_name():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	rule_name = str(request.args.get('rule_name'))
	db_obj.add_rule_name(project_id, rule_name)
	content_all_data = db_obj.content_all_data(project_id)
	classes = db_obj.all_classes(project_id)
	rules = db_obj.all_rules(project_id)
	return render_template('rule_based_home.html', content_all_data = content_all_data, classes = classes, rules = rules)

'''Show Relationship in frontend'''
@app.route('/show_relationship', methods=['GET'])
@check_user_session
def show_relationship_page():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	# fetch all relatioship from given project Id

	all_relationships = db_obj.get_all_relationship(project_id)
	entity_list = db_obj.get_entity_list(project_id)
	return render_template('show_relationship.html', all_relationships = all_relationships, entity_list = entity_list)

'''Add relationship in database'''
@app.route('/add_relationship', methods=['POST'])
@check_user_session
def add_relationship():
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	data = request.form.to_dict()
	form_output = {}
	relationship_name = data.get("relationship_name")
	head_entity_id = int(data.get("head_entity"))
	tail_entity_id = int(data.get("tail_entity"))
	# Add relationship into database.
	db_obj.add_relationship(project_id, relationship_name, head_entity_id, tail_entity_id)
	return redirect('show_relationship')

'''Add human annotation for relationship into database'''
@app.route('/annotation_relationship', methods=['POST'])
@check_user_session
def annotation_relationship():
	user_id = int(session['user_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	if request.method == 'POST':
		all_data = request.json
		for data in all_data:
			id_user_contain = data.get("contain_id")
			id_relationship = data.get("relationship_id")
			head_entity_word = data.get("head_word")
			head_entity_start = data.get("head_start")
			head_entity_end = data.get("head_end")
			tail_entity_word = data.get("tail_word")
			tail_entity_start = data.get("tail_start")
			tail_entity_end = data.get("tail_end")
			db_obj.add_relationship_annotation(id_user_contain, id_relationship, head_entity_word, head_entity_start, head_entity_end, tail_entity_word, tail_entity_start, tail_entity_end)
	return redirect('rule_based_home')

'''Show relatioship into frontend'''
@app.route('/relationship_detail', methods=['GET'])
@check_user_session
def relationsship_detail():
	contain_id = int(session['contain_id'])
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	data = request.form
	form_output = {}
	for entity in data:
		form_output[entity] = str(request.form[entity])
	# get the contain details 
	
	# get all relationship 
	return redirect('rule_based_home')

# add new class in rule based model 
@app.route('/add_new_rule', methods=["POST"])
@check_user_session
def add_new_rule():
	user_id = int(session['user_id'])
	project_id = 0 
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	data = request.form
	
	form_output = {}
	for entity in data:
		form_output[entity] = str(request.form[entity])
	rule_id = str(request.args.get('rule_id'))

	one_rule_dic = {}
	one_rule_dic['rule_id'] = form_output['rule_id']
	one_rule_dic['rule_name'] = "fifth_rule"
	one_rule_json = []
	is_assigned = "is_assign_class_"
	is_regex = "is_regex_"
	assigned_class_id = "assigned_class_id_"
	class_id = "regex_class_"
	
	max_token = 3
	for i in range(max_token):
		i += 1
		rule_dict = {}
		rule_dict['position'] = i
		if is_assigned+str(i) in form_output:
			rule_dict['is_assigned'] = True
			rule_dict['assigned_class_id'] = form_output['assign_class_'+str(i)]
		if is_assigned+str(i) not in form_output:
			rule_dict['is_assigned'] = False
			rule_dict['assigned_class_id'] = 0
		if is_regex+str(i) in form_output:
			rule_dict['is_regex'] = True
			rule_dict['class_id'] = form_output['regex_class_'+str(i)]
			rule_dict['text'] = "None"
		if is_regex+str(i) not in form_output:
			rule_dict['is_regex'] = False
			rule_dict['class_id'] = 0
			rule_dict['text'] = form_output['text_'+str(i)]

		one_rule_json.append(rule_dict)
	# pprint(one_rule_json)
	one_rule_dic['rule_regex'] = one_rule_json    

	content_all_data = db_obj.insert_rule_db(project_id, one_rule_dic)
	return redirect('rule_based_home')

# Display HTML page for predicting the text from given URL use NER Model in it 
@app.route('/predict_text_page')
@check_user_session
def predict_text_page():
	user_id = int(session['user_id'])
	# add data into system 
	return render_template('predict_NER_model.html')

# predict the text from given URL use NER Model in it 
@app.route('/predict_NER_model')
@check_user_session
def predict_NER_model():
	user_id = int(session['user_id'])
	# call model with given URL and Get result 
	predicted_url = str(request.args.get('predicted_url'))
	title, predicted_text, publish_date, meta_Description = extractor_obj.get_only_text(predicted_url)
	
	if 'user_id' in session:
		user_id = int(session['user_id'])
	if 'user_id' not in session:
		return redirect('signup_page')
	predicted_text = title + predicted_text.encode('ascii', 'ignore').decode('ascii')
	category = classifier_obj.prediction(predicted_url, predicted_text, user_id)

	project_id = db_obj.get_project_id_by_name(category)
	project_name =  db_obj.get_project_name(project_id)
	entity_list = db_obj.get_entity_list(project_id)

	predict_result = ner_model.predict_NER_model(predicted_text, str(project_id), project_name)
	rules_result = regex_rule_based_obj.apply_all_rule(predicted_text, project_id)
	enity_mapping = db_obj.get_entity_rule_mapping(project_id)
	result_ = {}
	logger.debug("Classifcation Result: {}".format(category))
	
	logger.debug("NER Model Result: {}".format(predict_result))

	for rule in rules_result:
		# print(rule['assigned_class_id'])
		matched_entity_id = next((key for key, value in enity_mapping.iteritems() if value == rule['assigned_class_id']), None)
		entity_name = next((value for key, value in entity_list.iteritems() if key == matched_entity_id), None)
		# print(entity_name)
		if entity_name in result_:
			result_[entity_name].add(rule['keyword'])
		if entity_name not in result_:
			result_[entity_name] = set()
			result_[entity_name].add(rule['keyword'])
	logger.debug("Rule Based Model Result: {}".format(result_))		
	for result in predict_result:
		if result['tag'] in result_:
			result_[result['tag']].add(result['keyword'])
		if result['tag'] not in result_:
			result_[result['tag']] = set()
			result_[result['tag']].add(result['keyword'])

	return render_template("NER_result.html", category = category, predict_result = result_, predicted_text = predicted_text)

@app.route('/predict_ner', methods=["POST"])
def predict_ner():
	# call model with given URL and Get result 
	request_dict = request.json

	predicted_text = str(request_dict["text"])
	predicted_text = predicted_text.encode('ascii', 'ignore').decode('ascii')
	predicted_url = ""
	
	project_id = request_dict["project_id"]
	project_name =  db_obj.get_project_name(project_id)
	entity_list = db_obj.get_entity_list(project_id)

	predict_result = ner_model.predict_NER_model(predicted_text, str(project_id), project_name, natural_entity = False)
	# rules_result = regex_rule_based_obj.apply_all_rule(predicted_text, project_id)
	# enity_mapping = db_obj.get_entity_rule_mapping(project_id)
	result_ = {}
	# result_['category'] = [category]
	# logger.debug("Classifcation Result: {}".format(category))
	# logger.debug("NER Model Result: {}".format(predict_result))

	# for rule in rules_result:
	# 	# print(rule['assigned_class_id'])
	# 	matched_entity_id = next((key for key, value in enity_mapping.iteritems() if value == rule['assigned_class_id']), None)
	# 	entity_name = next((value for key, value in entity_list.iteritems() if key == matched_entity_id), None)
	# 	# print(entity_name)
	# 	if entity_name in result_:
	# 		result_[entity_name].add(rule['keyword'])
	# 	if entity_name not in result_:
	# 		result_[entity_name] = set()
	# 		result_[entity_name].add(rule['keyword'])
	# logger.debug("Rule Based Model Result: {}".format(result_))		
	for result in predict_result:
		if result['tag'] in result_:
			result_[result['tag']].add(result['keyword'])
		if result['tag'] not in result_:
			result_[result['tag']] = set()
			result_[result['tag']].add(result['keyword'])
	# convert set to list 
	result_list = []

	for key, value in result_.iteritems():
		result_dict = {}
		result_dict["entity_name"] = str(key)
		result_dict["entity_id"] = [filter( lambda x: entity_list[x] == str(key)  , entity_list ),[None]][0][0]
		result_dict["keywords"] = list(value)

		result_list.append(result_dict)
	all_relationships = db_obj.get_all_relationship(project_id)	
	relationship_results = utils.check_relationship_between_entites(result_list, all_relationships)
	final_result = {}
	final_result["entities"] = result_list
	final_result["relationship"] = relationship_results
	utils.create_test_json(relationship_results, predicted_text)
	r = json.dumps(final_result)
	loaded_r = json.loads(r)
	print(loaded_r)
	return jsonify(loaded_r)


@app.route('/predict_NER_model_text')
@check_user_session
def predict_NER_model_text():
	user_id = int(session['user_id'])
	# call model with given URL and Get result 
	predicted_text = str(request.args.get('predicted_text'))
	predicted_text = predicted_text.encode('ascii', 'ignore').decode('ascii')
	predicted_url = ""
	
	if 'user_id' in session:
		user_id = int(session['user_id'])
	if 'user_id' not in session:
		return redirect('signup_page')

	# category = classifier_obj.prediction(predicted_url, predicted_text, user_id)
	project_id = 0#db_obj.get_project_id_by_name(category)
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	
	project_name =  db_obj.get_project_name(project_id)
	entity_list = db_obj.get_entity_list(project_id)

	predict_result = ner_model.predict_NER_model(predicted_text, str(project_id), project_name, natural_entity = False)
	rules_result = regex_rule_based_obj.apply_all_rule(predicted_text, project_id)
	enity_mapping = db_obj.get_entity_rule_mapping(project_id)
	result_ = {}
	# result_['category'] = [category]
	# logger.debug("Classifcation Result: {}".format(category))
	# logger.debug("NER Model Result: {}".format(predict_result))

	for rule in rules_result:
		# print(rule['assigned_class_id'])
		matched_entity_id = next((key for key, value in enity_mapping.iteritems() if value == rule['assigned_class_id']), None)
		entity_name = next((value for key, value in entity_list.iteritems() if key == matched_entity_id), None)
		# print(entity_name)
		if entity_name in result_:
			result_[entity_name].add(rule['keyword'])
		if entity_name not in result_:
			result_[entity_name] = set()
			result_[entity_name].add(rule['keyword'])
	# logger.debug("Rule Based Model Result: {}".format(result_))		
	for result in predict_result:
		if result['tag'] in result_:
			result_[result['tag']].add(result['keyword'])
		if result['tag'] not in result_:
			result_[result['tag']] = set()
			result_[result['tag']].add(result['keyword'])
	# convert set to list 
	result_list = {}
	for key, value in result_.iteritems():
		result_list[str(key)] = list(value)

	r = json.dumps(result_list)
	loaded_r = json.loads(r)
	print(loaded_r)
	return jsonify(loaded_r)

@app.route('/predict_text_page_RSS')
@check_user_session
def predict_text_page_RSS():
	user_id = int(session['user_id'])
	# add data into system 
	return render_template('predict_NER_model _RSS.html')

@app.route('/predict_NER_model_RSS')
@check_user_session
def predict_NER_model_RSS():
	user_id = int(session['user_id'])
	# call model with given URL and Get result 
	predicted_rss = str(request.args.get('predicted_rss'))
	all_urls = extractor_obj.getLinks(predicted_rss)
	all_result = []
	if 'project_id' in session:
		project_id = int(session['project_id'])
	if 'project_id' not in session:
		project_id=1
	project_name =  db_obj.get_project_name(project_id)
	entity_list = db_obj.get_entity_list(project_id)
	enity_mapping = db_obj.get_entity_rule_mapping(project_id)


	for predicted_url in all_urls:
		title, predicted_text, publish_date, meta_Description = extractor_obj.get_only_text(predicted_url)
		
		predicted_text = title + predicted_text.encode('ascii', 'ignore').decode('ascii')
		category = classifier_obj.prediction(predicted_url, predicted_text)
		predict_result = ner_model.predict_NER_model(predicted_text, str(project_id), project_name)
		rules_result = regex_rule_based_obj.apply_all_rule(predicted_text, project_id)
		result_ = {}
		result_['URL'] = predicted_url
		result_['category'] = category
		# logger.debug("Classifcation Result: {}".format(category))
		
		# logger.debug("NER Model Result: {}".format(predict_result))

		for rule in rules_result:
			# print(rule['assigned_class_id'])
			matched_entity_id = next((key for key, value in enity_mapping.iteritems() if value == rule['assigned_class_id']), None)
			entity_name = next((value for key, value in entity_list.iteritems() if key == matched_entity_id), None)
			# print(entity_name)
			if entity_name in result_:
				result_[entity_name].add(rule['keyword'])
			if entity_name not in result_:
				result_[entity_name] = set()
				result_[entity_name].add(rule['keyword'])
		# logger.debug("Rule Based Model Result: {}".format(result_))		
		for result in predict_result:
			if result['tag'] in result_:
				result_[result['tag']].add(result['keyword'])
			if result['tag'] not in result_:
				result_[result['tag']] = set()
				result_[result['tag']].add(result['keyword'])
		all_result.append(result_)		
	
	return render_template("NER_Result_RSS.html", all_result = all_result)

# External APIS
# API for classification of url
@app.route('/predict',  methods=["POST"])
@check_user_session
def predict():
	user_id = int(session['user_id'])
	# add data into system 
	api_key = request.headers.get('API-KEY')
	api_secret = request.headers.get('API-SECRET')
	# get user_id from api key and secret 
	user_id = db_obj.get_user_id_from_api_key(api_key, api_secret)
	if user_id == False:
		# raised error invalid api key and secret 
		print("Invalid api key and secret")

	predicted_url = request.form['predicted_url']
	# predicted_text = str(request.args.get('predicted_text'))
	title, predicted_text, publish_date, meta_Description = extractor_obj.get_only_text(predicted_url)
	predicted_text = predicted_text.encode('ascii', 'ignore').decode('ascii')

	category = classifier_obj.prediction(predicted_url, predicted_text, user_id)
	project_id = db_obj.get_project_id_by_name(category)
	
	project_name =  db_obj.get_project_name(project_id)
	entity_list = db_obj.get_entity_list(project_id)

	predict_result = ner_model.predict_NER_model(predicted_text, str(project_id), project_name, natural_entity = True)
	rules_result = regex_rule_based_obj.apply_all_rule(predicted_text, project_id)
	enity_mapping = db_obj.get_entity_rule_mapping(project_id)
	result_ = {}
	result_['category'] = [category]
	logger.debug("Classifcation Result: {}".format(category))
	# logger.debug("NER Model Result: {}".format(predict_result))

	for rule in rules_result:
		# print(rule['assigned_class_id'])
		matched_entity_id = next((key for key, value in enity_mapping.iteritems() if value == rule['assigned_class_id']), None)
		entity_name = next((value for key, value in entity_list.iteritems() if key == matched_entity_id), None)
		# print(entity_name)
		if entity_name in result_:
			result_[entity_name].add(rule['keyword'])
		if entity_name not in result_:
			result_[entity_name] = set()
			result_[entity_name].add(rule['keyword'])
	# logger.debug("Rule Based Model Result: {}".format(result_))		
	for result in predict_result:
		if result['tag'] in result_:
			result_[result['tag']].add(result['keyword'])
		if result['tag'] not in result_:
			result_[result['tag']] = set()
			result_[result['tag']].add(result['keyword'])
	# convert set to list 
	result_list = {}
	for key, value in result_.iteritems():
		result_list[str(key)] = list(value)

	r = json.dumps(result_list)
	loaded_r = json.loads(r)
	
	return jsonify(loaded_r)

# @app.route('/admin_login_page')
# @check_user_session
# def admin_login_page():
# 	# add data into system 
# 	return render_template('admin_login.html')

# @app.route('/admin_login')
# def admin_login():
# 	if request.method == 'POST':
# 		admin_user_name = request.form['admin_user_name']
# 		admin_password = request.form['admin_password']
# 		validation_response = db_obj.validate_admin(admin_user_name, admin_password)
# 		if validation_response == False:
# 			print("Invalid admin_credential")
# 			return redirect('admin_login_page')
			
# 		if validation_response != False:
# 			admin_id = validation_response
# 			print("admin Id: {}".format(admin_id))	
# 			session['admin_id'] = admin_id
# 			return redirect('admin_dashboard_page')	
	

# @app.route('/admin_dashboard_page')
# def admin_dashboard_page():
# 	# add data into system 
# 	return render_template('admin_dashboard.html')

# @app.route('/admin_dashboard')
# def admin_dashboard():
# 	# list of all users
# 	admin_id =  int(session['admin_id'])
# 	all_user_data = db_obj.get_user_name_and_id()
# 	# add data into system 
# 	return render_template('predict_NER_model _RSS.html')

if __name__ == '__main__':
	# Start Server with IP: '0.0.0.0' and Port : 3001 with debug: True 
	http_server = WSGIServer(('0.0.0.0', 3001), app)
	http_server.serve_forever()