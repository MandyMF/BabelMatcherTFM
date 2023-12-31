import spacy
from spacy import displacy as dspl
from spacy.lang.en import EnglishDefaults
import time
from threading import Thread
from pathlib import Path
import pandas as pd

from string import punctuation

import requests
import json

if __package__ is None or __package__ == '':
    # uses current directory visibility
  from stopwords import get_stop_words
else:
    # uses current package visibility
  from .stopwords import get_stop_words

import warnings
import unicodedata

warnings.filterwarnings("ignore", message=r"\[W006\]", category=UserWarning)

def removePuntuation(str_to_replace):
    punctuation_extended = list(punctuation) + ['\'', '\"', '\`']
    for c in punctuation_extended:
        str_to_replace = str_to_replace.replace(c, '')
    return str_to_replace

def normalize_text(text):
    return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8') 


class BabelTermsMatcher:

    COLORS = [
        "pink",
        "blue",
        "gray",
        "red",
        "green"
    ]


    def __init__ (self, key, waitTime = 360, doNotWaitForServer = False, matchDistance = 1, is_lemmatized = True):
      '''  
      Initialization method where:
      - key should be the babelnet key.
      - waitTime is the time that the code wait after an unsuccessful request to babelnet,
        the normal error is the one with status 403 because you can run out of babel tokens.
      - doNotWaitForServer if this parameter is True then after a failed request to babelnet,
        istead of waiting for more coins or wait to retry, it will just returns an empty array,
        this is use in case you do several continuos request and you run out of coins, so the
        program can finish its run with the data already collected.
      - is_lemmatized if the parameter is True, it activates an extra step on the pattern building process 
      '''
      self.key = key
      self.waitTime = waitTime
      self.waiting = False
      self.doNotWaitForServer = doNotWaitForServer
      self.latestOperation = None
      self.latestOperationResult = None
      self.currentNER_Model = None
      self.data = None
      self.ImageIds = None
      self.matchDistance = matchDistance
      self.is_lemmatized = is_lemmatized
    
    def load_data_from_padchest(self, data_path):
      '''
      Load the data from a padchest like structured file to the current data field to store
      in the class instance.
      '''
      raw_data = pd.read_csv(data_path, index_col=0)
      self.data = list(raw_data['Report'])
      self.ImageIds = list(raw_data['ImageID'])

    def save_model(self, model, path):
      '''
      Save model store in the model variable to a specific path, and this will create a directory,
      with the spacy model to load.
      '''
      model.to_disk(path)
      return

    def save_current_model(self, path):
      '''
      Save model store in the clase instance to a specific path, and this will create a directory,
      with the spacy model to load.
      '''
      if(self.currentNER_Model):
        self.currentNER_Model.to_disk(path)
        return 1
      else:
        print("No model to save")
        return 0

    def load_model(self, path):
      '''
      Load model from a specific path and returns this model.
      '''
      model = spacy.load(path)
      return model

    def load_to_current_model(self, path):
      '''
      Load model from a specific path to the instance model variable , also returns this model.
      '''
      self.currentNER_Model = spacy.load(path)
      return self.currentNER_Model

    def get_hyponyms(self, id, lang):
      '''
      Return the hyponyms from a specific babelnet id and a specific language.
      '''
      return_data= []
      
      data = []
      url = "https://babelnet.io/v8/getOutgoingEdges?id={0}&targetLang={1}&key={2}".format(id, lang, self.key)
      
      response = requests.request("POST", url)
      while(response.status_code == 403):
          if(self.doNotWaitForServer):
            self.latestOperation = "get_hyponyms"
            self.latestOperationResult = return_data
            self.waiting = False
            return return_data
          self.waiting = True
          print("Waiting, coins were spent or blocked !!!!!!")
          time.sleep(self.waitTime)
          # Request again after the waiting time
          response = requests.request("POST", url)
      self.waiting = False 
      data = json.loads(response.text)
      for result in data:
        target = result.get('target')
        language = result.get('language')
        # retrieving BabelPointer data
        pointer = result['pointer']
        #relation = pointer.get('name')
        group = pointer.get('relationGroup')
        if ('HYPONYM' == group and language == lang):
          return_data.append(target)
      self.latestOperation = "get_hyponyms"
      self.latestOperationResult = return_data
      return return_data

    def get_hyponyms_with_levels (self, id, lang, levels):
      '''
      Return the hyponyms from a specific id all the way recursively to a specific level.
      It uses the get_hyponyms to get all hyponymss from this id and then uses this results
      to get the hyponymss in the next level.
      '''
      ret_data = [id]
      current_l = [id]
      seen_ids = []
      
      for i in range(levels):
        level_l = []
        for id_v in current_l:
          if (id_v in seen_ids):
            continue
          else:
            hypo_l = self.get_hyponyms(id_v, lang) 
            level_l.extend(hypo_l)
            ret_data.extend(hypo_l)
            seen_ids.append(id_v)
        current_l = level_l
      
      return_data = list(set(ret_data))
      
      self.latestOperation = "get_hyponyms_with_levels"
      self.latestOperationResult = return_data
      return return_data

    def get_data_from_id_with_tag (self, id, lang, tag):
      '''
      Using a specific id and a specific tag, returns all data found from the id as a dict
      in a specific tag index.
      '''
      ret_dic = {}
      ret_dic[tag] = set()
      url = "https://babelnet.io/v8/getSynset?id={0}&targetLang={1}&key={2}".format(id, lang, self.key)
      
      response = requests.request("POST", url)
      while(response.status_code == 403):
          if(self.doNotWaitForServer):
            ret_dic[tag] = list(ret_dic[tag])
            self.latestOperation = "get_data_from_id_with_tag"
            self.latestOperationResult = ret_dic
            self.waiting = False
            return ret_dic
          self.waiting = True
          print("Waiting, coins were spent or blocked !!!!!!")
          time.sleep(self.waitTime)
          
          # Request again after the waiting time
          response = requests.request("POST", url)
      self.waiting = False
      data = json.loads(response.text)
      ret_dic = self.create_dic_from_instance(data, tag, ret_dic)
      self.latestOperation = "get_data_from_id_with_tag"
      self.latestOperationResult = ret_dic
      return ret_dic

    def create_dic_from_instance(self, data, tag, ret_dic):
      '''
      It returns a dict from a raw babel data query response by processing the data.
      '''
      for val in data['senses']:
        if(tag in ret_dic):
          ret_dic[tag] = ret_dic[tag].union( set([(val['properties']['lemma']['lemma']).lower()]))
        else:
          ret_dic[tag] = set([(val['properties']['lemma']['lemma']).lower()])
      ret_dic[tag] = list(ret_dic[tag]) 
      self.latestOperation = "create_dic_from_instance"
      self.latestOperationResult = ret_dic
      return ret_dic

    def get_data_from_id_and_hypo_by_level(self, id, lang, tag, levels):
      '''
      It uses get_hyponyms_with_levels to get the list of babel ids and from those,
      the function get_data_from_id_with_tag is used to get the data, also from babelnet.
      '''
      hypo_by_lvl_l = self.get_hyponyms_with_levels(id, lang, levels)
      ret_dic = {}
      ret_dic[tag] = []
      for id in hypo_by_lvl_l:
        ret_data_dic = self.get_data_from_id_with_tag(id, lang, tag)
        if(ret_data_dic):
          ret_dic[tag] = ret_dic[tag] + ret_data_dic[tag]
      ret_dic[tag] = list(set(ret_dic[tag]))
      self.latestOperation = "get_data_from_id_and_hypo_by_level"
      self.latestOperationResult = ret_dic
      return ret_dic
    
    #---------------------------------- stage 4 ---------------------------------------------
    def get_only_data_from_id(self, id, lang):
      '''
      Get the data from babelnet from a specific id.
      '''
      ret_dic = []
      url = "https://babelnet.io/v8/getSynset?id={0}&targetLang={1}&key={2}".format(id, lang, self.key)
      
      response = requests.request("POST", url)
      while(response.status_code == 403):
          if(self.doNotWaitForServer):
            self.latestOperation = "get_only_data_from_id"
            self.latestOperationResult = ret_dic
            self.waiting = False
            return ret_dic
          self.waiting = True
          print("Waiting, coins were spent or blocked !!!!!!")
          time.sleep(self.waitTime)
          
          # Request again after the waiting time
          response = requests.request("POST", url)
      self.waiting = False
      data = json.loads(response.text)
      ret_dic = self.get_data_from_resp(data)
      self.latestOperation = "get_only_data_from_id"
      self.latestOperationResult = ret_dic
      return ret_dic

    def get_data_from_resp(self, data):
      '''
      This function process the babelnet response into a list, this list is compose of
      the Potencial Synonyms in the babelnet graph that are marked as HIGH_QUALITY,
      low quality ones are useless.
      '''
      ret_list=[]
      sourceSense_l = []
      for val in data['senses']:
        # POTENTIAL_NEAR_SYNONYM_OR_WORSE
        if(val['properties']['lemma']['type'] != 'HIGH_QUALITY'):
          #if(val['properties']['lemma']['type'] != 'POTENTIAL_NEAR_SYNONYM_OR_WORSE'):
          #  continue
          continue
        if(val['properties']['synsetID']['id'] in sourceSense_l):
          continue
        if('glosses' in data):
          item = {
              'lemma': val['properties']['lemma']['lemma'],
              'glosses': data['glosses']
          }
        else:
          item = {
              'lemma': val['properties']['lemma']['lemma'],
              'glosses': ''
          }
        sourceSense_l.append(val['properties']['synsetID']['id'])
        ret_list.append(item)
      self.latestOperation = "get_data_from_resp"
      self.latestOperationResult = ret_list
      return ret_list

    # -----------------------------------------------
    # get data from a lemma, return a list of ids
    # -----------------------------------------------
    
    def get_data_from_lemma(self, lemma, lang):
      '''
      This function creates a query that returns all posible ids from a specific lemma or word,
      and uses the get_only_data_from_id to get the highest quality ones.
      *IMPORTANT* this one includes glosses but it's slower and consume more queries than get_only_data_from_lemma
      '''
      ret_resp = []
      resp_data_list = []
      url = "https://babelnet.io/v8/getSynsetIds?lemma={0}&searchLang={1}&key={2}".format(lemma, lang, self.key)
      
      response = requests.request("POST", url)
      while(response.status_code == 403):
          if(self.doNotWaitForServer):
            self.latestOperation = "get_data_from_lemma"
            self.latestOperationResult = resp_data_list
            self.waiting = False
            return resp_data_list
          self.waiting = True
          print("Waiting, coins were spent or blocked !!!!!!")
          time.sleep(self.waitTime)
          
          # Request again after the waiting time
          response = requests.request("POST", url)
      self.waiting = False
      data = json.loads(response.text)
      ret_resp.extend(data)
  
      for item in ret_resp:
        resp_data = self.get_only_data_from_id(item['id'], lang)
        resp_data_list.append({
            'id': item['id'],
            'data': resp_data
        })
      
      self.latestOperation = "get_data_from_lemma"
      self.latestOperationResult = resp_data_list
      return resp_data_list
    
    # -----------------------------------------------
    # get data from a lemma, return a list of ids
    # -----------------------------------------------
    
    def get_only_data_from_lemma(self, lemma, lang):
      '''
      This function creates a query that returns all posible ids from a specific lemma or word.
      *IMPORTANT* this one doesn't include glosses but it's faster and consume less queries than get_data_from_lemma
      '''
      ret_resp = []
      resp_data_list = []
      url = "https://babelnet.io/v8/getSenses?lemma={0}&searchLang={1}&key={2}".format(lemma, lang, self.key)
      
      response = requests.request("POST", url)
      while(response.status_code == 403):
          if(self.doNotWaitForServer):
            self.latestOperation = "get_data_from_lemma"
            self.latestOperationResult = resp_data_list
            self.waiting = False
            return resp_data_list
          self.waiting = True
          print("Waiting, coins were spent or blocked !!!!!!")
          time.sleep(self.waitTime)
          
          # Request again after the waiting time
          response = requests.request("POST", url)
      self.waiting = False
      data = json.loads(response.text)
      ret_resp.extend(data)
      
      list_known_ids = []
      
      for item in ret_resp:
        resp_data = self.get_data_from_resp({'senses': [item]})
        
        if(item['properties']['synsetID']['id'] in list_known_ids):
          continue
        else:
          list_known_ids.append(item['properties']['synsetID']['id'])
        resp_data_list.append({
            'id': item['properties']['synsetID']['id'],
            'data': resp_data
        }) 

      self.latestOperation = "get_only_data_from_lemma"
      self.latestOperationResult = resp_data_list
      return resp_data_list

    def get_glosses_and_id_from_lemma(self, lemma, lang):
      ''' Returns lemma that would be the tag and the lists to disambiguate. '''
      
      data_from_lemma = self.get_data_from_lemma(lemma, lang)
      ret_data = []
      for item in data_from_lemma:
          ent_to_add = {
              'id': item['id'],
              'lemma': [],
              'glosses': []
          }
          for data in item['data']:
            if(data['lemma']):
              ent_to_add['lemma'].append(data['lemma'])
            if(data['glosses']):
              for gloss in data['glosses']:
                if(gloss['gloss']):
                  ent_to_add['glosses'].append(gloss['gloss'])
          ret_data.append(ent_to_add)
      self.latestOperation = "get_glosses_and_id_from_lemma"
      self.latestOperationResult = [lemma, ret_data]
      return [lemma, ret_data]

    def create_pattern (self, data, lang):
      '''
      This function creates the pattern that is going to be use by the spacy model.
      This implementation uses FUZZY with one letter permutation, to match the data
      that comes in the data parameter.
      The data parameter is a dict of:
      keys that describes the list of terms or lemmas to match, this can be the main
      lemma to match or a made tag.
      '''
      
      stop_words = []
      try: 
        stop_words = set(get_stop_words(lang.lower()))
      except:
        stop_words = set([])
    
      pattern = []
        
      for key in data:
        
        data_key_split = set()
        data_split_l = []
        for i in data[key]:
          split_result = i.split('_')
          for word in split_result:
            if(word in stop_words):
              continue
            after_word = removePuntuation(normalize_text(word))
            if(len(after_word)<=2):
              continue
            data_split_l.append(after_word)
          
          replace_result = removePuntuation(normalize_text(i.replace('_', ' ')))
          data_key_split.add(replace_result)
        
        data_split_l = list(set(data_split_l))
        data_key_split = list(data_key_split)
        
        # This is the old way to create patterns, the IN operator only takes words, not frases.
        
        for element in data_key_split:
          if(len(element) == 0):
            continue
          item1 = {
              "label": key.replace(' ', '_'),
              "pattern": element,
              "type": "fuzzy"+str(self.matchDistance)
          }
          
          pattern.append(item1)
        
        item2 = {
            "label": key.replace(' ', '_'),
            "pattern": [
               {
                   "TEXT": 
                   {
                      "FUZZY"+str(self.matchDistance): 
                      {
                        "IN": data_split_l,
                        "NOT_IN": list(punctuation) + list(stop_words)
                      }
                   }
               } 
            ]
        }
        if(self.is_lemmatized):
          pattern.append(item2)
      
      phone_pattern = {"label": "PHONE_NUMBER", "pattern": [
          {'ORTH': '('}, {'SHAPE': 'd'},
          {'ORTH': ')'},
          {'SHAPE': 'dd'},
          {'ORTH': '-', 'OP': '?'},
          {'SHAPE': 'ddd'},
          {'ORTH': '-', 'OP': '?'},
          {'SHAPE': 'dddd'}
          ]}  
      phone_pattern_2 = {"label": "PHONE_NUMBER", "pattern": [
          {'ORTH': '('},
          {'TEXT':{'REGEX':'[\d]\)[\d]*'}},
          {'ORTH': '-', 'OP': '?'},
          {'SHAPE': 'ddd'},
          {'ORTH': '-', 'OP': '?'},
          {'SHAPE': 'dddd'}
          ]}
      
      phone_pattern_3 = {"label": "PHONE_NUMBER", "pattern": [
            {"IS_DIGIT":True ,"LENGTH": 9}
          ]}
      
      email_pattern = {"label": "EMAIL", "pattern": [
            {'LIKE_EMAIL': True}
          ]}  
      date_pattern = {"label": "DATE", "pattern": [{'TEXT':{'REGEX':r'^\d{1,2}/\d{1,2}/\d{2}(?:\d{2})?$'}}]}                               
      date_pattern2 = {"label": "DATE", "pattern": [{'IS_DIGIT': True}, {'ORTH': '-'}, {'IS_DIGIT': True}, {'ORTH': '-'}, {'IS_DIGIT': True}]}
      pattern.append(phone_pattern)
      pattern.append(phone_pattern_2)
      pattern.append(phone_pattern_3)
      pattern.append(date_pattern)
      pattern.append(date_pattern2)
      pattern.append(email_pattern)
      
      return pattern



    def create_NER_model (self, pattern, lang):
      '''
      This function creates a model from a specific pattern.
      The pattern has to have the spacy pattern structure structure.
      ''' 
      stop_words = []
      try: 
        stop_words = set(get_stop_words(lang.lower()))
      except:
        stop_words = set([])

      EnglishDefaults.stop_words = stop_words
      nlp = spacy.blank("en")

      ruler = nlp.add_pipe("entity_ruler")
      
      ruler.add_patterns(pattern)
      self.currentNER_Model = nlp
      return nlp, ruler

    def display_doc_by_labels(self, doc):
      '''
      This function uses the result from a model to display the results in color;
      it only works in colab, jupyter notebook, and jupyter lab envs.
      '''
      colors_l = self.COLORS
      color_count = 0
      opt_colors = {}
      opts_ents = []
      labels = set()
      for ent in doc.ents:
        labels.add(ent.label_)
      labels = list(labels)
      for lab in labels:
        if (color_count >= len(colors_l)): 
          color_count = 0
        opt_colors[lab] = colors_l[color_count]
        opts_ents.append(lab)
        color_count+=1
      opts = {
          "ents": opts_ents,
          "colors": opt_colors,
          "distance": 90 
      }
      dspl.render(doc, style='ent', jupyter=True, options=opts)
      return opts
    
    def display_html_doc_by_labels(self, doc):
      '''
      This function uses the result from a model to display the results in color;
      it returns an html code to show.
      '''
      colors_l = self.COLORS
      color_count = 0
      opt_colors = {}
      opts_ents = []
      labels = set()
      for ent in doc.ents:
        labels.add(ent.label_)
      labels = list(labels)
      for lab in labels:
        if (color_count >= len(colors_l)): 
          color_count = 0
        opt_colors[lab] = colors_l[color_count]
        opts_ents.append(lab)
        color_count+=1
      opts = {
          "ents": opts_ents,
          "colors": opt_colors,
          "distance": 90 
      }
      html = dspl.render(doc, style='ent', page=True, options=opts)
      return opts, html

    #this is only use when working with jupyterLab, jupyterNotebook or colab
    def apply_and_show_model (self, model_ner, text):
      '''
      This function uses display_doc_by_labels to show display the the results of the
      text processed by the model_ner parameter.
      '''
      doc = model_ner(text) 
      for ent in doc.ents:
        print(ent.text, ent.label_)
      self.display_doc_by_labels(doc)

    def apply_model (self, model_ner, text):
      '''
      This function apply the model over the text and return the result.
      '''
      doc = model_ner(text) 
      return doc

    def get_data_from_list_of_lemmas_default_first (self, l_terms, lang, levels):
      '''
      This function receives a list of terms and processes and returns the data of the first
      babelnet matching terms found by every lemma in l_terms, and uses the lemma as identifier tag.
      '''
      l_id_result = []
      l_lemma_result = []
      
      for lemma in l_terms:
        data = self.get_only_data_from_lemma(normalize_text(lemma), lang)
        if (len(data) == 0 and not 'id' in data):
          continue
        
        l_id_result.append(data[0]['id'])
        l_lemma_result.append(normalize_text(lemma))
      return self.get_data_from_list_of_ids_and_tags(l_id_result, l_lemma_result, lang, levels)

    def get_data_from_list_of_lemmas_default_all (self, l_terms, lang, levels):
      '''
      This function receives a list of terms and processes and returns the data of all the
      babelnet matching terms found by every lemma in l_terms, and uses the lemma as identifier tag.
      '''
      l_id_result = []
      l_lemma_result = []
      
      for lemma in l_terms:
        data = self.get_only_data_from_lemma(normalize_text(lemma), lang)
        if (len(data) == 0 and not 'id' in data):
          continue
        for item in data:
          if not ('id' in item and item['id']):
            continue
          l_lemma_result.append(normalize_text(lemma))
          l_id_result.append(item['id'])
      return self.get_data_from_list_of_ids_and_tags(l_id_result, l_lemma_result, lang, levels)

    def get_data_from_list_of_ids_and_tags (self, l_ids, l_tags, lang, levels):
      '''
      This function receives a list of ids and tags, and returns the processed babelnet data from every id
      in the corresponding tag index.
      '''
      pattern_return = {}
      if(len(l_ids) != len(l_tags)):
        return 0
      for i in range(len(l_ids)):
        d_lemma_childs = self.get_data_from_id_and_hypo_by_level(l_ids[i], lang, l_tags[i], levels)
        pattern_return = { key:pattern_return.get(key,[])+d_lemma_childs.get(key,[]) for key in set(list(pattern_return.keys())+list(d_lemma_childs.keys())) }
      
      return self.create_pattern(pattern_return, lang)

        

    def get_data_from_list_of_ids (self, l_ids, lang, levels):
      '''
      This function receives a list of ids and returns the babelnet data, and it uses the id found lemma as
      identifying tag.
      '''
      tag = {}
      pattern_return = {}
      for id in l_ids:
        data = self.get_only_data_from_id(id, lang)
        
        if(data[0]['lemma']):
          tag[id] = data[0]['lemma']
        else:
          tag[id] = False
      for id in l_ids:
        if(not tag[id]):
          continue
        d_lemma_childs = self.get_data_from_id_and_hypo_by_level(id, lang, tag[id], levels)
        pattern_return = { key:pattern_return.get(key,[])+d_lemma_childs.get(key,[]) for key in set(list(pattern_return.keys())+list(d_lemma_childs.keys())) }
      return self.create_pattern(pattern_return, lang)

    def execute_async (self, task, args):
      '''
      This function is used to execure task asynchronously and returns the executing thread.
      '''
      thread = Thread(target= task, args=args)
      thread.start()
      return thread
