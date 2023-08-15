from BabelMatcher import BabelTermsMatcher
from utils import get_data_from_config_file, write_result_to_pc, create_html_file, create_html_var, write_html_to_pc, write_html

def exec():
  config_data = get_data_from_config_file()

  testBabelTermsMatcher = BabelTermsMatcher(
                                            config_data['babel_key'], 
                                            waitTime= config_data['waiting_time_on_error'], 
                                            doNotWaitForServer= config_data['not_wait_when_token_are_spend'], 
                                            matchDistance=config_data['match_levenshtein_distance'],
                                            is_lemmatized= config_data['dataset_is_lemmatized']
                                          )
  testBabelTermsMatcher.load_data_from_padchest(config_data['data_to_process_path'])

  data_from_babelnet = testBabelTermsMatcher.get_data_from_list_of_ids ( config_data['id_list'], config_data['lang'], config_data['search_levels'])

  write_result_to_pc(data_from_babelnet, config_data['save_pattern_path'])

  model, ruler = testBabelTermsMatcher.create_NER_model(data_from_babelnet, config_data['lang'])

  testBabelTermsMatcher.save_current_model(config_data['save_model_path'])

  results = []
  raw_results = []

  print("Model Created and Saved")
  print("Now Processing Data")

  for i in range(len(testBabelTermsMatcher.data)):
    if(type(testBabelTermsMatcher.data[i]) != str):
      continue
    
    doc = testBabelTermsMatcher.apply_model(model, testBabelTermsMatcher.data[i])
    results.append({ "id": testBabelTermsMatcher.ImageIds[i] ,"tags":[{"entity": str(ent.text) , "tag": str(ent.label_)} for ent in doc.ents]})
    raw_results.append(doc)

  print("Saving Results")
  write_result_to_pc(results, config_data['result_file_path'])

  create_html_file(config_data['save_html_view'])

  batch_size = 100
  count = 0
  html_result = ''

  print("Creating Html Data from Results")

  for doc in raw_results:
    _, html = testBabelTermsMatcher.display_html_doc_by_labels(doc)
    html_result = create_html_var(html, html_result, results[count]["id"])
    count += 1
    if(count % batch_size == 0):
      write_html_to_pc(html_result, config_data['save_html_view'])

  write_html_to_pc(html_result, config_data['save_html_view'])

  print("Job Done")

if __name__ == "__main__":
  exec ()