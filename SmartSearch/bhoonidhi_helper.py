# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 14:14:13 2020
@author: Rohit Gandikota
"""
import numpy as np
import re
import requests
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import nltk
import os
import urllib
from nltk.corpus import stopwords
import cx_Oracle
from multiprocessing.pool import ThreadPool


# Function to help understand what all available configurations are available. All imp info is stored here!!
def getAvailableSatSen():
    '''
    A Database call to fetch all the available satellite sensor configurations
    
    Parameters
    ----------
    void

    Returns
    -------
    list
        A list of satellite sensor configs in the master format [sat,sen,prod_type,sensor_type,open_paid,resolution,index_in_db,product_category]
    '''
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'
    try:
        <Database Operations>
    except:
        raise Exception('Database Error at SatSen Configuration')
    satsen = []
    for row in c:
        if 'strip' in row[6].lower():
            continue
        if row[2]!='-':
            sen = f'{row[1]}({row[2]})'
        else:
            sen = row[1]
        if row[14].lower()=='open_data':
            prod_type=f'_{row[5]}'
        else:
            prod_type=f''
        if [row[0],sen,prod_type,row[17],row[14]] not in satsen:
            
            satsen.append([row[0],sen,prod_type,row[17],row[14],row[12],row[19],row[6]])
    return (satsen)

def getBhoonidhiEventSatellites(event):
    '''
    Function to get event related satellite configs from event object
    
    Parameters
    ----------
    event : list
        Event object under consideration

    Returns
    -------
    list
        List of all the satellite configurations for the events as per database
    '''
    availSatSenConfigs =  getAvailableSatSen()
    UPGRADED_SATSENAVAIL = []
    EventSatSen = []
    for satsen in availSatSenConfigs:       
        UPGRADED_SATSENAVAIL.append(f'{satsen[0]}_{satsen[1]}{satsen[2]}${satsen[3]}${satsen[4]}${satsen[5]}')
    for sensor in event[0].split(','):
        for satsen in UPGRADED_SATSENAVAIL:
            if sensor.strip().lower() in satsen.lower():
                EventSatSen.append(satsen)
    return EventSatSen
    
# New function for a clean approached satellite and sensor combination detection in the search query  
def findBhoonidhiSatellites(user_pos):
    '''
    An upgraded and optimised function to find any satellite sensor configuration present in the query. Can also curate sensor type, imaging mode, etc.
    
    Parameters
    ----------
    user_pos : list
        List of tokenised parts of speech calculated words in the entire query

    Returns
    -------
    user_sat : list
        List of all the found satellite sensor configurations from the query
    user_tags : list
        List of all the tokens in the query after removing the tokens that belong to the fetched configurations
    user_pos_new : list
        List of new updated user_pos after removing the entries that belongs to the satsen config search
    '''
    availSatSenConfigs =  getAvailableSatSen()
    UPGRADED_SATSENAVAIL = []
    
    for satsen in availSatSenConfigs:
           
        UPGRADED_SATSENAVAIL.append(f'{satsen[0]}_{satsen[1]}{satsen[2]}${satsen[3]}${satsen[4]}${satsen[5]}${satsen[7]}')
    user_sat_club = []
    user_tags = []
    pos_remove_index = []
    i = -1
    for pos in user_pos:
        i+=1
        if pos[-1] == 'CD':
            if len(user_tags)>0:
                user_tags.pop(-1)
                user_tags.append(user_pos[i-1][0]+pos[0])
                pos_remove_index.pop(-1)
                pos_remove_index.append([i-1,i])
            else:
                user_tags.append(pos[0])
                pos_remove_index.append([i])
                
        else:
            user_tags.append(pos[0])
            pos_remove_index.append([i])
    i = -1
    pos_remove = []
    for tag in user_tags:
        i+=1
        user_sat_club_new = []
        curated_flag = False
        curated = []
        if len(user_sat_club) == 0:
            for sat_avail in UPGRADED_SATSENAVAIL:
                sat_avail_ = re.sub('-','',sat_avail)
                sat_avail_ = sat_avail_.split('$')[0]
                if re.sub('-','',tag) in sat_avail_.lower():
                    curated.append(sat_avail)
                    
            if len(curated)>0:
                user_sat_club_new.append(curated)
                pos_remove.append(pos_remove_index[i])    
            
        else:
            for club in user_sat_club:
                for sat_avail in club:
                    sat_avail_ = re.sub('-','',sat_avail)
                    sat_avail_ = sat_avail_.split('$')[0]
                    if re.sub('-','',tag) in sat_avail_.lower():
                        curated.append(sat_avail)
                        curated_flag = True
                        
                if curated_flag:
                    user_sat_club_new.append(curated)
                    pos_remove.append(pos_remove_index[i])
                else:
                    user_sat_club_new.append(club)
            if curated_flag == False:
                for sat_avail in UPGRADED_SATSENAVAIL:
                    sat_avail_ = re.sub('-','',sat_avail)
                    sat_avail_ = sat_avail_.split('$')[0]
                    if re.sub('-','',tag) in sat_avail_.lower():
                        curated.append(sat_avail)
                        
                if len(curated)>0:
                    user_sat_club_new.append(curated)
                    pos_remove.append(pos_remove_index[i])
               
        user_sat_club = user_sat_club_new
    user_sat = []
    for club in user_sat_club:
        user_sat.extend(club)
        
    
    
    user_pos_new = []
    remove_index = []

    for index in pos_remove:
        for ind in index:
            remove_index.append(ind)
    for i in range(len(user_pos)):
            if i not in remove_index:
                user_pos_new.append(user_pos[i])
                
    
    return list(np.unique(user_sat)), user_tags,user_pos_new
# New function to curate the found satellites further based on resolution, open/free, sensor-type
def getFilteredSatSen(user_sats,user_tags):
    '''
    Function to curate the found satellites further based on resolution, open/free, sensor-type
    
    Parameters
    ----------
    user_sats : list
        List of all the found satellites from user query
    user_tags : list
        List of tokens from user query text

    Returns
    -------
    list
        List of all the curated satellite and sensor configurations which are bhoonidhi compatible
    '''
    SATSENCONFIG =  {}
    OPT_SAR_CONFIG={}
    OPEN_FREE_CONFIG={}
    SENSATCONFIG =  {}
    PRO_CAT_CONFIG = {}
    for satsen in getAvailableSatSen():
        SATSENCONFIG[satsen[0].replace('-','').lower()] = []
        OPT_SAR_CONFIG[satsen[3].lower()]=[]
        OPEN_FREE_CONFIG[satsen[4].split('_')[0].lower()]=[]
        PRO_CAT_CONFIG[satsen[7].lower()] = []
        sen = satsen[1].split('+') 
        for s in sen:
            s = s.replace('(','')
            s = s.replace(')','')
            s = s.replace('_','')
            s = s.replace('-','')   
            SENSATCONFIG[s.lower()] = []
    for satsen in getAvailableSatSen():
        ptype = satsen[2]
        SATSENCONFIG[satsen[0].replace('-','').lower()].append(f'{satsen[0]}_{satsen[1]}{ptype}')
        sen = satsen[1].split('+')
        for s in sen:
            s = s.replace('(','')
            s = s.replace(')','')
            s = s.replace('_','')
            s = s.replace('-','')   
            SENSATCONFIG[s.lower()].append(f'{satsen[0]}_{satsen[1]}{ptype}')
    
        OPT_SAR_CONFIG[satsen[3].lower()].append(f'{satsen[0]}_{satsen[1]}{ptype}${satsen[3]}${satsen[4]}${satsen[5]}')
        OPEN_FREE_CONFIG[satsen[4].split('_')[0].lower()].append(f'{satsen[0]}_{satsen[1]}{ptype}${satsen[3]}${satsen[4]}${satsen[5]}')
        PRO_CAT_CONFIG[satsen[7].lower()].append(f'{satsen[0]}_{satsen[1]}{ptype}${satsen[3]}${satsen[4]}${satsen[5]}')
    # Pricing 
    if 'paid' in user_tags or  'priced' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[2].lower() == 'priced':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = OPEN_FREE_CONFIG['priced']
        
        user_sats=user_sats_new
        
    if 'free' in user_tags or  'open' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[2].lower() == 'open_data':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = OPEN_FREE_CONFIG['open']
        
        user_sats=user_sats_new
    # Sensor types   
    if  'optical' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[1].lower() == 'optical':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = OPT_SAR_CONFIG['optical']
        
        user_sats=user_sats_new
        
    if  'microwave' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[1].lower() == 'microwave':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = OPT_SAR_CONFIG['microwave']
        
        user_sats=user_sats_new
        
    
        
    if  'scatterometer' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[1].lower() == 'scatterometer':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = OPT_SAR_CONFIG['scatterometer']
        
        user_sats=user_sats_new
    
    if  'infrared' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[1].lower() == 'infrared':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = OPT_SAR_CONFIG['infrared']
        
        user_sats=user_sats_new
    # Product Categories
    if  'aisdata' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[4].lower() == 'ais':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = PRO_CAT_CONFIG['ais']
        
        user_sats=user_sats_new
    if 'thematic' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[4].lower() == 'thematic':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = PRO_CAT_CONFIG['thematic']
        
        user_sats=user_sats_new
    if 'standard' in user_tags:
        user_sats_new = []
        for sat in user_sats:
            if sat.split('$')[4].lower() == 'standard':
                user_sats_new.append(sat)
        if len(user_sats) == 0:
            user_sats_new = PRO_CAT_CONFIG['standard']
        
        user_sats=user_sats_new
    # Resolution
    for tag in user_tags:
        if tag.lower() in ['superhigh','high','low','coarse','medium']:
            if tag.lower() == 'superhigh':
                tag = 'very high'            ################ dependency on database
            user_sats_new = []
            curated_ = False
            for sat in user_sats:
                if sat.split('$')[3].lower() == tag:
                    curated_ = True
                    user_sats_new.append(sat)
            
            if len(user_sats) == 0:
                user_sats_new = getBhoonidhiSatellitefromResolution(tag)          
            else:
                if not curated_:
                    user_sats.extend(getBhoonidhiSatellitefromResolution(tag))
                    user_sats_new = user_sats
            user_sats=user_sats_new
            
    SatSen = []
    resolution_alert = False
    resolution_check = ''
    for sat in user_sats:
        if resolution_check != '' :
            if resolution_check !=sat.split('$')[3]:
                resolution_alert = True
        else:
            resolution_check= sat.split('$')[3]
    for sat in user_sats:
        if resolution_alert == True:
            if sat.split('$')[3] == 'Very High':
                if resolution_check == 'Very High':
                    resolution_check = 'Medium'
                continue
        SatSen.append(sat.split('$')[0])
    if resolution_check  == 'Very High':
        resolution_check = '0-1'
    elif resolution_check  == 'High':
        resolution_check = '1-5'
    elif resolution_check  == 'Medium':
        resolution_check = '5-25'
    elif resolution_check  == 'Low':
        resolution_check = '25-100'
    elif resolution_check  == 'Coarse':
        resolution_check = '100-1000'
    return SatSen, resolution_check   
#Function to catch additional parameters like resolution and process the units for each value in the parameters
def getBhoonidhiProcessedParameters(parameters,user_pos):
    '''
    A helper function to curate the parameters further if any missing or processing further for removing units, symbols, etc.
    
    Parameters
    ----------
    parameters : list
        List of raw parameters found in the text
    user_pos : list
        A list of tokenized parts of speech in the query text

    Returns
    -------
    list
        A curated list of parameters in the format [[value1,key1],[value2,key2],....]
    '''
    user_pos = np.array(user_pos)
    resolution_specific = False
    for filt in parameters:
        if filt[-1] in ['latitude']:
            filt[-1] = 'lat'
        if filt[-1] in ['longitude']:
            filt[-1] = 'lon'
        if filt[-1] in ['resolution']:
            resolution_specific = True
            comp = filt[0][0]
            num = int(re.search(r'\d+',  filt[0]).group())
            if comp == '+':
                num+=10
            if comp == '-':
                num-=9
            if 'kilometer' in filt[0] or 'km' in filt[0] or 'kilo' in filt[0]:
                num = num*1000
            elif 'miles' in filt[0] or 'mile' in filt[0]:
                num = num*1609.34
            elif 'meter' in filt[0] or 'mts' in filt[0] or 'm' in filt[0]:
                num = num
            
            if num<1 or num ==1:
                filt[0] = ['SuperHigh']
            elif num < 5 or num ==5:
                filt[0] = ['High']                    
            elif num < 25 or num == 25:
                filt[0] =['Medium']
            elif num < 100 or num == 100:
                filt[0] = ['Low']
            elif num >100:
                filt[0] = ['Coarse']
            else:
                filt[0] = ['Medium']     
            
            
        if filt[-1] in ['radius','area','swath','spread']:
            num = int(re.search(r'\d+',  filt[0]).group())
            if filt[-1]=='area':
                num = int(num**0.5)
            if 'kilometer' in filt[0] or 'km' in filt[0] or 'kilo' in filt[0]:
                pass
            elif 'miles' in filt[0] or 'mile' in filt[0]:
                num = num*1609.34
            elif 'meter' in filt[0] or 'mts' in filt[0] or 'm' in filt[0]:
                num = num*0.001
            filt[0] = str(num)
            filt[-1] = 'radius'
            
            
        if filt[-1] == 'cloud':
            filt[-1] = 'cloudThresh'
            filt[0] = int(re.search(r'\d+',  filt[0]).group())
    if resolution_specific == False and 'resolution' in user_pos[:,0]:
        res = []
        if 'medium' in user_pos[:,0]:
            res.append('Medium')
        if 'low' in user_pos[:,0]:
            res.append('Low')
        if 'superhigh' in user_pos[:,0]:
            res.append('SuperHigh')
        if 'high' in user_pos[:,0]:
            res.append('High')
        if  'coarse' in user_pos[:,0]:
            res.append('Coarse')
        else:
            pass
        if len(res)>0:
            parameters.append([res,'resolution'])
    return parameters



# Date formatting for bhoonidhi JSON  
def getBhoonidhiDates(string):
    '''
    A helper function to format date in the JSON as per HTML requirements
    
    Parameters
    ----------
    string : str
        Date string in the format dd MMM, yyyy

    Returns
    -------
    list
        A formated date string as per HTML requirement in the format MM%2Fdd%2Fyyyy
    '''
    terms = string.split(' ')
    date = terms[0]
    month = terms[1][:3].upper()
    year = terms[2]
    return month+'%2F'+date+'%2F'+year
# For html post request on bhoonidhi through python requests module
def hitBhoonidhi(jsons):
    '''
    A function to request a post on bhoonidhi server
    
    Parameters
    ----------
    jsons : list
        A list of jsons for sending them in the post requests as the body/data

    Returns
    -------
    list
        A list of results returned by the server
    
    '''
    output = []
    i=0
    proxies = {
     'http': '',
     'https': ''
    }
    for j in jsons.keys():
        i=i+1
        response = requests.post('https://bhoonidhi.nrsc.gov.in/bhoonidhi/ProductSearch', json=jsons[j], proxies=proxies,timeout=20)
        try:
            if i == 1:
                output = response.json()['Results']
            else:
                output.extend(response.json()['Results'])
        except:
            pass
    return output
# Database call for fetching locations (states, countries, districts and cities)
def getLocationsBhoonidhi():
    '''
    A Database call for fetching locations (states, countries, districts and cities)
    
    Parameters
    ----------
    void

    Returns
    -------
    cities : array
    districts: array
    states : array
    countries : array
    '''
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'
    try:
        <Database Operations>
    except:
        raise Exception('Database Error at Locations database')
    db.close()
    return np.array(cities), np.array(districts), np.array(states), np.array(countries)
# Database call for fetching all the events types in the repo.
def getEventTypesBhoonidhi():
    '''
    Database call for fetching all the events types present in the repo.
    
    Parameters
    ----------
    void

    Returns
    -------
    dict 
        A list of event types in the database
    '''
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'
    try:
        <Database Operations>
    except:
        raise Exception('Database Error at Events database')
    eventTypes = []
    for row in c:
        if row[7].lower() not in eventTypes:
            eventTypes.append(row[7].lower())
            
    return eventTypes
# Database call for fetching all the events objects in the repo.
def getEventsBhoonidhi():
    '''
    Database call for fetching all the events objects in the repo.
    
    Parameters
    ----------
    void

    Returns
    -------
    dict 
        A dictionary of events object in the format of {event_name:[sensors, point/polygon, radius,type of event, location, sdate,  edate]}
    '''
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'
    try:
        <Database Operations>
    except:
        raise Exception('Database Error at Events database')
    EVENTS = {}
#    events=[]
    for row in c:
#        events.append(row)
        EVENTS[row[1].lower()] = [row[8],row[10],row[6],row[7],row[9],row[2],row[3]]
    return EVENTS
# Recognition of locations in the user_text that are available in the database
def findBhoonidhiLocations(user_text):
    '''
    Recognition of locations in the user_text that are available in the database
    
    Parameters
    ----------
    user_text : str
        The preprocessed query text

    Returns
    -------
    list 
        A list of available location in the query and database in the format [[shp name/lat lon, code (0 if no match, 1 if shapefile, 2 if lat lon)]]
    '''
    user_tokens = word_tokenize(user_text.lower())
    cities, districts, states, countries = (getLocationsBhoonidhi())
    lemmatizer = WordNetLemmatizer() 
    for i in range(len(user_tokens)):
        user_tokens[i] = lemmatizer.lemmatize(user_tokens[i])
    
    user_pos = nltk.pos_tag(user_tokens)
    results = []
    tags = []
    i = 0
    for word in user_pos:
        i+=1
        probable = user_pos[i-1][0]

        if probable in countries[:,0]:
            results.append(countries[np.where(probable == countries[:,0])][0])
            tags.append('shape')
        elif probable in states[:,0]:
            results.append(states[np.where(probable == states[:,0])][0])
            tags.append('shape')
        elif probable in districts[:,0]:
            results.append(districts[np.where(probable == districts[:,0])][0])
            tags.append('shape')
        elif probable in cities[:,0]:
            results.append(cities[np.where(probable == cities[:,0])][0])
            tags.append('location')
        else:
            if i<len(user_pos)-1:
                probable = user_pos[i-1][0] + user_pos[i][0]
                if probable in countries[:,0]:
                   results.append(countries[np.where(probable == countries[:,0])][0])
                   tags.append('shape')
                elif probable in states[:,0]:
                    results.append(states[np.where(probable == states[:,0])][0])
                    tags.append('shape')
                elif probable in cities[:,0]:
                    results.append(cities[np.where(probable == cities[:,0])][0])
                    tags.append('location')
                elif probable in districts[:,0]:
                    results.append(districts[np.where(probable == districts[:,0])][0])
                    tags.append('shape')
                else:
                    pass
                
            else:    
                pass
    if results == []:
        break_loop = False
        for word in user_tokens:
            if word not in set(stopwords.words('english'))  and len(word)>3:
                for c in countries:
                    if word in c[0]:
                        results.append(c)
                        break_loop = True
                        break
                for c in states:
                    if break_loop:
                        break
                    if word in c[0]:
                        results.append(c)
                        break_loop = True
                        break
                for c in cities:
                    if break_loop:
                        break
                    if word in c[0]:
                        results.append(c)
                        break_loop = True
                        break  
                for c in districts:
                    if break_loop:
                        break
                    if word in c[0]:
                        results.append(c)
                        break_loop = True
                        break
                
    return results
# Converting the datetime format as given in the events database to required format
def getBhoonidhiEventDate(date):
    '''
    Converting the datetime format as given in the events database to required format
    
    Parameters
    ----------
    date : datetime.datetime
        Datetime formatted date object

    Returns
    -------
    str 
        A string in the format of dd MM, YYYY
    '''
    return date.strftime("%d %B, %Y")
# Database call for fetching satellites as per their resolution
def getBhoonidhiSatellitefromResolution(user_res):
    '''
    Database call for fetching satellites as per their resolution
    
    Parameters
    ----------
    user_res : str
        resolution in the consideration

    Returns
    -------
    list 
        A list of all the available satsen configs in the master format
    '''
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'
    try:
       <Database Operations>
    except:
        raise Exception('Database Error at satsen configuration database')
    resolution = {}
    for satsen in getAvailableSatSen():
        if satsen[5]!=None:
            if satsen[5].lower() not in resolution.keys():
                resolution[satsen[5].lower()] = []
    for satsen in getAvailableSatSen():
        ptype = satsen[2]
        resolution[satsen[5].lower()].append(f'{satsen[0]}_{satsen[1]}{ptype}${satsen[3]}${satsen[4]}${satsen[5]}')    
    if user_res.lower() == 'fine':
        user_res = 'very high'

    return resolution[user_res.lower()]

# Login function
def bhoonidhiLogin(user_id, password):
    '''
    Login function through html requests
    
    Parameters
    ----------
    user_id : str
        user id as per the account
    password : str
        password of the particular user id

    Returns
    -------
    str 
        A JWT token for validation of the login
    '''
    url = 'https://bhoonidhi-staging.nrsc.gov.in/bhoonidhi/LoginServlet'
    json = {}
    json['userId'] = user_id
    json['password'] = password
    json['oldDB'] = 'false'
    json['action'] = 'VALIDATE_LOGIN'
    
    response = requests.post(url, json=json)
    
    return response.json()["Results"][0]['JWT']

# Downlaod function for 1 product
def bhoonidhiDownload(product_obj, user_id, password, output_path=''):
    '''
    Login function through html requests
    
    Parameters
    ----------
    product_obj : json
        The result object returned by bhoonidhi html server
    user_id : str
        user id as per the account
    password : str
        password of the particular user id
    output_path : str,optional
        The output path where user would like the download to happen

    Returns
    -------
    str 
        A succesful or failure message after the download thread exits
    '''
    token = bhoonidhiLogin(user_id, password)
    sat = product_obj['OTS_SATELLITE']
    if sat == 'L8':
        sen = 'O'
    else:
         sen = product_obj['OTS_SENSOR']
    year = product_obj['OTS_DATE_OF_DUMPING'].split('-')[-1]
    month = product_obj['OTS_DATE_OF_DUMPING'].split('-')[1].upper()
    prdId = product_obj['OTS_OTSPRODUCTID']
    
    try:
        path = "https://bhoonidhi.nrsc.gov.in/bhoonidhi/data/" + sat + "/" + sen + "/" + year + "/" + month + "/" + prdId + ".zip?token=" + token + "&product_id=" + prdId
        urllib.request.urlretrieve(path, os.path.join(output_path,prdId + ".zip"))
        return f'Downloaded the product succefully at {os.path.join(output_path,prdId + ".zip")}'
    except Exception as e:
        return str(e)
# Batch downloading the entire products in the list
def bhoonidhiBatchDownload(products, user_id, password, output_path=''):
    '''
    Login function through html requests
    
    Parameters
    ----------
    products : list
        The list of all results object returned by bhoonidhi html server
    user_id : str
        user id as per the account
    password : str
        password of the particular user id
    output_path : str,optional
        The output path where user would like the download to happen

    Returns
    -------
    str 
        A succesful or failure messages after each download thread exits
    '''
    def download(product):
        product_obj = product[0]
        user_id= product[1]
        password = product[2]
        token = bhoonidhiLogin(user_id, password)
        sat = product_obj['OTS_SATELLITE']
        if sat == 'L8':
            sen = 'O'
        else:
             sen = product_obj['OTS_SENSOR']
        year = product_obj['OTS_DATE_OF_DUMPING'].split('-')[-1]
        month = product_obj['OTS_DATE_OF_DUMPING'].split('-')[1].upper()
        prdId = product_obj['OTS_OTSPRODUCTID']
        
        try:
            path = "https://bhoonidhi.nrsc.gov.in/bhoonidhi/data/" + sat + "/" + sen + "/" + year + "/" + month + "/" + prdId + ".zip?token=" + token + "&product_id=" + prdId
            urllib.request.urlretrieve(path, os.path.join(output_path,prdId + ".zip"))
            return f'Downloaded the product succesfully at {os.path.join(output_path,prdId + ".zip")}'
        except Exception as e:
            return str(e)
    edited_products = []
    for product in products:
        edited_products.append([product,user_id,password])
    results = ThreadPool(5).imap_unordered(download, edited_products)
    Not_happened = []
    i=0
    for result in results:
        if 'succesfully' in result:
            pass
        else:
            Not_happened.append(products[i]['OTS_OTSPRODUCTID'])
        i+=1
    if Not_happened == []:
        return('Downloaded all the products')
    else:
        return(f'The following products could not download {Not_happened}')
# Database call for validating and fetchin all the relevant additional filters for a given satellite
def getFilterValidation(sat,filter_text):
    '''
    Database call for validating and fetchin all the relevant additional filters for a given satellite
    
    Parameters
    ----------
    sat : str
        The satellite sensor product_type sample
    filter_text : str
        All the advanced filter in the query converted to JSON compliant format
    Returns
    -------
    str 
        A formatted satellite compatible and relevant advanced filter in the format required by HTML JSON
    '''
    SATSEN = {}
    for satsen in getAvailableSatSen():
        SATSEN[f'{satsen[0]}_{satsen[1]}{satsen[2]}']= satsen[6]
    sat_index = SATSEN[sat]
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'
    try:
       <Database Operations>
    except:
        raise Exception('Database Error at Events database')
    FILTERS = {}
    for row in c:
        FILTERS[row[3]]= row[0]
        
        
    ip = 'xxx.yy.c.ss'
    port = port_number
    SID = 'db_name'        
    try:
        <Database Operations>
    except:
        raise Exception('Database Error at filter configuration database')
        
    config = []
    for row in c:
        if row[1] == sat_index:
            config.append(FILTERS[row[0]])
    
    user_filters= filter_text.split('$')
    sat_filter_text = f''
    for filt in user_filters:
        if filt.split(':')[0][1:-1] in config:
            sat_filter_text+=f"{filt},"
        
    return sat_filter_text[:-1]
# A function to add additional filter text into the json which will be sent to the bhoonidhi backend
def getBhoonidhiFilterText(parameters,SatSen,json_dict,location_flag):
    '''
    A function to add additional filter text into the json which will be sent to the bhoonidhi backend
    
    Parameters
    ----------
    parameters : list
        List of all the parameters found in the query
    SatSen : list
        The list of all the satellite sensor product_type samples found in the query
    json_dict : json
        JSON formed so far for bhoonidhi backend
    location_flag : boolean
        A flag to show if the parameters contain any location value, if yes, the JSON format has to be changed after the function
    Returns
    -------
    json 
        JSON after adding the additional filters key in the input JSON
    '''
    filter_text=''
    default_filters = {}
    default_filters[1]='"PATH":{"min":"0","max":"1000"}$'
    default_filters[2]='"ROW":{"min":"0","max":"1000"}$'
    default_filters[3]='"INCIDENCE_ANGLE":{"min":"0","max":"360"}$'
    default_filters[4]='"INCLINATION_ANGLE":{"min":"0","max":"360"}$'
    default_filters[5]='"TRANSPOL":"Any"$'
    default_filters[6]='"RECVPOL":"Any"$'
    default_filters[7]='"NODE":"Any"$'
    default_filters[8]='"LOOK_DIRECTION":"Any"$'
    default_filters[9]='"CLOUD":"100"$'
    no_filters = True
    default_false = []
    if location_flag==1:
        default_false = [1,2]
    for parameter in parameters:
        
        if parameter[-1]=='pathno' or parameter[-1]=='rowno':
            if location_flag==1:
                raise Exception('Please provide either path/row or geo location information')
            no_filters = False
            if parameter[-1]=='pathno':
                default_false.append(1)
            else:
                default_false.append(2)
            if parameter[0]=='+':
                min_val = parameter[1:]
                max_val = '10000'
            elif parameter[0]=='-':
                min_val = '0'
                max_val = parameter[1:]
            else:
                min_val = min(parameter[0].split('123456789'))
                max_val = max(parameter[0].split('123456789'))
            filter_text+=f'"{parameter[-1][:-2].upper()}":{{"min":"{min_val}","max":"{max_val}"}}$'
        elif parameter[-1]=='incidenceangle' or parameter[-1]=='inclinationangle':
            no_filters = False
            if parameter[-1]=='incidenceangle':
                default_false.append(3)
            else:
                default_false.append(4)
            if parameter[0]=='+':
                min_val = parameter[1:]
                max_val = '360'
            elif parameter[0]=='-':
                min_val = '0'
                max_val = parameter[1:]
            else:
                min_val = min(parameter[0].split('123456789'))
                max_val = max(parameter[0].split('123456789'))
            filter_text+=f'"{parameter[-1][:-5].upper()}_ANGLE":{{"min":"{min_val}","max":"{max_val}"}}$'  
        elif parameter[-1]=='transpol':
            no_filters = False
            default_false.append(5)
            if parameter[0]=='143143143':
                val = 'Horizontal'
            elif parameter[0]=='341341341':
                val = 'Vertical'
            elif parameter[0]=='001001001':
                val = 'Circular'
            else:
                val= 'Any'
            filter_text+=f'"TRANSPOL":"{val}"$'
        
        elif parameter[-1]=='recvpol':
            no_filters = False
            default_false.append(6)
            if parameter[0]=='101101101':
                val = 'Any'
            elif parameter[0]=='696969696':
                val = 'Dual'
            else:
                val= 'Any'
            filter_text+=f'"RECVPOL":"{val}"$'
        
        elif parameter[-1]=='node':
            no_filters = False
            default_false.append(7)
            if parameter[0]=='248163264':
                val = 'Ascending'
            elif parameter[0]=='643216842':
                val = 'Descending'
            else:
                val= 'Any'
            filter_text+=f'"NODE":"{val}"$'
        
        elif parameter[-1]=='lookdirection':
            no_filters = False
            default_false.append(8)
            if parameter[0]=='123123123':
                val = 'Right'
            elif parameter[0]=='321321321':
                val = 'Left'
            else:
                val= 'Any'
            filter_text+=f'"LOOK_DIRECTION":"{val}"$'
        
        elif parameter[-1]=='cloudThresh':
            no_filters = False
            default_false.append(9)
            filter_text+=f'"CLOUD":"{parameter[0]}"$'
        
        elif parameter[-1]=='resolution':
            pass
        else:
            if parameter[-1] == 'radius':
                if 'shapefilename' not in json_dict.keys():
                    json_dict[parameter[-1]] = min(100,int(parameter[0]))
            else:
                json_dict[parameter[-1]] = parameter[0]
    if no_filters:
        return json_dict
    for i in range(9):
        if i+1 not in default_false:
            filter_text+=default_filters[i+1]
    if len(filter_text)>0:
        filter_text = filter_text[:-1]
        final_filter_text='{'
        for sat in SatSen:
            text = getFilterValidation(sat,filter_text)
            if len(text)!=0:
                final_filter_text+=f'"{sat}":{{{text}}},'
        json_dict['filters']=  (final_filter_text[:-1]+'}')
    return json_dict

# New function outputs only the event objects, not the json. Making the code clutter and redundant free  
def findBhoonidhiEvents(user_text, user_tokens):
    '''
    Function to fetch available events in the query text
    
    Parameters
    ----------
    user_text : str
        User query string
    user_tokens : list
        List of tokenised words in the query

    Returns
    -------
    list 
        A list of all the found events in the query
        
    '''
    def hasNumbers(inputString):
        return bool(re.search(r'\d', inputString))
    events = (getEventsBhoonidhi())
    common_data = []
    specific_data = []
    found_events = []
    flo = 0
    ava = 0 
    for event in events.keys():
        f = events[event]
        f.append(event)
        i = -1
        for token in user_tokens:
            i+=1
            if token in event:
                if 'flood' in token or 'avalanche' in token:
                    a = user_tokens.copy()
                    a.pop(i)
                    if 'avalanche' in a:
                        a.remove('avalanche')
                    if 'flood' in a:
                        a.remove('flood')
                    if 'floods' in a:
                        a.remove('floods')
                    values = ([val for i, val in enumerate(a) if val in event and not hasNumbers(val) and val!='pradesh'])
                    if values!=[]:
                        specific_data.append(f) 
                        if 'flood' in event:
                            flo = 1
                        else:
                            ava = 1
                        break
                    else:
                        values = []
                        for eve in event.split(' '):
                            values.extend([val for i, val in enumerate(a) if val in eve and not hasNumbers(val) and val!='pradesh'])
                        if values == []:
                            common_data.append(f)
                elif token=='pradesh' or hasNumbers(token):
                    pass
                else:
                    specific_data.append(f)
                    if 'flood' in event:
                        flo = 1
                    else:
                        ava = 1
                    
                break
    if specific_data == []:
        specific_data.extend(common_data)
    else:
        found_events = specific_data
        for data in common_data:
            if flo == 0:
                if 'Flood' == data[0]:
                    specific_data.append(data)
            if ava == 0:
                if 'Avalanche' == data[0]:
                    specific_data.append(data)
                
    found_events = specific_data
    del(specific_data)        
        
    unique = []
    final_events = []
    i = 0
    for f in found_events:
        if i == 0:
            unique.append(f[-1])
            final_events.append(f)
        elif f[-1] not in unique:    
            final_events.append(f)
    found_events = final_events
    del(final_events)
                
    found_events =found_events
    if len(np.shape(found_events)) == 1:
        if len(found_events) > 0:
            found_events = [found_events]
    return found_events