import re
from pprint import pprint
import logging
from NER_DB import nlp_DB as DB
db_obj = DB()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class regex_rule_based(object):
	"""docstring for regex_rule_based"""
	def get_all_rules(self, project_id):
		# return all rules in given project
		all_rules = db_obj.all_rules_regex(project_id)
		# pprint(all_rules)
		return all_rules
		
	def get_all_classes(self, project_id):
		# get all classes fin given project 
		all_classes = db_obj.regex_classes_all(project_id)

		return all_classes
		
	def convert_regex_to_str(self, regex_list):
		reg = len(regex_list)
		regex_str = ""
		for position in range(reg):
		    if position +2 > reg:
		        regex_str = regex_str + regex_list[position]
		    else:
		        regex_str = regex_str + regex_list[position] + "|"
		return regex_str
	
	def regex_string_convertor(self, all_rule_jsons, all_classes):
	    sorted_list = sorted(all_rule_jsons, key=lambda k: k['position']) 
	    return_str = ""
	    for i in range(len(sorted_list)):
	        if sorted_list[i]['is_regex']: 
	            matched_regex = next((l for l in all_classes if l['class_id'] == sorted_list[i]['class_id']), None)
	            regex_str = self.convert_regex_to_str(matched_regex['all_regex'])
	            return_str = return_str + "({}) ".format(regex_str)
	        else:
	            return_str = return_str + "({}) ".format(sorted_list[i]['text'])
	    return return_str	
	
	def get_assiged_class(self, start, searched_text, end, all_rule_jsons, all_classes, rule_id, rule_name):
	    sorted_list = sorted(all_rule_jsons, key=lambda k: k['position'])
	    if len(sorted_list) == 0:
	    	return []
	    # print(sorted_list)
	    returned_json = []
	    for i in range(len(sorted_list)):
	    	position = sorted_list[i]['position']
	        if sorted_list[i]['is_assigned']: 
	            if sorted_list[i]['is_regex']: 
	            	matched_regex = next((l for l in all_classes if l['class_id'] == sorted_list[i]['class_id']), None)
	                regex_str = self.convert_regex_to_str(matched_regex['all_regex'])
	            else:
	                regex_str = sorted_list[i]['text']
	            regex_str = "({})".format(regex_str)
	            
	            generic_re_assigned = re.compile(regex_str)
	            
	            searched_text_tokken = searched_text.split(' ')
	            
	            poss = 0
	            # print(searched_text_tokken)
	            for mm in generic_re_assigned.finditer(searched_text):
	            	keyword = mm.group()
	            	# print(keyword)
	            	if keyword in searched_text_tokken:
    					poss = searched_text_tokken.index(keyword) + 1
	            	
	            	# if poss == position:

	                returned_json_dict = {}
	                returned_json_dict['start'] = start + mm.start()
	                returned_json_dict['end'] = start + mm.end()
	                returned_json_dict['keyword'] = mm.group()
	                returned_json_dict['assigned_class_id'] = sorted_list[i]['assigned_class_id']
	                returned_json_dict['rule_id'] = rule_id
	                returned_json_dict['rule_name'] = rule_name

	                returned_json.append(returned_json_dict)
	    return returned_json

	def find_rule(self, raw_text, all_rules, all_classes):
		returned_match_list = []
		for rule in all_rules:
			rule_id = rule['rule_id']
			rule_name = rule['rule_name']
			rule_regex = rule['rule_regex']
			if len(rule_regex) != 0:
				return_str = self.regex_string_convertor(rule_regex, all_classes)
				generic_re = re.compile(return_str)
				# print(return_str)
				for m in generic_re.finditer(raw_text):
					# print(m.start(), m.group() , m.end())
					returned_match_list = returned_match_list + self.get_assiged_class(m.start(), m.group() , m.end(), rule_regex, all_classes, rule_id, rule_name)
		return returned_match_list
	    
	def rule_html_wrapper(self, raw_text, match_rules, rule_html_tags):
		ii = 0
		match_rules = sorted(match_rules, key=lambda k: k['start'])
		for match in match_rules:
			assigned_class_id = match['assigned_class_id']
			# print(match['keyword'])
			start_index = match['start']
			end_index = match['end']
			rule_html_tag = next((l for l in rule_html_tags if l['class_id'] == assigned_class_id), None)
			start_tag = rule_html_tag['start_tag']
			end_tag = rule_html_tag['end_tag']
			start_len = len(start_tag)
			end_len = len(end_tag)
			
			start_index = start_index + ii
			new_raw_text =raw_text[:start_index] + start_tag + raw_text[start_index:] 
			end_index = end_index + start_len + ii
			new_raw_text = new_raw_text[:end_index] + end_tag + new_raw_text[end_index:]
			
			ii = ii + start_len + end_len

			# print(new_raw_text)
			# print("******************")
			raw_text = new_raw_text

		return raw_text

	def get_rules_html_tags(self, project_id):
		rule_html_tags = []
		all_classes = db_obj.all_classes(project_id)
		for classes in all_classes:
			rule_html_tags_dict = {}
			rule_html_tags_dict['class_id'] = classes['class_id']
			rule_html_tags_dict['start_tag'] = "<mark data-entity='{}'>".format(classes['class_name'])
			rule_html_tags_dict['end_tag'] = '</mark>'
			rule_html_tags.append(rule_html_tags_dict)

		return rule_html_tags

	def apply_all_rule(self, raw_text, project_id):
		all_classes = self.get_all_classes(project_id)
		all_rules = self.get_all_rules(project_id)
		# print(all_rules)
		all_matched = self.find_rule(raw_text, all_rules, all_classes)
		return all_matched

		
	def main(self, raw_text, project_id):
		# get Raw_text and written json with assigned class and start and end position
		all_matched = self.apply_all_rule(raw_text, project_id)
		# pprint(all_matched)
		all_html_tags = self.get_rules_html_tags(project_id)
		tagged_text = self.rule_html_wrapper(raw_text, all_matched, all_html_tags)
		return tagged_text	


if __name__ == '__main__':
	project_id = 1
	raw_text = "One India For Regular 2 Expression 4 p, it true that , One India thus we say that the zero Regular two Expression four empty string is the identity under concatenation. There is no annihilator under concatenation, no regular expression 0 so that for any regular expression p it holds that . Concatenation is not commutative, since pq is not equal to qp, but associative since for any regular expressions p and q  true that "
	regex_rule_based_obj = regex_rule_based()
	match_result = regex_rule_based_obj.main(raw_text, project_id)
	pprint(match_result)