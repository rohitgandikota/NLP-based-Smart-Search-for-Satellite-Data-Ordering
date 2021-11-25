# NLP-based-Smart-Search-for-Satellite-Data-Ordering
# bhoonidhi
https://bhoonidhi.nrsc.gov.in/bhoonidhi/index.html

A Python library for Bhoonidhi, ISRO's Paid and Open data access portal. The current version (v1.0.0) contains AI helper called "smart search" using NLP. The functionality can enable the power of searching in bhoonidhi using common search sentences and fetch the bhoonidhi results.

## Importing and using the module
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch

user_query = "Get me oceansat data from the region of hyderabad and Guntur from the last 1 month"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
```

## Smart search for event based
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch

user_query = "Get me available data from siachen avalanche and kerala floods 2020"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
```

## Smart search for paid/free data
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch

user_query = "Get me free high resolution optical data from 2020"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
```


## Advanced Fitlers search made easy
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch

user_query = 'resourcesat2 series liss3 data from 01 June 2020 till today with path 103 and inclination angle from 30 to 180 degrees"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
```

## Multiple query parameters
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch

user_query = "I want cartosat 2e and sentinel 2a data from the region of Guntur over the radius of 20 km and cloud threshold of 35%"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
```

## Curated search queries
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch

user_query = "I want free rs2 liss3 data from 1st June till 28th July over hyderabad"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
```



## Download searched products
```
from bhoonidhi.SmartSearch import bhoonidhiSmartSearch
from bhoonidhi.SmartSearch import bhoonidhiDownload

user_query = "I want cartosat 2e mx data from the region of Guntur over the radius of 20 km and cloud threshold of 35%"
bhoonidhiResponse = bhoonidhiSmartSearch(user_query)
# Want to download the 12th product from the response
bhoonidhiDownload(bhoonidhiResponse[12],user_id='bhoonidhi_user', password='password', output_path='D:\\bhoonidhiDownloads')
# Want to download all
for item in bhoonidhiResponse:
  bhoonidhiDownload(item,user_id='bhoonidhi_user', password='password', output_path='D:\\bhoonidhiDownloads')
  
```

The module fetches the results seperately and concatenates the results in a list format. 

One can download products easily from this library
This module shall be enabled for bhoondihiAPI which is currently under construction. Thematic based search, on-demand-LULC classification module libraries shall be released soon. 

