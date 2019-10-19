import json
import copy

def __compare_relationship(entity_first_id, entity_second_id, relationship_list):
	for relationship in relationship_list:
		head_entity_id = relationship["head_entity"]["entity_id"] 
		tail_entity_id = relationship["tail_entity"]["entity_id"] 
		if entity_first_id == head_entity_id and entity_second_id == tail_entity_id:
			return True, relationship["relationship_name"]
		
	return False, "_"	
		

def check_relationship_between_entites(entity_result, relationship_list):
	# find if there is some relationship is between two enties.
	relationship_results = []
	for entity_first in entity_result:
		for entity_second in entity_result:
			if entity_first["entity_id"] != entity_second["entity_id"]:
				is_equal, relationship_name = __compare_relationship(entity_first["entity_id"], entity_second["entity_id"], relationship_list)
				if is_equal:
					for head_keyword in entity_first["keywords"]:
						for tail_keyword in entity_second["keywords"]:
							relationship_dict = {}
							head_entity = {}
							head_entity["id"] = str(entity_first["entity_id"])
							head_entity["type"] = entity_first["entity_name"]
							head_entity["word"] = head_keyword
							tail_entity = {}
							tail_entity["id"] = str(entity_second["entity_id"])
							tail_entity["type"] = entity_second["entity_name"]
							tail_entity["word"] = tail_keyword
							relationship_dict["head"] = head_entity
							relationship_dict["tail"] = tail_entity
							relationship_dict["relation"] = relationship_name
							relationship_results.append(relationship_dict)
	return relationship_results 				

def create_test_json(relationship_list, raw_content):
	# create test json in code
	final_relationship = []
	for relationship in relationship_list:
		new_relationship = copy.deepcopy(relationship)
		new_relationship["sentence"] = raw_content
		final_relationship.append(new_relationship)
	with open('test.json', 'w') as fp:
		json.dump(final_relationship, fp, indent=4)	

