from BabelMatcher import BabelTermsMatcher
from utils import get_data_from_config_file, write_result_to_pc

config_data = get_data_from_config_file()

testBabelTermsMatcher = BabelTermsMatcher(config_data['babel_key'])
testBabelTermsMatcher.load_data_from_padchest(config_data['data_to_process_path'])

data_from_babelnet = testBabelTermsMatcher.get_data_from_list_of_ids ( config_data['id_list'], config_data['lang'], config_data['search_levels'])

model, ruler = testBabelTermsMatcher.create_NER_model(data_from_babelnet, config_data['lang'])

results = []

for i in range(len(testBabelTermsMatcher.data)):
  
  doc = testBabelTermsMatcher.apply_model(model, testBabelTermsMatcher.data[i])
  results.append([{"entity": str(ent.text) , "tag": str(ent.label_)} for ent in doc.ents])

write_result_to_pc(results, config_data['result_file_path'])

testBabelTermsMatcher.save_current_model(config_data['save_model_path'])

