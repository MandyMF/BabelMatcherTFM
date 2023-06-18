from BabelMatcher import BabelTermsMatcher
from utils import get_data_from_config_file, write_result_to_pc

config_data = get_data_from_config_file()

testBabelTermsMatcher = BabelTermsMatcher(config_data['babel_key'])
testBabelTermsMatcher.load_data_from_padchest(config_data['data_to_process_path'])

testBabelTermsMatcher.load_to_current_model(config_data['load_model_path'])

results = []

for i in range(len(testBabelTermsMatcher.data)):
  
  doc = testBabelTermsMatcher.apply_model(testBabelTermsMatcher.currentNER_Model, testBabelTermsMatcher.data[i])
  results.append([{"entity": str(ent.text) , "tag": str(ent.label_)} for ent in doc.ents])

write_result_to_pc(results, config_data['result_file_path'])

testBabelTermsMatcher.save_current_model(config_data['save_model_path'])

