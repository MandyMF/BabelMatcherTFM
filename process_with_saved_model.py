from .BabelMatcher import BabelTermsMatcher
from .utils import get_data_from_config_file, write_result_to_pc, create_html_file, create_html_var, write_html_to_pc

class ExecClass:
  
  def __init__ (self):
    self.finish = False
    self.config_data = get_data_from_config_file()
    self.babelTermsMatcher = BabelTermsMatcher(
                                            self.config_data['babel_key'], 
                                            waitTime= self.config_data['waiting_time_on_error'], 
                                            doNotWaitForServer= self.config_data['not_wait_when_token_are_spend'], 
                                            matchDistance= self.config_data['match_levenshtein_distance'],
                                            is_lemmatized=  self.config_data['dataset_is_lemmatized']
                                          )
    
  def exec(self):

    self.babelTermsMatcher.load_data_from_padchest(self.config_data['data_to_process_path'])

    self.babelTermsMatcher.load_to_current_model(self.config_data['load_model_path'])

    self.babelTermsMatcher.save_current_model(self.config_data['save_model_path'])

    results = []
    raw_results = []

    print("Model Loaded and Saved")
    print("Now Processing Data")

    for i in range(len(self.babelTermsMatcher.data)):
      if(type(self.babelTermsMatcher.data[i]) != str):
        continue
      
      doc = self.babelTermsMatcher.apply_model(self.babelTermsMatcher.currentNER_Model, self.babelTermsMatcher.data[i])
      results.append({ "id": self.babelTermsMatcher.ImageIds[i] ,"tags":[{"entity": str(ent.text) , "tag": str(ent.label_)} for ent in doc.ents]})
      raw_results.append(doc)

    print("Saving Results")
    write_result_to_pc(results, self.config_data['result_file_path'])

    create_html_file(self.config_data['save_html_view'])

    batch_size = 100
    count = 0
    html_result = ''

    print("Creating Html Data from Results")

    for doc in raw_results:
      _, html = self.babelTermsMatcher.display_html_doc_by_labels(doc)
      html_result = create_html_var(html, html_result, results[count]["id"])
      count += 1
      if(count % batch_size == 0):
        write_html_to_pc(html_result, self.config_data['save_html_view'])

    write_html_to_pc(html_result, self.config_data['save_html_view'])

    self.finish = True
    print("Job Done")

if __name__ == "__main__":
  exec_inst = ExecClass()
  exec_inst.exec()
