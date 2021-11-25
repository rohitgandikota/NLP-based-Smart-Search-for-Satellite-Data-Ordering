# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 14:34:43 2020
@author: Rohit Gandikota
"""
import re 
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import datetime
from dateparser.search import search_dates
from quantulum3 import parser
from word2number import w2n
#%%  All the tags that has to be searched for. Created as global variables so that it is easy to configure for future use
TAGS_JSON = ['radius', 'buffer', 'swath', 'resolution', 'lat', 'latitude', 'lon','longitude', 'area','swath','spread','pathno','rowno','cloud','incidenceangle','inclinationangle','transpol','recvpol','lookdirection','node']
############################################################################### Functions

# An improved date finding code for many user friendly queries like "2020 data", "July 2020 data", "Last month data"   
def findDates(user_text,feature_count):
    '''
    Function to find dates in the query. Advanced options like entire year, month, pop formats are made available
    
    Parameters
    ----------
    user_text : str
        Query string as per user
    feature_count : int
        Number of query parameters found in the query so far

    Returns
    -------
    init_date : str
        Start date in the format dd MM, YY (default same day's date)
    final_date : str
        End date in the format dd MM, YY (default same day - 30 days)
    user_text_new : str
        An updated query text after eliminatind the text corresponding to the query
    feature_count : int
        An updated count of number of parameters found in the query (add 2 if two dates found, add 1 if 1 date found, else add 0)
    '''
    user_text_new = user_text
    def hasNumbers(inputString):
        return bool(re.search(r'\d', inputString))
    if '%' in user_text:
        user_text = user_text.replace('%','')
    if re.search(r'\s+m\s+', user_text):
        user_text = user_text.replace(re.search(r'\s+m\s+', user_text).group(),'mts')
    if re.search(r'\s+km\s+', user_text):
        user_text = user_text.replace(re.search(r'\s+km\s+', user_text).group(),'km ')
    if re.search(r'\s+mt\w\s+', user_text):
        user_text = user_text.replace(re.search(r'\s+mt\w\s+', user_text).group(),'mts ')
    if re.search(r'\s+km\w\s+', user_text):
        user_text = user_text.replace(re.search(r'\s+km\w\s+', user_text).group(),'kms ')
    if re.search(r'[0-9]+m\s+', user_text):
        user_text = user_text.replace(re.search(r'[0-9]*m', user_text).group(),re.search(r'[0-9]*m', user_text).group()+'ts')
    
    user_text= user_text.replace(' meter ','meter ')
    user_text= user_text.replace(' meters ','meters ')
    user_text= user_text.replace(' kilometer ','kilometers ')
    user_text= user_text.replace('Lat ','Lattitude ')
    user_text= user_text.replace('lat ','lattitude ')
    user_text= user_text.replace('Lon ','Longitude ')
    user_text= user_text.replace('lon ','longitude ')
    user_text= user_text.replace(' abu ',' ')
    user_text = re.sub('123456789','fsdf',user_text)
    user_text = re.sub('143143143','sdfsdf',user_text)
    user_text = re.sub('341341341','sdfsdf',user_text)
    user_text = re.sub('001001001','sdfsdf',user_text)
    user_text = re.sub('101101101','sdfgs',user_text)
    user_text = re.sub('696969696','gdsgsg',user_text)
    user_text = re.sub('123123123','gsdg',user_text)
    user_text = re.sub('321321321','sdgsdg',user_text)
    user_text = re.sub('248163264','sdggs',user_text)
    user_text = re.sub('643216842','sdggsdg',user_text)
    user_text = re.sub('\s+of\s+',' ',user_text)
    user_text = re.sub('\s+\d\d\d\s+',' ',user_text)
    user_text = re.sub(' this month',f' 01 {datetime.datetime.today().strftime(" %B %Y")} till today',user_text)
    user_text = re.sub(' this year',f'01 January{datetime.datetime.today().strftime("%Y")} till today',user_text)
    user_text = re.sub(' current month',f' 01 {datetime.datetime.today().strftime(" %B %Y")} till today',user_text)
    user_text = re.sub(' current year',f'01 January{datetime.datetime.today().strftime("%Y")} till today',user_text)
    user_text = re.sub(' and ',' ',user_text)
    user_text = re.sub(' on ',' ',user_text)
    dates = search_dates(user_text)
    if dates != None:
        year_whole = False
        dates = np.array(dates)
        
        for date in dates:
            if date[0].isdigit():
                user_text = user_text.replace(date[0],' ')
            if (int(date[1].strftime('%y-%m-%d').split('-')[-1]) == int(datetime.datetime.today().strftime('%y-%m-%d').split('-')[-1])):
                if re.search(r'2[0-9][0-9][0-9]',date[0]):
                    if re.search(r'2[0-9][0-9][0-9]',date[0]).group() == date[0].strip():
                        user_text = user_text.replace(re.search(r'2[0-9][0-9][0-9]',date[0]).group(),' ')
                        year_bup = re.search(r'2[0-9][0-9][0-9]',date[0]).group()
                        date[0] = date[0].replace( re.search(r'2[0-9][0-9][0-9]',date[0]).group(),'')
                        if date[0] == '':
                            year_whole_ = year_bup
                            year_whole = True                          
                            
                        
            if (int(date[1].strftime('%y-%m-%d').split('-')[-1]) == int(datetime.datetime.today().strftime('%y-%m-%d').split('-')[-1]) and str(int(date[1].strftime('%y-%m-%d').split('-')[-1])) not in date[0]) and ((date[0] not in ['today', 'yesterday','tomorrow']) and ('month' not in date[0] and 'week' not in date[0] and 'day' not in date[0]) and ((date[1].strftime('%B').lower() in date[0] or date[0] in date[1].strftime('%B').lower())) and date[0]!=''):
                user_text = user_text.replace(date[0],' ')
                d = date[1].strftime(' %B %Y')
                if d.split(' ')[1] == 'February':
                    user_text = '01'+d+ ' to '+'28th'+d +' date range '+ user_text
                else:   
                    user_text = '01'+d+ ' to '+'30th'+d +' date range '+ user_text
        dates = search_dates(user_text)
        if dates==None and year_whole == True:
            user_text_new = user_text_new.replace(f'{year_whole_}','')
            dates = search_dates(f'data from 1 January {year_whole_} to 31st December {year_whole_} please')
            
        if dates != None:
            dates = np.array(dates)
            for date in dates:
                user_text_new = user_text_new.replace(date[0],'')
            dates = np.unique(dates[:,-1])
            dates = list(dates)
            if 'today' in user_text.lower():
                dates.append(datetime.datetime.now())
            if 'yesterday' in user_text.lower():
                dates.append(datetime.datetime.now() - datetime.timedelta(days=1))
            if 'tomorrow' in user_text.lower():
                dates.append(datetime.datetime.now() + datetime.timedelta(days=1))
            
                
            dates = np.unique(dates)
            
            if len(dates) > 1:
                init_date = dates.min()
                final_date = dates.max()
                feature_count+=2
            elif len(dates) == 1:
                init_date = dates[0]
                final_date = dates[0]
                feature_count+=1
            else:
                init_date = (datetime.datetime.now() - datetime.timedelta(days=10))
                final_date =(datetime.datetime.now())
        else:
            init_date = (datetime.datetime.now() - datetime.timedelta(days=10))
            final_date = (datetime.datetime.now()) 
    elif 'recent' in user_text.lower() or 'latest' in user_text.lower():
        init_date = (datetime.datetime.now() - datetime.timedelta(days=3)).strftime("%d %B, %Y")
        final_date = (datetime.datetime.now()).strftime("%d %B, %Y")
        feature_count += 2
        return init_date, final_date,user_text_new,  feature_count
    elif 'today' in user_text.lower() or 'yesterday' in user_text.lower() or 'tomorrow' in user_text.lower() or 'day before yesterday' in user_text.lower() or 'day after tomorrow' in user_text.lower():
        dates = []
        if 'today' in user_text.lower():
            dates.append(datetime.datetime.now())
        if 'day before yesterday' in user_text.lower():
            user_text = user_text.replace('day before yesterday','')
            dates.append(datetime.datetime.now() - datetime.timedelta(days=2))
        if 'day after tomorrow' in user_text.lower():
            user_text = user_text.replace('day after tomorrow','')
            dates.append(datetime.datetime.now() + datetime.timedelta(days=2))
        if 'yesterday' in user_text.lower():
            dates.append(datetime.datetime.now() - datetime.timedelta(days=1))
        if 'tomorrow' in user_text.lower():
            dates.append(datetime.datetime.now() + datetime.timedelta(days=1))
        
        
            
        dates = np.unique(dates)
        
        if len(dates) > 1:
            init_date = dates.min()
            final_date = dates.max()
            feature_count+=2
        elif len(dates) == 1:
            init_date = dates[0]
            final_date = dates[0]
            feature_count+=1
        else:
            init_date = (datetime.datetime.now() - datetime.timedelta(days=10))
            final_date =(datetime.datetime.now())
    else:
        init_date = (datetime.datetime.now() - datetime.timedelta(days=30))
        final_date = (datetime.datetime.now())
    if init_date > datetime.datetime.now():
        init_date = init_date - datetime.timedelta(days=365)
    if final_date > datetime.datetime.now():
        final_date = final_date - datetime.timedelta(days=365)
    s_date = min(init_date,final_date)
    e_date = max(init_date, final_date)
    init_date = s_date.strftime("%d %B, %Y")
    final_date = e_date.strftime("%d %B, %Y")      
        
    return init_date, final_date, user_text_new, feature_count

# Main function in the entire code. Preprocesses the user text and transforms the text to a code friendly format
def preprocess(user_text):
    '''
    Function to preproces the user text and transforms the text to a code friendly format
    
    Parameters
    ----------
    user_text : str
        Query string as per user
    
    Returns
    -------
    str 
        An updated query text after basic and some advanced preprocessing
    
    '''
    user_text = user_text.lower()
    user_text = ' '+user_text+' '
    if re.search(r' path ',user_text):
        user_text = user_text.replace(' path ',' pathno ')
    if re.search(r' row ',user_text):
        user_text = user_text.replace(' row ',' rowno ')
    user_text = re.sub('transfer polarisation','transpol',user_text)
    user_text = re.sub('transmission polarisation','transpol',user_text)
    user_text = re.sub('trans polarisation','transpol',user_text)
    user_text = re.sub('trans pol','transpol',user_text)
    user_text = re.sub('recv polarisation','recvpol',user_text)
    user_text = re.sub('recv pol','recvpol',user_text)
    user_text = re.sub('reception polarisation','recvpol',user_text)
    user_text = re.sub('incidence angle','incidenceangle',user_text)
    user_text = re.sub('inclination angle','inclinationangle',user_text)
    user_text = re.sub('look direction','lookdirection',user_text)
    user_text = re.sub('range','',user_text)
    user_text = re.sub('very high resolution','superhigh resolution',user_text)
    user_text = re.sub('resolution very high','superhigh resolution',user_text)
    user_text = re.sub('fine resolution','superhigh resolution',user_text)
    user_text = re.sub('resolution fine','superhigh resolution',user_text)
    user_text = re.sub('resourcesat2\s+','resourcesat2_ ',user_text)
    if re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text):
        try:
            if len(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group().split('-')[-1]) == 2:
                replace = datetime.datetime.strptime(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group(),'%d-%m-%y')
                user_text = user_text.replace(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group(),replace.strftime('%d %B %Y'))
            elif len(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group().split('-')[-1]) == 4:
                replace = datetime.datetime.strptime(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group(),'%d-%m-%Y')
                user_text = user_text.replace(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group(),replace.strftime('%d %B %Y'))
            else:
                user_text = user_text.replace(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group(),'today')
        except:
            user_text = user_text.replace(re.search(r'[0-9]*-[0-9]*-[0-9]*',user_text).group(),'today')
    if re.search(r'\s+\d+\s*-\s*\d+\s+',  user_text):
        user_text = user_text.replace(re.search(r'\s+\d+\s*-\s*\d+\s+',  user_text).group() ,re.sub('\s*-\s*','123456789',re.search(r'\s+\d+\s*-\s*\d+\s+',  user_text).group()))
        user_text = re.sub(r'\s*-\s*',r'-',user_text)
        user_text = re.sub(r'\s*to\s*',r'-',user_text)
    if re.search(r'\s+\d+\s*to\s*\d+\s+',  user_text):
        user_text = user_text.replace(re.search(r'\s+\d+\s*to\s*\d+\s+',  user_text).group() ,re.sub('\s*to\s*','123456789',re.search(r'\s+\d+\s*to\s*\d+\s+',  user_text).group()))
    if re.search(r'\s+\d+-\d+\s+',  user_text):
        user_text = user_text.replace(re.search(r'\s+\d+-\d+\s+',  user_text).group(), (re.search(r'\s+\d+-\d+\s+',  user_text).group().replace('-','123456789')))
    user_text = user_text.replace('<',' less than ')
    user_text = user_text.replace('>',' greater than ')
    user_text = user_text.replace('!', 'not')
    user_text = user_text.replace('=', ' ')
    user_text_new = ''
    words = user_text.split(' ')
    for word in words:
        try:
            user_text_new+=str(w2n.word_to_num(word))+' '
        except:
            user_text_new += word+' '
       
    user_text  = user_text_new[:-1]
    
    if len(user_text.strip())== 0:
        return 'Ping pong'
    if ' ais ' in user_text:
        user_text = user_text.replace(' ais ', ' aisdata ')
    if ' me ' in user_text:
        user_text = user_text.replace(' me ', ' ')
    if 'morethan' or 'more than' in user_text:
        user_text = user_text.replace('more', 'greater')
    if ' no ' in user_text:
        user_text = user_text.replace(' no ', ' 0 % ')
    if ' m ' in user_text:
        user_text = user_text.replace(' m ', ' meters ')
    if re.search(r'\[*\s*\d+.*\s*,\s*\d+.*\s*\]*',  user_text) :
        if re.search(r'location',  user_text) or re.search(r'lat\w*\s*lon\w*',  user_text):
            a = re.search(r'\[*\s*\d+.*\s*,\s*\d+.*\s*\]*',  user_text).group()
            nums = re.findall('\d+\.*\d*',a)
            user_text = user_text.replace(a,f'lat {nums[0]} and lon {nums[1]}')
   
    if re.search(r'from\s*\w*\s*\wast',  user_text):
        user_text = user_text.replace(re.search(r'from\s*\w*\s*\wast',  user_text).group(), 'till today '+re.search(r'from\s*\w*\s*\wast',  user_text).group() )

    if re.search(r'since\s*\w*\s*\wast',  user_text):
        user_text = user_text.replace(re.search(r'since\s*\w*\s*\wast',  user_text).group(),'till today '+re.search(r'since\s*\w*\s*\wast',  user_text).group() )
    now = datetime.datetime.now()
    this_year = now.year
    last_month = now.month-1 if now.month > 1 else 12
    last_year = now.year - 1     
    if re.search(r'\wast\s*year',  user_text):
        user_text = user_text.replace(re.search(r'\wast\s*year',  user_text).group(),re.search(r'\wast\s*year',user_text).group()[:-5]+f' 01-01-{last_year} till 31-12-{last_year}') 
    if re.search(r'\wast\s*month',  user_text):
        user_text = user_text.replace(re.search(r'\wast\s*month',  user_text).group(),re.search(r'\wast\s*month',user_text).group()[:-5]+f' 01-{last_month}-{this_year} till 30-{last_month}-{this_year}') 
    
    if re.search(r'\wast\s*week',  user_text):
        user_text = user_text.replace(re.search(r'\wast\s*week',  user_text).group(), re.search(r'\wast\s*week',  user_text).group()[:-4]+' 1 week' )
        
    if re.search(r'\wast\s*day',  user_text):
        user_text = user_text.replace(re.search(r'\wast\s*day',  user_text).group(), re.search(r'\wast\s*day',  user_text).group()[:-3]+' 1 day')
    if re.search(r'for\s*\w*\s*\wast',  user_text):
        user_text = user_text.replace(re.search(r'for\s*\w*\s*\wast',  user_text).group(), 'till today '+re.search(r'for\s*\w*\s*\wast',  user_text).group() )
    if re.search(r'month',user_text) or re.search(r'week',user_text) or re.search(r'days',user_text) or  re.search(r'year',user_text):
        if not re.search('ago',user_text) and not re.search('today',user_text) and not re.search('till',user_text) and not re.search('back',user_text):
            user_text = 'from today till '+user_text
              
    
    if re.search(r'cloud\s*percent\w*',  user_text):
        user_text = user_text.replace(re.search(r'cloud\s*percent\w*',  user_text).group(), 'cloud')
    elif re.search(r'cloud\s*cover\w*',  user_text):
        user_text = user_text.replace( re.search(r'cloud\s*cover\w*',  user_text).group(), 'cloud')
    elif re.search(r'cloud\s*spread\w*',  user_text):
        user_text = user_text.replace(re.search(r'cloud\s*spread\w*',  user_text).group(), 'cloud')
    elif re.search(r'cloud\s*thres\w*',  user_text):
        user_text = user_text.replace(re.search(r'cloud\s*thres\w*',  user_text).group(), 'cloud')
    elif re.search(r'cloud\s*free\w*',  user_text):
        user_text = user_text.replace(re.search(r'cloud\s*free\w*',  user_text).group(), 'cloud 0')
    else:
        pass
    if re.search(r'cloud\s*percent\w*',  user_text):
        user_text = user_text.replace(re.search(r'cloud\s*percent\w*',  user_text).group(), 'cloud')
    ######### Converting filter values to integer for generalised parameter extraction
    
    user_text = re.sub('horizontal','143143143',user_text)
    user_text = re.sub('vertical','341341341',user_text)
    user_text = re.sub('circular','001001001',user_text)
    user_text = re.sub('any','101101101',user_text)
    user_text = re.sub('dual','696969696',user_text)
    user_text = re.sub('right','123123123',user_text)
    user_text = re.sub('left','321321321',user_text)
    user_text = re.sub('ascending','248163264',user_text)
    user_text = re.sub('descending','643216842',user_text)
    
    ######### Shortcuts for extra special users
    user_text = re.sub('l8','landsat8',user_text)
    user_text = re.sub('rs1','resourcesat1_',user_text)
    user_text = re.sub('rs2','resourcesat2_',user_text)
    user_text = re.sub(' nvs ',' novasar ',user_text)
    user_text = re.sub('r2a','resourcesat2a',user_text)
    user_text = re.sub('r1','risat1',user_text)
    user_text = re.sub('r2','risat2',user_text)
    user_text = re.sub('c3','cartosat3',user_text)
    user_text = re.sub('c03','cartosat3',user_text)
    user_text = re.sub('c2','cartosat2',user_text)
    user_text = re.sub('c1','cartosat1',user_text)
    user_text = re.sub('os2','oceansat2',user_text)
    return user_text.lower()

# Finding additional parameters in the query like advanced filter parameters, paid/free query, resolution, etc.
def findParameters(user_pos):
    '''
    Function to find additional parameters in the query like advanced filter parameters, paid/free query, resolution, etc.
    
    Parameters
    ----------
    user_pos : list
        List of tokenised parts of speech extracted from query text

    Returns
    -------
    list
        A curated list of all the raw parameters found in the query tokens
    '''
    user_pos = np.array(user_pos)
    params = []
    length = len(user_pos)
    for i in range(len(user_pos)):
        if user_pos[i][-1] == 'CD':
            skip = False
            tags = []
            if i > 1:
                if user_pos[i-2][-1] in ['NN', 'VBP','VBD', 'NNS','JJ','RB','VBZ']:     
                    
                    if  user_pos[i-1][0] in ['le', 'lessthan', 'finer', 'fine','less', 'lesser', 'better']:
                        user_pos[i][0] = '-'+user_pos[i][0]
                        tags.append(user_pos[i-2][0])
                        skip = True
                        
                    elif user_pos[i-1][0] in ['great', 'greatthan', 'greater', 'coarse','coarser','more','worse']:
                        user_pos[i][0] = '+'+user_pos[i][0]
                        tags.append(user_pos[i-2][0])
                        skip = True
                    else:
                        if user_pos[i-2][0] in TAGS_JSON:
                            tags.append(user_pos[i-2][0])
                
            if i > 0 and not skip:
                if user_pos[i-1][-1] in ['NN', 'VBP','VBD', 'NNS','JJ','RB','VBZ']:
                    if user_pos[i-1][0] in TAGS_JSON:
                        tags.append(user_pos[i-1][0])    
            
            ######################## Finding tags and values by parsing through user_pos ###########        
            gotUnits = 0
        
            if i<length-1:
                try:
                    if user_pos[i+1][-1] in ['NN', 'VBP','VBD', 'NNS','JJ','RB','VBZ'] and len(parser.parse(user_pos[i][0]+' '+user_pos[i+1][0]))>0:
                        if parser.parse(user_pos[i][0]+' '+user_pos[i+1][0])[0].surface ==  user_pos[i][0]+' '+user_pos[i+1][0]:
                            tags.append(user_pos[i][0]+user_pos[i+1][0])
                        else:
                            tags.append(user_pos[i][0])
                            if user_pos[i+1][-1] in ['NN', 'VBP','VBD', 'NNS','JJ','RB','VBZ']:
                                tags.append(user_pos[i+1][0])
                        gotUnits = 1
                except:
                    pass
            if i>0 and gotUnits == 0:
                try:
                    if user_pos[i-1][-1]in ['NN', 'VBP','VBD', 'NNS','JJ','RB','VBZ'] and len(parser.parse(user_pos[i][0]+' '+user_pos[i-1][0]))>0:
                        if parser.parse(user_pos[i][0]+' '+user_pos[i-1][0])[0].surface ==  user_pos[i][0]+' '+user_pos[i-1][0]:
                            tags.append(user_pos[i][0]+user_pos[i-1][0])
                        else:
                            tags.append(user_pos[i][0])
                        gotUnits = 1 
                except:
                    pass
            if len(parser.parse(user_pos[i][0]))>0 and gotUnits == 0:
                tags.append(user_pos[i][0])
                gotUnits = 1
            if gotUnits == 0:
#                print('Got Nothing')
                continue            
            if i<length-2:
                if user_pos[i+2][-1] in ['NN', 'VBP','VBD', 'NNS','JJ','RB','VBZ']:
                    if user_pos[i+2][0] in TAGS_JSON:
                        tags.append(user_pos[i+2][0])
          
            if len(tags)>1:
                params.append(tags)
    ############## Filtering all the extracted parameters
    filtered = []
    length = len(params)
    for i in range(length):
        if i == 0 :
            for j in range(len(params[i])):
                if len(parser.parse(params[i][j]))==0:
                   if params[i][j].lower() in TAGS_JSON:
                       if j < len(params[i])-1:
                           if len(parser.parse(params[i][j+1]))==1:
                                filtered.append([params[i][j+1],params[i][j]])
                                break
                           elif j < len(params[i])-2:
                                if len(parser.parse(params[i][j+2]))==1:
                                    filtered.append([params[i][j+2],params[i][j]])
                                    break
                                elif j < len(params[i])-3:
                                    if len(parser.parse(params[i][j+3]))==1:
                                        filtered.append([params[i][j+3],params[i][j]])
                                        break
                        
                else:
                    if j < len(params[i])-1:
                        if params[i][j+1].lower() in TAGS_JSON:
                            if params[i][j+1] == 'cloudThresh':
                                filtered.append([(re.search(r'\d+', params[i][j]).group()),params[i][j+1]])
                            else:
                                filtered.append([params[i][j],params[i][j+1]])
                                
                            break
                        elif j < len(params[i])-2:
                            if params[i][j+2].lower() in TAGS_JSON:
                                if params[i][j+2] == 'cloudThresh':
                                    filtered.append([(re.search(r'\d+', params[i][j]).group()),params[i][j+2]])
                                else:
                                    filtered.append([params[i][j],params[i][j+2]])
                            
                                break
    
                    
        else:
            over_write = True
            for j in range(len(params[i])):
                if len(parser.parse(params[i][j]))==0:
                    if len(filtered)>0:
                        if params[i][j] in np.array(filtered)[:,-1]:
                            pass
                        else:
                            if params[i][j].lower() in TAGS_JSON:
                                if over_write:
                                    unit = params[i][j]
                                    over_write = False
                            
                    else:
                        if params[i][j].lower() in TAGS_JSON:
                            if over_write:
                                unit = params[i][j]
                                over_write = False
                        
                else:  
                    val =  params[i][j]
            try:
                if unit == 'cloud':
                    filtered.append([(re.search(r'\d+', val).group()),unit])
                else:
                    filtered.append([val,unit])  
                del(unit,val)
            except:
                pass
    return filtered
# Function to get parts of speech after tokenizing
def getTokensPOS(user_text):
    '''
    Function to get parts of speech after tokenizing
    
    Parameters
    ----------
    user_text : str
        User query text

    Returns
    -------
    list
        A list of tokenised parts of speech extracted from the query text
    '''
    user_tokens = word_tokenize(user_text)
    
    lemmatizer = WordNetLemmatizer() 
    #    pst = PorterStemmer()
    for i in range(len(user_tokens)):
        user_tokens[i] = lemmatizer.lemmatize(user_tokens[i])
    a = set(stopwords.words('english'))
    filtered = [x for x in user_tokens if x not in a]
    user_tokens =  filtered 
    for i in range(len(user_tokens)):
        if user_tokens[i]=='le':
            user_tokens[i]='less'
    user_pos = nltk.pos_tag(user_tokens)
    return user_pos, user_tokens