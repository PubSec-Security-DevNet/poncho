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

from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
import sqlite3
import hashlib
import yaml
import json
import bcrypt
from requests.auth import HTTPBasicAuth
from datetime import date,datetime

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

app = Flask(__name__)
app.secret_key = config['web']['secretKey']

def unixtimeDatetime(unixtime):
    return datetime.utcfromtimestamp(unixtime).strftime('%Y-%m-%d')

app.jinja_env.filters['unixtimeDatetime'] = unixtimeDatetime

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
        debug(f'Error Authenticating: {response.status_code}')
        return None
    
def getUmbrellaGlobalBlockListID(accessToken):
    url = 'https://api.umbrella.com/policies/v2/destinationlists'
    headers = {'Authorization': 'Bearer ' + accessToken}
    response = requests.get(url, headers=headers)
    for item in response.json()['data']:
        if item.get('name') == 'Global Block List':
            return item.get('id')

def addGlobalBlockListHost(accessToken,umbrellaGlobalBlockListID,hostname):
    found = False
    url = f'https://api.umbrella.com/policies/v2/destinationlists/{umbrellaGlobalBlockListID}/destinations'
    headers = {'Authorization': 'Bearer ' + accessToken}
    response = requests.get(url, headers=headers)
    for item in response.json()['data']:
        if item.get('destination') == hostname:
            found = True

    if not found:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer" + accessToken
        }
        payload = f'''[
            {{ "destination": "{hostname}",
                "comment": "Added by Poncho {date.today()}" }}
            ]'''
        response = requests.post(url, headers=headers, data=payload)
        debug(f'Add {hostname} Block Response: {response}')
        return True
    else:
        return None

def removeGlobalBlockListHost(accessToken,umbrellaGlobalBlockListID,hostname):
    found = False
    url = f'https://api.umbrella.com/policies/v2/destinationlists/{umbrellaGlobalBlockListID}/destinations'
    headers = {'Authorization': 'Bearer ' + accessToken}
    response = requests.get(url, headers=headers)
    for item in response.json()['data']:
        if item.get('destination') == hostname:
            found = True
    
    if found:
        url = f'https://api.umbrella.com/policies/v2/destinationlists/{umbrellaGlobalBlockListID}/destinations/remove'
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": "Bearer" + accessToken
        }

        payload = f'''[ {item.get('id')} ]'''
        response = requests.delete(url, headers=headers, data=payload)
        debug(f'Remove {hostname} Block Response: {response}')
        return True
    else:
        return None

def getDbConection():
    conn = sqlite3.connect(config['database']['filename'])
    conn.row_factory = sqlite3.Row
    return conn

def verifyPassword(config_password, input_password):
    return bcrypt.checkpw(input_password.encode('utf-8'), config_password.encode('utf-8'))

# Routes
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    conn = getDbConection()
    hosts = conn.execute('SELECT * FROM hostdata').fetchall()
    conn.close()
    return render_template('index.html', hosts=hosts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if verifyPassword(config['web']['password'], password):
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/updateumbrella/<int:host_id>')
def updateumbrella(host_id):
    addedBlock = None
    removedBlock = None
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    dbConnection = getDbConection()
    dbCursor = dbConnection.cursor()
    host = dbCursor.execute('SELECT hostname,umbrellaAction FROM hostdata WHERE id = ?', (host_id,)).fetchone()

    accessToken = getUmbrellaToken()
    umbrellaGlobalBlockListID = getUmbrellaGlobalBlockListID(accessToken)
    
    if not host['umbrellaAction']:
        addedBlock = addGlobalBlockListHost(accessToken,umbrellaGlobalBlockListID,host['hostname'])
    else:
        removedBlock = removeGlobalBlockListHost(accessToken,umbrellaGlobalBlockListID,host['hostname'])

    if addedBlock:
        dbCursor.execute('UPDATE hostdata SET umbrellaAction=True WHERE id=?', (host_id,))
        dbConnection.commit()
    
    if removedBlock:
        dbCursor.execute('UPDATE hostdata SET umbrellaAction=NULL WHERE id=?', (host_id,))
        dbConnection.commit()
    
    dbCursor.close()
    dbConnection.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=config['debug']['enabled'])
