
import spacy
import sys
import os
import re
import json
import datetime
from pathlib import Path
from collections import defaultdict


REGEX_LIST = []
RESULT_FILE = ""
ENTITY_NAME = []
ENTITY_TYPE = []
DATE_MATCHER = r'[^a-zA-Z0-9]*(?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[a-z\s,.]*(?:\d{1,2}[-/th|st|nd|rd)\s,]*)+(?:\d{2,4})+'

def write_or_append_to_file(filename, content):
    if not os.path.exists(filename):
       filename.touch()
    content = content + " \n"    
    with open(filename, 'a') as f:
         f.write(content)

def find_matches(text, regexList):
    match_list = []
    index_list = []
    counter=-1
    for regex in regexList:
        counter=counter+1
        ent_type = ENTITY_TYPE[counter]           
        for match in re.finditer(regex, text, re.IGNORECASE):
            if(match):
               match_list.append(match)
               index_list.append(ent_type)
    
    return match_list, index_list
  

def read_file_path(file_path):
    with open(file_path, 'r') as file:
         content = file.read()
    return content


def read_file_by_line(file_path):
    line_text = []
    with open(file_path, 'r') as file:
         for line in file:
             line_text.append(line)
    return line_text

def collecting_page_data(dir_path):
    files_list = list_directory_files(dir_path, ".txt")
    text_list = []
    page_list = []
    for fpath in files_list:
        page_number, page_text = page_text_number(fpath)
        text_list.append(page_text)
        page_list.append(page_number)

    return page_list, text_list

def list_directory_files(dir_path, extension):
    flist = []   
    for filename in os.listdir(dir_path):
        if filename.endswith(extension):
           filepath = os.path.join(dir_path, filename)
           flist.append(filepath)
    return flist

def page_text_number(file_path):
    content_list = read_file_by_line(file_path)
    filecontent = ' '.join(content_list)
    filterContent = re.sub(r'\s+', ' ', filecontent)
    pnumber = 0
    file_without_extension = Path(os.path.basename(file_path)).stem    
    match = re.search(r'\d+', file_without_extension)
    if match:
       pnumber = int(match.group())
    return pnumber, filterContent

def create_regex_cloud(file_path):
    text_list = read_file_by_line(file_path)
    for lst in text_list:
        rtext = lst.rstrip()
        reg = create_regex(rtext)                
        REGEX_LIST.append(reg)

def load_wordclouds_info(file_path):
    entity_names = []
    entity_types = []
    with open(file_path, 'r') as file:
         content = file.read()
    data = json.loads(content)     
    for item in data:
        name = item['name']
        ENTITY_NAME.append(name)
        ENTITY_TYPE.append(item['type'])
        rtext = name.rstrip()
        REGEX_LIST.append(create_regex(rtext))
    
    #return  entity_names, entity_types


def create_regex(word):    
    spaced_word = r'\s*'.join(list(word))
    pattern = rf'\b\w*{spaced_word}\w*\b'    
    return pattern

def found_date(text, startIndex):
    date_result = ""
    endIndex = len(text)
    try:
        portion_after_endindex = text[startIndex:endIndex]
        #date_pattern = r'(?:^[^a-zA-Z0-9]*)?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[a-z\s,.]*(?:\d{1,2}[-/th|st|nd|rd)\s,]*)+(?:\d{2,4})+'
        date_pattern = r'[^a-zA-Z0-9]*(?:\d{1,2}[-/th|st|nd|rd\s]*)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)?[a-z\s,.]*(?:\d{1,2}[-/th|st|nd|rd)\s,]*)+(?:\d{2,4})+'
        match = re.search(date_pattern, portion_after_endindex)        
        if match:        
            start, end = match.span()
            if(start < 3):
               date_result = match.group()
    except:
          date_result =""          
    finally:
            cleaned_part = re.sub(r'^[^a-zA-Z0-9]+', '', date_result)
            return cleaned_part

def found_provider(text, startIndex):
    result = ""
    endIndex = len(text)
    portion_after_endindex = text[startIndex:endIndex] 
    text_4_words = portion_after_endindex.split()[:4]
    words_text = ' '.join(text_4_words)
    first_4_words = re.sub(r'\s+', ' ', words_text).strip()    
    #print(f"wordsss : {first_4_words}")
    try:               
        nlp = NLP_MODEL ### spacy.load("en_core_web_sm")    
        doc = nlp(first_4_words)
        count=0
        #print("nlp2222")
        for ent in doc.ents:
            count = count + 1            
            #print(f"XXX--- {ent.text} YYY: {ent.label_}")
            if ent.label_ in ["PERSON", "ORG", "GPE", "LOC"]:            
              result = result + " " + ent.text
            elif not (result and result.strip()):
                 continue         
            elif ent.label_ not in ["PERSON", "ORG", "GPE", "LOC"]:
                break        
    except:
            result =""
    finally:
            #print(f"resulss: {result}")                
            return result

def found_hospital(text, start):
    result = ""
    result = hospital_provider_before(text, start)
    if(len(result) == 0):
      result = hospital_provider_after(text, start)
    return result

def found_physician(text, startIndex):
    result = ""
    endIndex = len(text)
    portion_after_endindex = text[startIndex:endIndex] 
    text_3_words = portion_after_endindex.split()[:3]
    words_text = ' '.join(text_3_words)
    first_3_words = re.sub(r'\s+', ' ', words_text).strip()        
    try:               
        nlp = NLP_MODEL ### spacy.load("en_core_web_sm")    
        doc = nlp(first_3_words)
        count=0
        for ent in doc.ents:
            count = count + 1
            if ent.label_ in ["PERSON"]:            
              result = result + " " + ent.text
            elif not (result and result.strip()):
                 continue         
            elif ent.label_ not in ["PERSON"]:
                break        
    except:
            result =""
    finally:
            return result


def hospital_provider_after(text, startIndex):
    result = ""
    endIndex = len(text)
    portion_after_endindex = text[startIndex:endIndex] 
    text_4_words = portion_after_endindex.split()[:4]
    words_text = ' '.join(text_4_words)
    first_4_words = re.sub(r'\s+', ' ', words_text).strip()        
    try:               
        nlp = NLP_MODEL ### spacy.load("en_core_web_sm")    
        doc = nlp(first_4_words)
        count=0
        for ent in doc.ents:
            count = count + 1
            if ent.label_ in ["ORG", "GPE", "LOC"]:            
              result = result + " " + ent.text
            elif not (result and result.strip()):
                 continue         
            elif ent.label_ not in ["ORG", "GPE", "LOC"]:
                break        
    except:
            result =""
    finally:
            return result

def hospital_provider_before(text, startIndex):
    result = ""
    endIndex = len(text)
    portion_after_endindex = text[startIndex-6:startIndex] 
    text_4_words = portion_after_endindex.split()[:4]
    words_text = ' '.join(text_4_words)
    first_4_words = re.sub(r'\s+', ' ', words_text).strip()        
    try:               
        nlp = NLP_MODEL ### spacy.load("en_core_web_sm")    
        doc = nlp(first_4_words)
        count=0
        for ent in doc.ents:
            count = count + 1
            if ent.label_ in ["ORG", "GPE", "LOC"]:            
              result = result + " " + ent.text
            elif not (result and result.strip()):
                 continue         
            elif ent.label_ not in ["ORG", "GPE", "LOC"]:
                break        
    except:
            result =""
    finally:
            return result

def entity_trace_bytype(entityType, text, startIndex):    
    if(entityType == "date"):
       return found_date(text, startIndex)
    if(entityType == "provider"):
       #print("provider type found")
       return found_provider(text, startIndex)
    if(entityType == "hospital"):
      return found_hospital(text, startIndex)
    if(entityType == "physician"):
      return found_physician(text, startIndex)

    return ""

def process_run(dir_path):
    # Collect all text files text and its page number. 
    # page_list : file page number
    # page_text: text of the page.
    # in find matches : using iterator 
    page_list, page_text = collecting_page_data(dir_path)
    regex_list = REGEX_LIST
    
    for tokenIndex in range(len(page_text)):
        main_str = page_text[tokenIndex]
        matches_collection, index_collection = find_matches(main_str, regex_list)
        indexCount = -1
        for match in matches_collection:
            indexCount = indexCount + 1
            #print(f"vvv: {index_collection[indexCount]}")                                
            if(match):
               etype = index_collection[indexCount]
               start, end = match.span()
               entity_value = entity_trace_bytype(etype, main_str, end)
               cont_txt = f"page: {page_list[tokenIndex]} Matched: {match.group()} value: {entity_value} start {start} end {end}"
               write_or_append_to_file(RESULT_FILE, cont_txt)
                
# Use command : 
# first parameter : text file directory path : "E:\\DELETES_9000\\IndexingPython\\datafiles"
# second parameter: search words path : "E:\\DELETES_9000\\IndexingPython\\words_cloud.txt"
# third parameter : path of output file : ""E:\\DELETES_9000\\IndexingPython\\results.txt"
if __name__ == '__main__':   
   arguments = sys.argv
   # Assign all input parameter in varaibles
   dir_path = arguments[1]
   filter_path = arguments[2]
   RESULT_FILE = arguments[3]
   
   outfile_path = Path(RESULT_FILE)   
   outfile_path.touch() #Create blank file of output
   
   #Create all possible regex for each from words_cloud.txt file
   #create_regex_cloud(filter_path)
   load_wordclouds_info(filter_path)
   
   NLP_MODEL = spacy.load("en_core_web_sm")
   
   stxt = f"       Start: {datetime.datetime.now()}"
   write_or_append_to_file(RESULT_FILE, stxt)
   process_run(dir_path)
   stxt = f"       End: {datetime.datetime.now()}"
   write_or_append_to_file(RESULT_FILE, stxt)
   
