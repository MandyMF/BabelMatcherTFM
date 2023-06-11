from BabelMatcher import BabelTermsMatcher
from utils import get_data_from_config_file, load_data_csv, write_result_to_pc

#!python -m spacy download en_core_web_sm


config_data = get_data_from_config_file()
#raw_test_df = load_data_csv(config_data['data_to_process_path'])

#print(raw_test_df)

testBabelTermsMatcher = BabelTermsMatcher(config_data['babel_key'])
testBabelTermsMatcher.load_data_from_padchest(config_data['data_to_process_path'])

#data_from_babelnet = testBabelTermsMatcher.get_data_from_list_of_lemmas_default_all ( ['medicine', 'surgery'], config_data['lang'], config_data['search_levels'])

data_from_babelnet = testBabelTermsMatcher.get_data_from_list_of_lemmas_default_first ( config_data['lemma_list'], config_data['lang'], config_data['search_levels'])

model, ruler = testBabelTermsMatcher.create_NER_model(data_from_babelnet, config_data['lang'])

results = []

for i in range(0, 8):
  
  doc = testBabelTermsMatcher.apply_model(model, testBabelTermsMatcher.data[i])
  results.append([{"entity": str(ent.text) , "tag": str(ent.label_)} for ent in doc.ents])

write_result_to_pc(results, config_data['result_file_path'])

testBabelTermsMatcher.save_current_model(config_data['save_model_path'])

