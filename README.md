# Poncho: Uncategorized Website Management Tool For Cisco Umbrella
*"When it's raining in all directions, an Umbrella may not be enough; grab a Poncho."*

## Overview

Poncho addresses the challenge of managing uncategorized websites accessed by users on the Internet. It regularly retrieves Umbrella logs to identify destinations lacking categorization. Poncho can then employ OpenAI to analyze website content, assessing if it aligns with predefined categories. 

Administrators can review the findings via a web interface, where they can investigate each destination further and decide whether to add it to the Umbrella global block list.

The use of OpenAI analysis is optional and requires an OpenAI API account, subject to usage charges. In the absence of OpenAI integration, Poncho still provides a comprehensive list of uncategorized websites within the logs, offering administrators the ability to review sites and add destinations to the block list after manual review.

<center><img src="doc/images/poncho-interface.png" style="max-width: 75%" alt="Poncho"></center>

## Features

- **Umbrella Log Integration:** Pulls Umbrella logs to identify uncategorized destinations.
- **OpenAI Analysis (optional):** Utilizes OpenAI to assess website content against predefined categories.
- **Web Interface:** Provides administrators with a user-friendly interface to review and manage uncategorized destinations.
- **Global Block List Management:** Enables administrators to add destinations to the Umbrella global block list.

## Technologies & Frameworks Used

**Cisco Products:**

- Cisco Umbrealla

## Technologies Used

- **Python3:** Utilized for backend development (Flask, SQLite3).
- **Docker:** Provides containerization for easy deployment.
- **Frontend:** Bootstrap, jQuery, feathericon, DataTables.

## Installation and Operation

### Standalone (No Python Virtual Enviroment)

1. Clone the Poncho repository. `git clone XXXXXX`.
2. Install dependencies using `pip install -r requirements.txt`.
3. Edit config.yaml and add Umbrella and OpenAI API credentials and make other modifications as required.
4. Setup a cron process to run `poller.py` at the same interval configured in config.yaml.
    - Example Linux:
        - Run `crontab -e`
        - Add `*/15 * * * * python3 /path/to/poller.py`
        - Save and exit `ESC :wq`
4. Run the web application using `gunicorn --workers=4 --bind 0.0.0.0:8000 web:app`.
    - Note, this example will run the web application without SSL on port 8000.  See gunicorn documentation or proxy the app behing Nginx, Apache, or other web server to add SSL.
6. Access the web interface at: `http://localhost:8000`.

### Standalone (Python Virtual Enviroment)

1. Clone the Poncho repository. `git clone XXXXXX`.
2. Create and activate a virtual environment. `python3 -m venv venv ; source venv/bin/activate`
3. Install dependencies using `pip install -r requirements.txt`.
4. Edit config.yaml and add Umbrella and OpenAI API credentials and make other modifications as required.
5. Setup a cron process to run `poller.py` at the same interval configured in config.yaml.
    - Example Linux:
        - Run `crontab -e`
        - Add `*/15 * * * * /path/to/poncho/venv/bin/python3 /path/to/poller.py`
        - Save and exit `ESC :wq`
6. Run the web application using `venv/bin/gunicorn --workers=4 --bind 0.0.0.0:8000 web:app`.
    - Note, this example will run the web application without SSL on port 8000.  See gunicorn documentation or proxy the app behing Nginx, Apache, or other web server to add SSL.
7. Access the web interface at: `http://localhost:8000`.

### Docker

1. Clone the Poncho repository: `git clone XXXXXX`.
2. Edit config.yaml and add Umbrella and OpenAI API credentials and make other modifications as required.
3. Build the Docker container: `docker build -t poncho .`.
4. Setup a cron process to run `poller.py` inside the Docker container at the same interval configured in config.yaml.
    - Example Linux:
        - Run `crontab -e`
        - Add `*/15 * * * * docker exec poncho python3 /poller.py`
        - Save and exit `ESC :wq`
5. Run the container: `docker run -d -p 8000:8000 poncho`.
    - Note, this example will run the web application without SSL on port 8000.  See gunicorn documentation or proxy the app behing Nginx, Apache, or other web server to add SSL.
6. Access the web interface at: `http://localhost:8000`.

## Creating API Keys in Umbrella and OpenAI

### Umbrella

1. Login to Umbrella.
2. Navigate to Admin -> API Keys.
3. Press the Add button in the upper right corner of the screen.
4. Give the API Key a Name and Grant Scope Access as follows:
    - Policies / Destinations: Read/Write
    - Reports / Granular Events: Read-Only
    - Policies / Destination Lists: Read/Write
5. Copy the API Key and Key Secret to `config.yaml`.

<center><img src="doc/images/umbrella-api-key.png" style="max-width: 75%" alt="Poncho"></center>

### OpenAI

1. Login to your OpenAI Account.
2. Navigate to API Keys ([https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
3. Press `Create new secret key`.
4. Enter a name for the new key and then press `Create secret key`.
5. Copy the key and place it in `config.yaml`.

<center><img src="doc/images/openai-api-key.png" style="max-width: 40%" alt="Poncho"></center>

## FAQ


1. How much does it cost to use OpenAI with Poncho?
    - Usage costs will vary based on the number of uncategorized sites Poncho finds in your Umbrella logs. Currently, Poncho is set to use the inexpensive gpt-3.5-turbo-0125 model. This model costs about $0.01 per 1K tokens. By default, Poncho uses no more than 255 tokens per site lookup. Poncho will only query OpenAI for new sites not already in the internal Poncho database.
2. How accurate is OpenAI analysis?
    - This is dependent on the websites Poncho finds as uncategorized in your Umbrella logs. By default, Poncho is set to input a maximum of 250 tokens which may not be a complete website. While in testing, this number seems sufficient, you may have to adjust the token size in config.yaml to have OpenAI review more of a website and return more accurate results. Also, the analysis of a website with OpenAI is meant to guide an administrator on which uncategorized sites to focus on, not be the be-all, end-all opinion on what a website may contain for content.
3.  Is the Poncho DB backed up?
    - No, as Poncho uses SQLite3, there is a DB file (data/poncho.db) that gets created when poller.py runs. A backup of this file is recommended if you wish to restore from a lost or deleted DB file.

## Authors

- Nick Ciesinski

## License

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