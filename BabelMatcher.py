#!pip install -U pip setuptools wheel
#!pip install -U spacy
#!python -m spacy download en_core_web_sm

import spacy
from spacy.tokens import Span
from spacy.language import Language
from spacy import displacy as dspl
import time
from threading import Thread
from pathlib import Path
import pandas as pd

from string import punctuation

import requests
import json


class BabelTermsMatcher:

    COLORS = [
        "pink",
        "blue",
        "white",
        "gray",
        "red"
    ]


    def __init__ (self, key, waitTime = 360, doNotWaitForServer = False):
      self.key = key
      self.waitTime = waitTime
      self.waiting = False
      self.doNotWaitForServer = doNotWaitForServer
      self.latestOperation = None
      self.latestOperationResult = None
      self.currentNER_Model = None
      self.data = None
    
    def load_data_from_padchest(self, data_path):
      raw_data = pd.read_csv(data_path, index_col=0)
      #print("--------------------------")
      #print(list(raw_data['Report']))
      #print("--------------------------")
      #self.data = [item for item in raw_data['Report']]
      self.data = list(raw_data['Report'])
      
    #---------------------------------- save NER model --------------------------------------
    def save_model(self, model, path):
      model.to_disk(path)
      return

    def save_current_model(self, path):
      if(self.currentNER_Model):
        self.currentNER_Model.to_disk(path)
        return 1
      else:
        print("No model to save")
        return 0
    #----------------------------------------------------------------------------------------

    #---------------------------------- save NER model --------------------------------------
    def load_model(self, path):
      model = spacy.load(path)
      return model

    def load_to_current_model(self, path):
      self.currentNER_Model = spacy.load(path)
      return self.currentNER_Model
    #----------------------------------------------------------------------------------------

    #---------------------------------- stage 1 ----------------------------------------
    def get_hypernom(self, id, lang):
        return_data= []
        
        data = []
        url = "https://babelnet.io/v8/getOutgoingEdges?id={0}&targetLang={1}&key={2}".format(id, lang, self.key)
        self.waiting = True
        response = requests.request("POST", url)

        while(response.status_code == 403):
            if(self.doNotWaitForServer):
              self.latestOperation = "get_hypernom"
              self.latestOperationResult = return_data
              self.waiting = False
              return return_data
            print("Waiting, coin spend !!!!!!")
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
          relation = pointer.get('name')
          group = pointer.get('relationGroup')

          if ('HYPONYM' == group and language == lang):
            return_data.append(target);

        self.latestOperation = "get_hypernom"
        self.latestOperationResult = return_data
        return return_data

    def get_hypernom_with_levels (self, id, lang, levels):
        ret_data = [id]
        current_l = [id]
        seen_ids = []
        
        for i in range(levels):
          level_l = []

          for id_v in current_l:
            if (id_v in seen_ids):
              continue
            else:
              hyper_l = self.get_hypernom(id_v, lang) 
              level_l.extend(hyper_l)
              ret_data.extend(hyper_l)
              seen_ids.append(id_v)

          current_l = level_l
        
        return_data = list(set(ret_data))
        
        self.latestOperation = "get_hypernom_with_levels"
        self.latestOperationResult = return_data
        return return_data
      
    #----------------------------------------------------------------------------------------
    
    #---------------------------------- stage 2 ---------------------------------------------

    def get_data_from_id_with_tag (self, id, lang, tag):
        ret_dic = {}
        ret_dic[tag] = set()

        url = "https://babelnet.io/v8/getSynset?id={0}&targetLang={1}&key={2}".format(id, lang, self.key)
        self.waiting = True
        response = requests.request("POST", url)

        while(response.status_code == 403):
            if(self.doNotWaitForServer):
              ret_dic[tag] = list(ret_dic[tag])

              self.latestOperation = "get_data_from_id_with_tag"
              self.latestOperationResult = ret_dic
              self.waiting = False
              return ret_dic
            print("Waiting, coin spend !!!!!!")
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
        #print(data)
        for val in data['senses']:
          if(tag in ret_dic):
            ret_dic[tag] = ret_dic[tag].union( set([(val['properties']['lemma']['lemma']).lower().replace('_', ' ')]) )
          else:
            ret_dic[tag] = set([(val['properties']['lemma']['lemma']).lower()])

        ret_dic[tag] = list(ret_dic[tag]) 

        self.latestOperation = "create_dic_from_instance"
        self.latestOperationResult = ret_dic
        return ret_dic

    #----------------------------------------------------------------------------------------
    
    #---------------------------------- stage 3 ---------------------------------------------
    def get_data_from_id_and_hyper_by_level(self, id, lang, tag, levels):
        hyper_by_lvl_l = self.get_hypernom_with_levels(id, lang, levels)
        ret_dic = {}
        ret_dic[tag] = [] 
        #print(hyper_by_lvl_l)

        for id in hyper_by_lvl_l:
          ret_data_dic = self.get_data_from_id_with_tag(id, lang, tag)
          if(ret_data_dic):
            ret_dic[tag] = ret_dic[tag] + ret_data_dic[tag]

        ret_dic[tag] = list(set(ret_dic[tag]))

        self.latestOperation = "get_data_from_id_and_hyper_by_level"
        self.latestOperationResult = ret_dic
        return ret_dic
    
    #---------------------------------- stage 4 ---------------------------------------------
    def get_only_data_from_id(self, id, lang):
        ret_dic = []

        url = "https://babelnet.io/v8/getSynset?id={0}&targetLang={1}&key={2}".format(id, lang, self.key)
        self.waiting = True
        response = requests.request("POST", url)

        while(response.status_code == 403):
            if(self.doNotWaitForServer):
              self.latestOperation = "get_only_data_from_id"
              self.latestOperationResult = ret_dic
              self.waiting = False
              return ret_dic
            print("Waiting, coin spend !!!!!!")
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
        ret_list=[]
        sourceSense_l = []
        #print(data)
        for val in data['senses']:
          # POTENTIAL_NEAR_SYNONYM_OR_WORSE
          if(val['properties']['lemma']['type'] != 'HIGH_QUALITY'):
            continue
          if(val['properties']['synsetID']['id'] in sourceSense_l):
            continue
          item = {
              'lemma': val['properties']['lemma']['lemma'],
              'glosses': data['glosses']
          }
          sourceSense_l.append(val['properties']['synsetID']['id'])
          #print(sourceSense_l)
          #print(val)
          #print();
          ret_list.append(item)
        #print(ret_list)

        self.latestOperation = "get_data_from_resp"
        self.latestOperationResult = ret_list
        return ret_list

    # -----------------------------------------------
    # get data from a lemma, return a list of ids
    # -----------------------------------------------
    
    def get_data_from_lemma(self, lemma, lang):
        ret_resp = []
        resp_data_list = []

        url = "https://babelnet.io/v8/getSynsetIds?lemma={0}&searchLang={1}&key={2}".format(lemma, lang, self.key)
        self.waiting = True
        response = requests.request("POST", url)

        while(response.status_code == 403):
            if(self.doNotWaitForServer):
              self.latestOperation = "get_data_from_lemma"
              self.latestOperationResult = resp_data_list
              self.waiting = False
              return resp_data_list
            print("Waiting, coin spend !!!!!!")
            time.sleep(self.waitTime)
            
            # Request again after the waiting time
            response = requests.request("POST", url)
        self.waiting = False

        data = json.loads(response.text)
        ret_resp.extend(data)
        #print(ret_resp)
   
        for item in ret_resp:
          resp_data = self.get_only_data_from_id(item['id'], lang)
          resp_data_list.append({
              'id': item['id'],
              'data': resp_data
          })
          #print(item['id'], resp_data_list)
        
        self.latestOperation = "get_data_from_lemma"
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
            ret_data.append(ent_to_add);

        self.latestOperation = "get_glosses_and_id_from_lemma"
        self.latestOperationResult = [lemma, ret_data]
        return [lemma, ret_data]


    #---------------------------------- stage 7 ---------------------------------------------

    def create_pattern (self, data):
        pattern = []
        for key in data:
          item = {
              "label": key,
              "pattern": [
                 {
                     "TEXT": 
                     {
                         "FUZZY1": 
                        {
                          "IN": data[key],
                          "NOT_IN": [' '] + list(punctuation)
                        }
                     }
                 } 
              ]
          }
          pattern.append(item)

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

    @Language.component("ignore_prepositions")
    def ignore_prepositions(doc):
      for i in range(len(doc)):
          print("-------------------------------")
          print(doc[i])
          print("-------------------------------")
          if doc[i].dep_ == "prep" or doc[i].dep_ == "aux" or doc[i].is_punct or doc[i].text == ' ':
              # Ignore prepositions by setting a custom flag
              #token.ignore = True
              print("++++++++++++++++++")
      return doc


    def create_NER_model (self, pattern, lang):
        if (lang == 'EN'):
          nlp = spacy.load("en_core_web_sm", disable=["ner"])
        else:
          nlp = spacy.blank("en")

        #nlp.add_pipe("ignore_prepositions", name="ignore_prepositions", last=True)
        ruler = nlp.add_pipe("entity_ruler")
        
        ruler.add_patterns(pattern)

        self.currentNER_Model = nlp
        return nlp, ruler

    def display_doc_by_labels(self, doc):
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

    #this is only use when working with jupyterLab, jupyterNotebook or colab
    def apply_and_show_model (self, model_ner, text):
        doc = model_ner(text) 
        for ent in doc.ents:
          print(ent.text, ent.label_)

        self.display_doc_by_labels(doc)

    def apply_model (self, model_ner, text):
        doc = model_ner(text) 
        return doc
    # ---------------------------------------  NEEDS TESTING ------------------------------------------------------

    def get_data_from_list_of_lemmas_default_first (self, l_terms, lang, levels):
        l_id_result = []
        l_lemma_result = []
        
        for lemma in l_terms:
          data = self.get_glosses_and_id_from_lemma(lemma, lang)

          if not (len(data[1]) > 0 and 'id' in data[1][0] ):
            continue
          
          l_id_result.append((data[1])[0]['id'])
          l_lemma_result.append(data[0])

        return self.get_data_from_list_of_ids_and_tags(l_id_result, l_lemma_result, lang, levels)

    def get_data_from_list_of_lemmas_default_all (self, l_terms, lang, levels):
        l_id_result = []
        l_lemma_result = []
        
        for lemma in l_terms:
          data = self.get_glosses_and_id_from_lemma(lemma, lang)

          if (not (len(data[1]) > 0)):
            continue

          for item in data[1]:
            if not ('id' in item and item['id']):
              continue

            l_lemma_result.append(data[0])
            l_id_result.append(item['id'])

        return self.get_data_from_list_of_ids_and_tags(l_id_result, l_lemma_result, lang, levels)

    def get_data_from_list_of_ids_and_tags (self, l_ids, l_tags, lang, levels):
        pattern_return = {}

        if(len(l_ids) != len(l_tags)):
          return 0

        for i in range(len(l_ids)):
          d_lemma_childs = self.get_data_from_id_and_hyper_by_level(l_ids[i], lang, l_tags[i], levels)
          #pattern_return = {key: pattern_return[key] + d_lemma_childs[key] for key in set(d_lemma_childs) & set(pattern_return)}

          pattern_return = { key:pattern_return.get(key,[])+d_lemma_childs.get(key,[]) for key in set(list(pattern_return.keys())+list(d_lemma_childs.keys())) }
        
        #return pattern_return
        return self.create_pattern(pattern_return)

        

    def get_data_from_list_of_ids (self, l_ids, lang, levels):
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
          d_lemma_childs = self.get_data_from_id_and_hyper_by_level(id, lang, tag[id], levels)
          pattern_return = { key:pattern_return.get(key,[])+d_lemma_childs.get(key,[]) for key in set(list(pattern_return.keys())+list(d_lemma_childs.keys())) }

        return self.create_pattern(pattern_return)

    def execute_async (self, task, args):
        thread = Thread(target= task, args=args)
        thread.start()
        return thread

    #----------------------------------------------------------------------------------------
