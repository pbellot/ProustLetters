import json 
import pycurl
import time
import os
from io import BytesIO # Core tools for working with streams

def api_letters_list(query_url):
    
    buffer = BytesIO() 
    c = pycurl.Curl()
    c.setopt(c.URL, query_url)
    c.setopt(c.HTTPHEADER, ['accept: application/json'])
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()
    body = buffer.getvalue()
    # print(body) # need something to handle redirection ? 
    json_answer = json.loads(body.decode('iso-8859-1'))
    return json_answer 


def prep_letters_query(json_answer, target_api):
    # target API : Prod     "https://proust.elan-numerique.fr/api/letter-preprod"
            #  or preprod : "https://proust-preprod.elan-numerique.fr/api/letter-preprod/"
    uris_to_call = []
    for letter in json_answer: 
        uris_to_call.append(target_api + letter["id"])
    return uris_to_call 

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]    


def query_letters_files(query_list):
    
    buffer_results = []

    ######
    start_time = time.time()
    ######
    
    uri_chunks = chunks(query_list, 30)
    
    
    cnt = 0 
    
    datalist_cnt = 0
    
    for uri_chunk in uri_chunks:
        
        
        #query_array = uri_chunk
        curl_count = len(uri_chunk)
        # curl_array = []
        m = pycurl.CurlMulti()
    
        for i in range(0, curl_count, 1):
            
            datalist_cnt += 1
            url = uri_chunk[i]
            buffer = BytesIO()
            handle = pycurl.Curl()
            handle.setopt(pycurl.URL, url)
            handle.setopt(pycurl.HTTPHEADER, ['accept: application/json'])
            handle.setopt(pycurl.WRITEDATA, buffer)
            req = (url, buffer)
            m.add_handle(handle)
            
            
            buffer_results.append(req)
            
            
            # Perform multi-request.
            # This code copied from pycurl docs, modified to explicitly
            # set num_handles before the outer while loop.
            SELECT_TIMEOUT = 1.0
            num_handles = curl_count
            while num_handles:
                ret = m.select(SELECT_TIMEOUT)
                if ret == -1:
                        continue
                while 1:
                        ret, num_handles = m.perform()
                        if ret != pycurl.E_CALL_MULTI_PERFORM:
                                break
        # basic way to to check progress 
        print(cnt)
        print("--- %s seconds ---" % (time.time() - start_time))
        cnt += 30 
                        
    
    
    ######
    print("--- %s seconds ---" % (time.time() - start_time))
    ######
    print(datalist_cnt)

    return buffer_results



def parse_save_xml(buffer_result, target_folder):
    
    for result in buffer_result:
        # print(result)
        body = result[1].getvalue()
        #  result[0] : 'https://proust-preprod.elan-numerique.fr/api/letter-preprod/03100', 
        #  result[1] : <_io.BytesIO object at 0x70b37dbb25c0>  that still needs to be parsed as json 
        
        json_object = json.loads(body.decode('iso-8859-1'))
    
        xml_data = json_object["content"]
        filename = json_object["filename"]
        file_path = target_folder + filename
    
        with open(file_path, "w") as out:
            print(file_path)
            out.write(xml_data)

# "recovered-files/"


# json_list = api_letters_list("https://proust-preprod.elan-numerique.fr/api/letters-preprod")
# query_list = prep_letters_query(json_list, "https://proust-preprod.elan-numerique.fr/api/letter-preprod/") 
# result = query_letters_files(query_list)
# parse_save_xml(result, "api-preprod-files/")

json_list = api_letters_list("https://proust.elan-numerique.fr/api/letters-preprod")
query_list = prep_letters_query(json_list, "https://proust.elan-numerique.fr/api/letter-preprod/") 
result = query_letters_files(query_list)
parse_save_xml(result, "/Users/Patrice/Proust/")