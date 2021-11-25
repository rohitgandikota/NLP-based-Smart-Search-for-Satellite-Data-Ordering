# -*- coding: utf-8 -*-
"""
Created on Tue Sep 22 22:42:51 2020
@author: Rohit Gandikota
"""
import numpy as np
import json
import re
import os
#import logging
import datetime
import urllib
from .bhoonidhi_helper import getBhoonidhiProcessedParameters,  getBhoonidhiDates, getEventTypesBhoonidhi, getBhoonidhiEventDate, getBhoonidhiFilterText,findBhoonidhiLocations, findBhoonidhiEvents, findBhoonidhiSatellites, getFilteredSatSen,getBhoonidhiEventSatellites
from .utils import findParameters, findDates, getTokensPOS, preprocess
#%% Proxy settings
#import nltk
#os.environ["https_proxy"] = "http://user_name:password@proxy.inst.com:port"
#nltk.set_proxy("http://user_name:password@proxy.inst.com:port")
#logging.basicConfig(filename='bhoonidhiSmartSearch.log', filemode='a', format='%(name)s - %(levelname)s - %(message)s')
#%% Smart Searching for Bhoonidhi
          
def bhoonidhiSmartSearch(user_text, write_json = False):
    '''
    Bhoonidhi Smart Search Master function which outputs the JSON query from a user query which is in casual english language
    
    Parameters
    ----------
    user_text : str
        User query string
    write_json : boolean, optional
        An optinal flag whether to store the json as a file in the local system / backend

    Returns
    -------
    json 
        Final json that will be passed to bhoonidhi server for fetching the results for the query raised by user.
        
    Raises
    ------
    Too many requests
        Error if user asks for all the satellite data available
    No input 
        Error if user query contains no relevant query parameters for a satellite data search
    Internal Error
        If any unforseen exception occurs in the python script
    '''
#    bup_txt = user_text
    feature_count = 0
    # Preprocessing the text query to remove harmful expressions and get code friendly text parameters
    
    user_text = preprocess(user_text) 
    #################################################################### Finding dates in the string    
    init_date, final_date, user_text, feature_count = findDates(user_text,feature_count)
    ################################################################## tokenize and parts of speech classification
    user_pos, user_tokens = getTokensPOS(user_text)
    ################################################################# Search for event based
    eventTypes = getEventTypesBhoonidhi()
    trueVals = [x for x in eventTypes if re.search(x,user_text)]
    events = []
    if trueVals !=[]:
        events = findBhoonidhiEvents(user_text, user_tokens)
    
#    if re.search(r'flood',user_text) or re.search(r'avalanche',user_text):
        
    
    ################################################################## Finding geo-locations in the string
    location = findBhoonidhiLocations(user_text)
    feature_count+=len(location)
   
    ######################################################################## Finding satellite in the tokens (Uses an improved algorithm for curated results)
    try:
        user_sat, user_tags, user_pos = findBhoonidhiSatellites(user_pos)
    except Exception as e:
        jsons = {}
        jsons[1]={}
        jsons[1]['Error']=f'Smart Search Error. Could not find satellite/sesnor configuration in the text: {e}'
        return jsons
        
    
    ################################################################## Get advanced filter parameters from tokenised POS
    if len(user_pos)>0:
        parameters = findParameters(user_pos)
        parameters = getBhoonidhiProcessedParameters(parameters,user_pos)
        feature_count+=len(parameters)
    else:
        parameters = []
    for param in parameters:
        if param[-1] == 'resolution':
            resols = param[0]
            for res in resols:
                if not res in user_tags:        
                    user_tags.append(res.lower())
            if not 'resolution' in user_tags:
                user_tags.append('resolution')
    ################################################################## Further curate the satellites and sensors based on resolution, paid, sensor type etc
    try:
        SatSen, resolution_check = getFilteredSatSen(user_sat,user_tags)
    except Exception as e:
        jsons = {}
        jsons[1]={}
        jsons[1]['Error']=f'Smart Search Error. {e}'
        return jsons
    EventSatFlag=False
    if len(SatSen) == 0 and len(events)==0:
        jsons = {}
        jsons[1]={}
        jsons[1]['Error']=f'Smart Search Error. Could not find any specific satellite/sensor request. Kindly enter a more accurate query'
        return jsons
    else:
        if len(SatSen) == 0:
            EventSatFlag=True
        else:
            output = ""
            for sat in SatSen:
                output += f'{sat},'
            output=output[:-1]
    # Check if the query given is junk
    feature_count+=len(SatSen)      
#    resolution_check = bup_txt
    if feature_count>0:  
#        logging.info(f'Found {feature_count} number of features in the query')
        jsons = {}
        cnt = 1
        ############################################################# Pack the json 
        if not len(location)>0:
            location=[['sad']]
        if len(events)>0:                
            for event in events:
                json_dict = {}
                json_dict["filters"]="{}"
                json_dict["userId"]="T"
                json_dict["offset"]="0"
                if EventSatFlag:
                    event_user_sats = getBhoonidhiEventSatellites(event)
                    EventSatSen = getFilteredSatSen(event_user_sats,user_tags)
                    output = ""
                    for sat in EventSatSen:
                        output += f'{sat},'
                    output=output[:-1]
                json_dict['selSats']=output 
                json_dict['resolutioncategory'] = resolution_check                  
                if final_date != datetime.datetime.now().strftime("%d %B, %Y"):
                    json_dict['sdate'] = (getBhoonidhiDates(init_date)) 
                    json_dict['edate'] = (getBhoonidhiDates(final_date))  
                else:
                    json_dict['sdate'] =(getBhoonidhiDates(getBhoonidhiEventDate(event[5]))) 
                    json_dict['edate'] = (getBhoonidhiDates(getBhoonidhiEventDate(event[6]))) 
                json_dict['query']='area'
                location = event[4].split(',')
                if len(location)==2:
                    json_dict['queryType']='location'
                    json_dict['lat']=location[0]
                    json_dict['lon']=location[1]
                    json_dict['radius']=event[2]
                elif len(location)>2 :
                    json_dict['queryType']='polygon'
                    json_dict['brlat']=location[4]
                    json_dict['brlon']=location[5]
                    json_dict['tllat']=location[0]
                    json_dict['tllon']=location[1]
                if len(parameters)>0:
                     json_dict = getBhoonidhiFilterText(parameters,SatSen,json_dict,location_flag=1)
                json_dict['selSats']= urllib.parse.quote(json_dict['selSats'])
                json_dict['selSats'] = re.sub('%28','(',json_dict['selSats'])
                json_dict['selSats'] = re.sub('%29',')',json_dict['selSats'])
                json_dict['filters']= urllib.parse.quote(json_dict['filters'])
                json_dict['filters'] = re.sub('%28','(',json_dict['filters'])
                json_dict['filters'] = re.sub('%29',')',json_dict['filters'])
                jsons[cnt] = (json_dict)
            if write_json == True:
                json_path = "D:\\Projects\\Bhoonidhi\\SmartOrdering\\user_request.json"
                if os.path.exists(json_path):
                    os.remove(json_path)
                for i in range(len(jsons)):
                    with open(json_path, "w+") as outfile:  
                            json.dump(jsons[i], outfile)
            return jsons
        else:
            for city in location:
                json_dict = {}
                json_dict["filters"]="{}"
                json_dict["userId"]="T"
                json_dict["offset"]="0"
                json_dict['selSats']=output
                json_dict['resolutioncategory'] = resolution_check 
                json_dict['sdate'] = (getBhoonidhiDates(init_date)) 
                json_dict['edate'] = (getBhoonidhiDates(final_date))
                json_dict['query']='date'
                json_dict['queryType']='date'
                location_flag=0
                if len(parameters)> 0:
                    if 'lat' in np.array(parameters)[:,-1]:
                        json_dict['query']='area'
                        json_dict['queryType']='location'
                        location_flag=1
                if len(city)== 3:
                    json_dict['lat']=city[1]
                    json_dict['lon']=city[2]
                    json_dict['query']='area'
                    json_dict['queryType']='location'
                    location_flag=1
                    try:
                        if not len(json_dict['radius'])>0:
                            json_dict['radius']= '10'
                    except:
                        json_dict['radius']= '10'
                elif len(city) == 2:
                    json_dict['shapefilename']=city[1]
                    json_dict['shpCat']='existingShp'
                    json_dict['query']='area'
                    json_dict['queryType']='shape'
                    location_flag=1
                
                if len(parameters)>0:
                    try:
                        json_dict = getBhoonidhiFilterText(parameters,SatSen,json_dict,location_flag)
                    except Exception as e:
                        if str(e).startswith('Please'):
                            jsons = {}
                            jsons[1]={}
                            jsons[1]['Error']='Smart Search Error. ' + str(e)
                            return jsons
                json_dict['selSats']= urllib.parse.quote(json_dict['selSats'])
                json_dict['selSats'] = re.sub('%28','(',json_dict['selSats'])
                json_dict['selSats'] = re.sub('%29',')',json_dict['selSats'])
                json_dict['filters']= urllib.parse.quote(json_dict['filters'])
                json_dict['filters'] = re.sub('%28','(',json_dict['filters'])
                json_dict['filters'] = re.sub('%29',')',json_dict['filters'])
                jsons[cnt] = (json_dict)
                cnt+=1
            if write_json == True:
                json_path = "D:\\Projects\\Bhoonidhi\\SmartOrdering\\user_request.json"
                if os.path.exists(json_path):
                    os.remove(json_path)
                for i in range(len(jsons)):
                    with open(json_path, "w+") as outfile:  
                            json.dump(jsons[i], outfile)
            return (jsons)
    else:   
#        logging.warning('No relevant features found in the query')
        jsons = {}
        jsons[1]={}
        jsons[1]['Error']='Smart Seach Error. No relevant parameters found in the query'
        return jsons
        
        
        
#%% Testing code platform
if __name__ == "__main__":   
    user_text = 'Get recent landsat 8 data'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Get me sentinel data from hyderabad with radius of 100 km with resolution coarser than 30 mts latitude 10.56 and longitude of 72.35 and cloud coverage of less than 5 %'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Data from 1st December 2020 radius 100 km 30 cloud l8 oli latitude 12.34 and longitude 76.25'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Hyderabad from 14th September 2020 radius 100 km 15% cloud l8 oli latitude = 17.33 and longitude = 78.5 '
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'get high resolution free data images over kerala floods location from 2 years till today'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Lat 17.38 Lon 78.48 radius 300 landsat 8 oli from the last 3 year'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'resolution more than 50 m and radius of 10 km around hyderabad landsat 8 data'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Get Hyderabad pingpong with medium resolution'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'get satellite data more than 100 Meter Resolution'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'get free data for past two years over guntur area of 400 km2'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'get priced data for past two months over hyderabad and guntur area of 400 km2'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'get risat 2b1 spotlight mode with incidence angle range 12-55 from 01 August 2020 to 04 february 2021'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'rs2 liss3  03-feb-2021 path 97'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'resourcesat2 liss3 data from 01 June 2020 till today with path 103 '
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)    
    user_text= "get kerala floods data with resolution 6 mts"
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text= "get nvs data from last year"
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text="Resourcesat AWIFS Data 15th July 2020 to 20th September 2020 Hyderabad"
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'novasar standard data last year'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = "Data from January radius 10 km 15 cloud l8 oli latitude  17.33 and longitude  78.5"
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = "get risat 2b1 spotlight mode with incidence angle range 12 to 55 from 01 August 2020 to 04 february 2021"
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text='get risat2b2 data with horizontal transpol and ascending node'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'L8 hyderabad and bangalore 50 km radius from 23rd January till 02-02-2020'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'resolution more than 50 m and radius of 10 km around hyderabad landsat 8 data'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'resourcesat2 series liss3 data from 01 June 2020 till today with path 103'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Get me sentinel data from hyderabad with radius of 100 km and cloud coverage of less than 5'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
    user_text = 'Get  cloud free RS2 and R2A data from Jan 1 till  31st April over India'
    json_obj =  bhoonidhiSmartSearch(user_text)
    print(json_obj)
