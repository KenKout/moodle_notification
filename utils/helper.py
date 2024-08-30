import html2text
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
import random
from utils.config import *

def convert_html_to_text(html_content):

    # Initialize the HTML to Text converter
    html_to_text = html2text.HTML2Text()

    # Set options for the converter
    html_to_text.body_width = 0  # No line wrapping
    html_to_text.ignore_links = True  # Ignore hyperlinks
    html_to_text.ignore_images = True  # Ignore images

    # Convert HTML to plain text
    plain_text = html_to_text.handle(html_content)
    return plain_text


def diff_compare(old, new, is_module=False):
    changes = {'added': [], 'removed': [], 'changed': []}
    for data in old:
        if data['id'] not in [x['id'] for x in new]:
            print('Removed:', data['name'])
            if is_module:
                print('ID:', data['id'])
                print('Description:', data['description'])
                print('URL:', data['url'])
                changes['removed'].append(data)
            else:
                changes['removed'].append(data)
                print('Section ID:', data['id'])
                print('Summary:', data['summary'])
                for data in data['modules']:
                    print('Module Name:', data['name'])
                    print('Module ID:', data['id'])
                    print('Module Description:', data['description'])
                    print('Module URL:', data['url'])
    for data in new:
        if data['id'] not in [x['id'] for x in old]:
            print('Added:', data['name'])
            if is_module:
                print('ID:', data['id'])
                print('Description:', data['description'])
                print('URL:', data['url'])
                print(data)
                changes['added'].append(data)
            else:
                changes['added'].append(data)
                print('Section ID:', data['id'])
                print('Summary:', data['summary'])
                for data in data['modules']:
                    print('Module Name:', data['name'])
                    print('Module ID:', data['id'])
                    print('Module Description:', data['description'])
                    print('Module URL:', data['url'])
            # Print new values
            # print('New:', data)
            continue
        for key in data:
            if data[key] != [x for x in old if x['id'] == data['id']][0][key]:
                # print('Changed:', data['name'], key)
                print('Changed:', [x for x in old if x['id'] == data['id']][0]['name'], "'s", key)
                # Print old and new values
                if key != 'modules':
                    print('From:', [x for x in old if x['id'] == data['id']][0][key])
                    print('To:', data[key])
                    # Add old data with key_old
                    temp_data = {**data,key + '_old': [x for x in old if x['id'] == data['id']][0][key]}
                    changes['changed'].append(temp_data)
                else:
                    return_data = diff_compare([x for x in old if x['id'] == data['id']][0][key], data[key], is_module=True)
                    changes['changed'].extend(return_data['changed'])
                    changes['added'].extend(return_data['added'])
                    changes['removed'].extend(return_data['removed'])
    return changes


def upload_data(data):
    client = MongoClient(MONGODB_URI)
    db = client['lms']
    collection = db['courses']
    collection.insert_one(data)


def get_data(query=None):
    client = MongoClient(MONGODB_URI)
    db = client['lms']
    collection = db['courses']
    if query:
        return collection.find(query)
    return collection.find()


def update_data(data):
    client = MongoClient(MONGODB_URI)
    db = client['lms']
    collection = db['courses']
    collection.update_one({'_id': ObjectId(data['_id'])}, {'$set': data})


def send_notification(data):
    for change in data['added']:
        payload = {
            "content":
                "",
            "tts":
                False,
            "embeds": [{
                "title": f"New content: {change['name']}",
                "description": f"Click title to check new content.",
                "color": random.randint(1000000, 9999999),
                "fields": [],
                "url": change['url'],
            }],
            "components": [],
            "actions": {},
            "username":
                "E-Learning Notification",
            "avatar_url":
                "https://i.imgur.com/PX6pxLS.png"
        }
        print(requests.post(WEBHOOK_URL, json=payload).text)
    for change in data['removed']:
        payload = {
            "content":
                "",
            "tts":
                False,
            "embeds": [{
                "title": f"Content removed: {change['name']}",
                "description": f"Click title to check removed content.",
                "color": random.randint(1000000, 9999999),
                "fields": [],
                "url": change['url'],
            }],
            "components": [],
            "actions": {},
            "username":
                "E-Learning Notification",
            "avatar_url":
                "https://i.imgur.com/PX6pxLS.png"
        }
        requests.post(WEBHOOK_URL, json=payload)
    for change in data['changed']:
        payload = {
            "content":
                "",
            "tts":
                False,
            "embeds": [{
                "title": f"Content changed: {change['name']}",
                "description": f"Click title to check changed content.",
                "color": random.randint(1000000, 9999999),
                "fields": [],
                "url": change['url'],
            }],
            "components": [],
            "actions": {},
            "username":
                "E-Learning Notification",
            "avatar_url":
                "https://i.imgur.com/PX6pxLS.png"
        }
        requests.post(WEBHOOK_URL, json=payload)
    for change in data["changed"]:
        payload = {
            "content":
                "",
            "tts":
                False,
            "embeds": [{
                "title": f"Content changed in {change['name']}",
                "description": f"Click title to check changed content.",
                "color": random.randint(1000000, 9999999),
                "fields": [],
                "url": change['url'],
            }],
            "components": [],
            "actions": {},
            "username":
                "E-Learning Notification",
            "avatar_url":
                "https://i.imgur.com/PX6pxLS.png"
        }
        requests.post(WEBHOOK_URL, json=payload)
