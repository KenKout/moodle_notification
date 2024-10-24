import html2text
from pymongo import MongoClient
from bson.objectid import ObjectId
import requests
import random
from utils.config import *
import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def convert_html_to_text(html_content):
    try:
        # Initialize the HTML to Text converter
        html_to_text = html2text.HTML2Text()

        # Set options for the converter
        html_to_text.body_width = 0  # No line wrapping
        html_to_text.ignore_links = True  # Ignore hyperlinks
        html_to_text.ignore_images = True  # Ignore images

        # Convert HTML to plain text
        plain_text = html_to_text.handle(html_content)
        return plain_text
    except Exception as e:
        logger.error(f'Error converting HTML to text: {e}')
        return ''


def diff_compare(old, new, is_module=False):
    changes = {'added': [], 'removed': [], 'changed': []}
    try:
        old_ids = {item['id'] for item in old}
        new_ids = {item['id'] for item in new}

        # Detect removed items
        for data in old:
            if data['id'] not in new_ids:
                logger.info(f'Removed: {data["name"]}')
                changes['removed'].append(data)

        # Detect added and changed items
        for data in new:
            if data['id'] not in old_ids:
                logger.info(f'Added: {data["name"]}')
                changes['added'].append(data)
                continue

            # Compare data when IDs are the same
            old_item = next((x for x in old if x['id'] == data['id']), None)
            if old_item:
                for key in data:
                    if data[key] != old_item.get(key):
                        if key != 'modules':
                            logger.info(f'Changed: {data["name"]}, key: {key}')
                            logger.info(f"From: {old_item[key]} To: {data[key]}")
                            temp_data = data.copy()
                            temp_data[key + '_old'] = old_item[key]
                            changes['changed'].append(temp_data)
                        else:
                            # Recursively check modules
                            module_changes = diff_compare(old_item[key], data[key], is_module=True)
                            changes['changed'].extend(module_changes['changed'])
                            changes['added'].extend(module_changes['added'])
                            changes['removed'].extend(module_changes['removed'])
    except Exception as e:
        logger.error(f'Error in diff_compare: {e}')
    return changes


def upload_data(data):
    try:
        client = MongoClient(MONGODB_URI)
        db = client['lms']
        collection = db['courses']
        collection.insert_one(data)
        logger.info('Data uploaded successfully')
    except Exception as e:
        logger.error(f'Error uploading data to MongoDB: {e}')


def get_data(query=None):
    try:
        client = MongoClient(MONGODB_URI)
        db = client['lms']
        collection = db['courses']
        if query:
            data = collection.find(query)
        else:
            data = collection.find()
        return list(data)
    except Exception as e:
        logger.error(f'Error getting data from MongoDB: {e}')
        return []


def update_data(data):
    try:
        client = MongoClient(MONGODB_URI)
        db = client['lms']
        collection = db['courses']
        result = collection.update_one({'_id': ObjectId(data['_id'])}, {'$set': data})
        if result.matched_count > 0:
            logger.info('Data updated successfully')
        else:
            logger.warning('No matching document found to update')
    except Exception as e:
        logger.error(f'Error updating data in MongoDB: {e}')


def send_notification(data):
    try:
        for change in data['added']:
            payload = {
                "content": "",
                "tts": False,
                "embeds": [{
                    "title": f"New content: {change['name']}",
                    "description": "Click title to check new content.",
                    "color": random.randint(1000000, 9999999),
                    "fields": [],
                    "url": change.get('url', ''),
                }],
                "components": [],
                "actions": {},
                "username": "E-Learning Notification",
                "avatar_url": "https://i.imgur.com/PX6pxLS.png"
            }
            try:
                response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                if response.status_code != 204:
                    logger.error(f'Failed to send notification for added content "{change["name"]}", Status code: {response.status_code}')
            except requests.exceptions.RequestException as e:
                logger.error(f'Error sending notification for added content "{change["name"]}": {e}')

        for change in data['removed']:
            payload = {
                "content": "",
                "tts": False,
                "embeds": [{
                    "title": f"Content removed: {change['name']}",
                    "description": "Click title to check removed content.",
                    "color": random.randint(1000000, 9999999),
                    "fields": [],
                    "url": change.get('url', ''),
                }],
                "components": [],
                "actions": {},
                "username": "E-Learning Notification",
                "avatar_url": "https://i.imgur.com/PX6pxLS.png"
            }
            try:
                response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                if response.status_code != 204:
                    logger.error(f'Failed to send notification for removed content "{change["name"]}", Status code: {response.status_code}')
            except requests.exceptions.RequestException as e:
                logger.error(f'Error sending notification for removed content "{change["name"]}": {e}')

        for change in data['changed']:
            for key in change:
                if key.endswith('_old'):
                    payload = {
                        "content": "",
                        "tts": False,
                        "embeds": [{
                            "title": f"Content changed: {change['name']}",
                            "description": "Click title to check changed content.",
                            "color": random.randint(1000000, 9999999),
                            "fields": [
                                {
                                    "name": f"Old {key.replace('_old', '')}",
                                    "value": str(change[key]),
                                    "inline": False
                                },
                                {
                                    "name": f"New {key.replace('_old', '')}",
                                    "value": str(change[key.replace('_old', '')]),
                                    "inline": False
                                }
                            ],
                            "url": change.get('url', ''),
                        }],
                        "components": [],
                        "actions": {},
                        "username": "E-Learning Notification",
                        "avatar_url": "https://i.imgur.com/PX6pxLS.png"
                    }
                    try:
                        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
                        if response.status_code != 204:
                            logger.error(f'Failed to send notification for changed content "{change["name"]}", Status code: {response.status_code}')
                    except requests.exceptions.RequestException as e:
                        logger.error(f'Error sending notification for changed content "{change["name"]}": {e}')
    except Exception as e:
        logger.error(f'Error in send_notification: {e}')
