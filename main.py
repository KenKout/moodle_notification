from utils.helper import *
import requests
from requests.structures import CaseInsensitiveDict
import json
import time
from flask import Flask
from utils.config import *
import threading
import concurrent.futures
import traceback

import logging

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Import Lock from threading module
from threading import Lock


class MOODLE_NOTI:
    NON_CHANGE = {'added': [], 'removed': [], 'changed': []}

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MoodleMobile 4.4.0 (44004)',
        'Origin': URL_LOGIN,
        'Referer': URL_LOGIN
    }

    def __init__(self):
        self.s = requests.Session()
        self.course_detail = []
        self.userid = None
        self.token = None
        self.total_course = []

    def login_sso(self):
        url = URL_CAS
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        try:
            resp = self.s.get(url, headers=headers, timeout=10).text
            lt = resp.split('<input type="hidden" name="lt" value="')[1].split('" />')[0]
            execution = resp.split('<input type="hidden" name="execution" value="')[1].split('" />')[0]
            data = f"username={USERNAME}&password={PASSWORD}&execution={execution}&_eventId=submit&submit=Login&lt={lt}"
            resp = self.s.post(url, headers=headers, data=data, timeout=10)
            logger.info('Function - Login: Success')
        except Exception as e:
            logger.error(f'Error in login_sso: {e}')
            raise

    def login_moodle(self):
        try:
            if TYPE_SSO == 'CAS':
                self.login_sso()
                url = URL_LOGIN + '/login/index.php?authCAS=CAS'
                url = URL_CAS + url
                url_launch = URL_LOGIN + '/admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=1&urlscheme=moodlemobile'
                login = self.s.get(url, headers=self.headers, timeout=10)
                self.userid = login.text.split('userid="')[1].split('"')[0]
                import httpx
                login = httpx.get(url_launch, headers=self.headers, cookies=self.s.cookies, timeout=10)
                raw_token = login.headers['location'].split('token=')[1]
                import base64
                self.token = base64.b64decode(raw_token).decode('utf-8').split(':::')[1]
                logger.info(f'Token: {self.token}')
            else:
                self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
                url = URL_LOGIN + '/login/token.php'
                data = {
                    'username': USERNAME,
                    'password': PASSWORD,
                    'service': 'moodle_mobile_app'
                }
                resp = self.s.get(url, headers=self.headers, params=data, timeout=10)
                self.token = resp.json()['token']

                url = URL_LOGIN + '/webservice/rest/server.php'
                params = {
                    'wsfunction': 'core_webservice_get_site_info',
                    'moodlewsrestformat': 'json'
                }
                data = 'moodlewssettingfilter=true&moodlewssettingfileurl=true&moodlewssettinglang=en&wsfunction=core_webservice_get_site_info&wstoken=' + self.token
                resp = self.s.post(url, headers=self.headers, data=data, params=params, timeout=10)
                self.userid = str(resp.json()['userid'])
        except Exception as e:
            logger.error(f'Error in login_moodle: {e}')
            raise

    def get_course(self):
        while True:
            try:
                self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
                url = URL_LOGIN + '/webservice/rest/server.php'
                params = {
                    'wsfunction': 'tool_mobile_call_external_functions',
                    'moodlewsrestformat': 'json'
                }
                data = ('requests[0][function]=core_enrol_get_users_courses'
                        f'&requests[0][arguments]={{"userid":"{self.userid}","returnusercount":"0"}}'
                        '&requests[0][settingfilter]=1&requests[0][settingfileurl]=1'
                        '&requests[1][function]=tool_mobile_get_plugins_supporting_mobile'
                        '&requests[1][arguments]={}&requests[1][settingfilter]=1&requests[1][settingfileurl]=1'
                        '&requests[2][function]=tool_mobile_get_config&requests[2][arguments]={}'
                        '&requests[2][settingfilter]=1&requests[2][settingfileurl]=1'
                        '&moodlewssettinglang=en&wsfunction=tool_mobile_call_external_functions'
                        f'&wstoken={self.token}')
                resp = requests.post(url, headers=self.headers, params=params, data=data, timeout=10)
                resp_json = resp.json()
                responses = resp_json.get('responses', [])
                if not responses or len(responses) == 0:
                    logger.warning('No responses in get_course')
                    time.sleep(5)
                    continue
                self.total_course = json.loads(responses[0]['data'])
                if self.total_course:
                    break
                else:
                    time.sleep(5)
            except Exception as e:
                logger.error(f'Error in get_course: {e}')
                time.sleep(5)

    def get_course_detail(self, courseid, retries=3):
        try:
            courseid = str(courseid)
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            url = URL_LOGIN + '/webservice/rest/server.php'
            params = {
                'wsfunction': 'core_course_get_contents',
                'moodlewsrestformat': 'json'
            }
            data = ('requests[0][function]=gradereport_user_get_access_information'
                    f'&requests[0][arguments]={{"courseid":"{courseid}"}}'
                    '&requests[0][settingfilter]=1&requests[0][settingfileurl]=1'
                    '&requests[1][function]=core_block_get_course_blocks'
                    f'&requests[1][arguments]={{"courseid":"{courseid}","returncontents":"1"}}'
                    '&requests[1][settingfilter]=1&requests[1][settingfileurl]=1'
                    '&requests[2][function]=core_course_get_contents'
                    f'&requests[2][arguments]={{"courseid":"{courseid}","options":[{{"name":"excludemodules","value":"0"}},{{"name":"excludecontents","value":"1"}},{{"name":"includestealthmodules","value":"1"}}]}}'
                    '&requests[2][settingfilter]=1&requests[2][settingfileurl]=1'
                    '&moodlewssettinglang=en&wsfunction=tool_mobile_call_external_functions'
                    f'&wstoken={self.token}')
            resp = requests.post(url, headers=self.headers, params=params, data=data, timeout=10)
            resp_json = resp.json()
            responses = resp_json.get('responses', [])
            if len(responses) >= 3:
                data = json.loads(responses[2]['data'])
                return data
            else:
                logger.warning(f'Insufficient responses in get_course_detail for courseid {courseid}')
                return []
        except Exception as e:
            logger.error(f'Error in get_course_detail: {e}. Retries left: {retries}')
            if retries > 0:
                return self.get_course_detail(courseid, retries - 1)
            else:
                raise e

    def process_data(self, data):
        return_data = []
        for item in data:
            modules = {"name": item['name'], "modules": [], "id": item['id']}
            for module in item['modules']:
                id_module = module['id']
                name = module.get('name', '')
                description = convert_html_to_text(module.get('description', '')).strip()
                url = module.get('url', '')
                modules['modules'].append({"id": id_module, "name": name, "description": description, "url": url})
            return_data.append(modules)
        return return_data


def FlaskApp():
    app = Flask(__name__)

    @app.route('/', methods=['GET'])
    def index():
        return 'Hello World'

    app.run(host='0.0.0.0', port=7860)


# Create a lock for protecting shared data structures
data_course_lock = Lock()

def threading_get_course_detail(moodle, courseid):
    try:
        data = {"id": courseid, "data": moodle.process_data(moodle.get_course_detail(courseid))}
        return data
    except Exception as e:
        logger.error(f'Error processing course {courseid}: {e}')
        raise e


if __name__ == '__main__':
    if not USERNAME or not PASSWORD:
        logger.error('Please provide username and password')
        exit()
    if HUGGINGFACE:
        threading.Thread(target=FlaskApp).start()
    moodle = MOODLE_NOTI()
    while True:
        try:
            moodle.login_moodle()
            moodle.get_course()
            break
        except Exception as e:
            logger.error(f'First login failed: {e}. Retrying...')
            time.sleep(10)
            continue

    while True:
        try:
            # Initial fetching of course details
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(threading_get_course_detail, moodle, course['id']) for course in moodle.total_course]
                DATA_COURSE = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        # Acquire lock before modifying shared data structure
                        with data_course_lock:
                            DATA_COURSE.append(result)
            break
        except Exception as e:
            logger.error(f'Error in initial fetching of course details: {e}. Retrying...')
            time.sleep(10)
            continue

    with data_course_lock:
        DATA_COURSE.sort(key=lambda x: x['id'])
    logger.info(f'Get course success. Total courses: {len(DATA_COURSE)}')

    while True:
        try:
            logger.info('Starting new iteration...')
            time.sleep(TIME_SLEEP)
            # Re-fetch courses in case new courses are added
            moodle.get_course()

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(threading_get_course_detail, moodle, course['id']) for course in moodle.total_course]
                DATA_COURSE_NEW = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        # Acquire lock before modifying shared data structure
                        with data_course_lock:
                            DATA_COURSE_NEW.append(result)
            with data_course_lock:
                DATA_COURSE_NEW.sort(key=lambda x: x['id'])

            # Use locks when accessing shared data structures
            with data_course_lock:
                if DATA_COURSE_NEW != DATA_COURSE:
                    logger.info('Change detected')
                    # Create dictionaries for easy comparison
                    DATA_COURSE_DICT = {course['id']: course for course in DATA_COURSE}
                    DATA_COURSE_NEW_DICT = {course['id']: course for course in DATA_COURSE_NEW}

                    old_course_ids = set(DATA_COURSE_DICT.keys())
                    new_course_ids = set(DATA_COURSE_NEW_DICT.keys())

                    added_course_ids = new_course_ids - old_course_ids
                    removed_course_ids = old_course_ids - new_course_ids
                    common_course_ids = old_course_ids & new_course_ids

                    changes = {'added': [], 'removed': [], 'changed': []}

                    # Handle added courses
                    for course_id in added_course_ids:
                        data_new = DATA_COURSE_NEW_DICT[course_id]
                        logger.info(f'New course added: {data_new["id"]}')
                        changes['added'].append({'name': data_new['id'], 'url': f'{URL_LOGIN}/course/view.php?id={data_new["id"]}'})

                    # Handle removed courses
                    for course_id in removed_course_ids:
                        data_old = DATA_COURSE_DICT[course_id]
                        logger.info(f'Course removed: {data_old["id"]}')
                        changes['removed'].append({'name': data_old['id'], 'url': f'{URL_LOGIN}/course/view.php?id={data_old["id"]}'})

                    # Handle changed courses
                    for course_id in common_course_ids:
                        data_old = DATA_COURSE_DICT[course_id]
                        data_new = DATA_COURSE_NEW_DICT[course_id]
                        if data_old['data'] != data_new['data']:
                            diff = diff_compare(data_old['data'], data_new['data'])
                            if diff != moodle.NON_CHANGE:
                                logger.info(f'Changes detected in course {course_id}. Sending notification...')
                                send_notification(diff)

                    # Send notifications if any course was added, removed
                    if changes['added'] or changes['removed'] or changes['changed']:
                        send_notification(changes)
                    else:
                        logger.info('No significant changes detected')

                    # Update the DATA_COURSE with the new data
                    DATA_COURSE = DATA_COURSE_NEW.copy()
                else:
                    logger.info(f'No changes detected, sleeping for {TIME_SLEEP} seconds')
        except Exception as e:
            traceback.print_exc()
            logger.error(f'Error: {e}.')
            time.sleep(5)
            continue
