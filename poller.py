"""
@license

Copyright 2024 Cisco Systems, Inc. or its affiliates

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


"""
@author	Nick Ciesinski (nciesins@cisco.com)
"""

import requests
import sqlite3
import unicodedata
import tiktoken
import time
import json
import yaml
import urllib3
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth
from openai import OpenAI

# Disable warning about SSL verify being disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

accessToken = None

def debug(message):
    if config['debug']['enabled']:
        print('DEBUG: ',message)

def getUmbrellaToken():
    url = 'https://api.umbrella.com/auth/v2/token'
    response = requests.post(url, auth=HTTPBasicAuth(config['umbrella']['apiKey'], config['umbrella']['apiKeySecret']))
    if (response.status_code == 200):
        accessToken = response.json()['access_token']
        return accessToken
    else:
        debug('Error Authenticating: ' + response.status_code)
        return None
    
def getUmbrellaReportingData(accessToken):
    domains = set() 
    url = 'https://api.umbrella.com/reports/v2/activity/dns'
    fromString = f"-{config['umbrella']['reportingLookback']}minutes"
    params = {'limit':5000, 'to': 'now', 'from': fromString}
    headers = {'Authorization': 'Bearer ' + accessToken}
    response = requests.get(url,params=params, headers=headers)
    try:
        for item in response.json()['data']:
            # Check if 'categories' key is empty
            if not item.get('categories'):
                # Only add domain to list if it had a DNS entry returned and is a IPv4 lookup and its vertict was allowed
                if (item.get('returncode') == 0 and (item.get('querytype') == 'A') and (item.get('verdict') == 'allowed')):
                    domains.add(item['domain'])
        if not domains:
            debug("No Uncategorized Domains Found")
        else:
            debug(domains)
    except Exception as e:
        debug("Umbrellay Query Empty")
    finally:
        return(domains)
    
def newDatabaseCheck(dbConnection):
    dbCursor = dbConnection.cursor()
    dbCursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hostdata'")
    dbTableExists = dbCursor.fetchone()

    if not dbTableExists:
        dbCursor.execute('''CREATE TABLE hostdata (
                            id INTEGER PRIMARY KEY,
                            hostname TEXT NOT NULL,
                            seenCount INTEGER,
                            aiResult TEXT NULL,
                            umbrellaAction INTEGER,
                            createdOn INTEGER,
                            lastSeen INTEGER 
                          )''')
        dbConnection.commit()
        debug('Database table created successfully')
    else:
        debug('Database table already exists')

def insertData(dbConnection,umbrellaDomains):
    
    dbCursor = dbConnection.cursor()
    for item in umbrellaDomains:

        dbCursor.execute('SELECT id,hostname,seenCount FROM hostdata WHERE hostname=?',(item,))
        existingEntry = dbCursor.fetchone()

        if existingEntry:
            dbCursor.execute('UPDATE hostdata SET seenCount=?, lastSeen=? WHERE id=?', (existingEntry[2] + 1, int(time.time()), existingEntry[0],))
            dbConnection.commit()
            debug('Row updated successfully: ' + item)
        else:
            if config['ai']['enabled']:
                aiResult = getAiResult(item)
                dbCursor.execute('INSERT INTO hostdata (hostname, seenCount, aiResult, lastSeen, createdOn) VALUES (?, ?, ?, ?, ?)', (item, 1, aiResult,int(time.time()),int(time.time()),))
                dbConnection.commit()
            else:            
                dbCursor.execute('INSERT INTO hostdata (hostname, seenCount, lastSeen, createdOn) VALUES (?, ?, ?, ?)', (item, 1,int(time.time()),int(time.time()),))
                dbConnection.commit()
            debug('New row added: ' + item)

def removeNonASCIICharacters(text):
    cleanedText = ''
    for char in text:
        if ord(char) < 128 or unicodedata.category(char) in ('Lu', 'Ll', 'Lt', 'Lo', 'Nd'):
            cleanedText += char
    return cleanedText

def tokenResize(text):
    encoding = tiktoken.encoding_for_model('gpt-3.5-turbo-0125')
    tokenizedText = encoding.encode(text)
    debug('Pre-resize token size: ' + str(len(tokenizedText)))   
    del tokenizedText[config['ai']['maxInputToken']:]
    debug('Post-resize token size: ' + str(len(tokenizedText)))
    return encoding.decode(tokenizedText)

def getAiResult(hostname):
    try:
        response = requests.get('https://'+hostname,verify=False,timeout=10)
    except requests.exceptions.Timeout:
        debug('Connection Timeout')
        return 'Connection Timeout'

    if response.status_code == 200:
        # Parse the HTML content, strip HTML tags, remove non US characters
        parsedContent = BeautifulSoup(response.content, 'html.parser')
        siteText = parsedContent.get_text(separator='\n', strip=True)
        siteText = removeNonASCIICharacters(siteText)
        
        if siteText:
            if config['ai']['maxInputToken'] > 0:
                siteText = tokenResize(siteText)

            client = OpenAI(api_key=config['ai']['openAIKey'])
            completion = client.chat.completions.create(
                model='gpt-3.5-turbo-0125',
                max_tokens=5,
                temperature=0.1,
                messages=[
                    {'role': 'system', 'content': f'Is the text from a {config["ai"]["categories"]} website? Answer Yes or No with percent confidence your answer is correct'},
                    {'role': 'user', 'content': siteText},
                ]
            )
            debug(completion.choices[0].message)
            return completion.choices[0].message.content
    else:
        debug('Connection Error ' + str(response.status_code))
        return 'Connection Error ' + str(response.status_code)

def dataPurge(dbConnection):
    dbCursor = dbConnection.cursor()
    dbCursor.execute('DELETE from hostdata WHERE umbrellaAction IS NULL AND lastSeen <= ?', ((int(time.time()) - (config['database']['defaultPurgeDays'] * 86400)),))
    dbConnection.commit()
    dbCursor.execute('DELETE from hostdata WHERE umbrellaAction IS NOT NULL AND lastSeen <= ?', ((int(time.time()) - (config['database']['blockedPurgeDays'] * 86400)),))
    
accessToken = getUmbrellaToken()
if (accessToken):
    umbrellaDomains = getUmbrellaReportingData(accessToken)
    dbConnection = sqlite3.connect(config['database']['filename'])
    newDatabaseCheck(dbConnection)
    insertData(dbConnection,umbrellaDomains)
    dataPurge(dbConnection)
    dbConnection.close()
else:
    exit(1)
exit(0)