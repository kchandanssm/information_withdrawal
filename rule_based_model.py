# coding: utf8
import re
import os
import logging
from regex_apply import regex_rule_based

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
regex_rule_based_obj = regex_rule_based()

class rule_based_model(object):
	"""docstring for rule_based_model"""
	def __init__(self):
		super(rule_based_model, self).__init__()

	def regex_markup(self, text, regex_annotation):
		# Regex markup for fitting the regex into text 
		return_dic = {}
		for class_name, regex in regex_annotation[0].iteritems():
			return_dic[class_name] = []
			for reg in regex:
				logging.debug(str(reg+class_name))
				p=re.compile(reg)
				for m in p.finditer(text):
					# logging.debug(str(m.start()+m.group()+m.end()))
					send_dic = {}
					send_dic['start'] = m.start()
					send_dic['end'] = m.end()
					return_dic[class_name].append(send_dic)
		return return_dic

	def regex_applying(self, raw_text, regex_classes, regex_html_tag):
		# On raw text apply regex in it
		
		# regex_classes = { 
		# 	 	'class_name': ['regex'],
		# 	 }
		
		# Regex Html tag =
			# {
			# 	'class_name' : [
			# 						'start_html_tag':'html_tag_start'
			# 						'end_html_tag': 'html_tag_end'
			# 						]
			# }
		return_dictin = {}
		return_dictin['raw_text'] = raw_text
		return_dictin['regex_classes'] = {}
		for keys,values in regex_classes.items():
			if len(values) != 0:
				return_dictin['regex_classes'][keys] = []
				p = regex_rule_based_obj.convert_regex_to_str(values)
				pp = re.compile(p)
				ii = 0
				for m in pp.finditer(raw_text):
					regex_dict = {}
					regex_dict['start'] = m.start()
					regex_dict['end'] = m.end()
					regex_dict['keywords'] = m.group()
					return_dictin['regex_classes'][keys].append(regex_dict)
					start_index = m.start() + ii
					end_index = m.end()
					keywords = m.group()
					start_index = start_index
					
					start_tag = regex_html_tag[keys]['start_html_tag']
					end_tag = regex_html_tag[keys]['end_html_tag']
					
					new_raw_text =raw_text[:start_index] + start_tag + raw_text[start_index:] 
					start_len = len(start_tag)
					end_index = end_index + start_len + ii
					new_raw_text = new_raw_text[:end_index] + end_tag + new_raw_text[end_index:]
					end_len = len(end_tag)

					ii = ii + start_len + end_len
					raw_text = new_raw_text
					regex_apply_text = ""

		return raw_text

if __name__ == '__main__':
	rule_based_model_obj  = rule_based_model()
	raw_text = 'I owned a company called GOOGLE INDIA PVT in $1 Billion AND also $2 billion.'
	regex_classes = { 
				'PERSON': ['regex_11', 'regex_12', 'regex_13'],
				'FACILITY': ['regex_22', 'regex_21', 'regex_23'],
				'GPR': ['regex_32', 'regex_31']
			}
	regex_html_tag = {
				'PERSON' : {
									'start_html_tag':"<mark data-entity='person'>",
									'end_html_tag': '</mark>'
									},

				'FACILITY' : {
									'start_html_tag':"<mark data-entity='FACILITY'>",
									'end_html_tag': '</mark>'
									},
				'GPR' : {
									'start_html_tag':"<mark data-entity='GPR'>",
									'end_html_tag': '</mark>'
									}
			}

	regex_response = rule_based_model_obj.regex_applying(raw_text, regex_classes, regex_html_tag)		
	# print(regex_response)

