from utils.helper import *
import requests
from requests.structures import CaseInsensitiveDict
import json
import time
from flask import Flask
from utils.config import *
import threading

import logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

DATA_COURSE = []


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

    def login_sso(self):
        url = URL_CAS
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        resp = self.s.get(url, headers=headers).text
        lt = resp.split('<input type="hidden" name="lt" value="')[1].split('" />')[0]
        execution = resp.split(
            '<input type="hidden" name="execution" value="')[1].split('" />')[0]
        data = f"username={USERNAME}&password={PASSWORD}&execution={execution}&_eventId=submit&submit=Login&lt={lt}"
        resp = self.s.post(url, headers=headers, data=data)
        logger.info('Function - Login: Success')

    def login_moodle(self):
        if TYPE_SSO == 'CAS':
            self.login_sso()
            url = URL_LOGIN + 'login/index.php?authCAS=CAS'
            url = URL_CAS + url
            url_launch = URL_LOGIN + 'admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=1&urlscheme=moodlemobile'
            login = self.s.get(url, headers=self.headers)
            self.userid = login.text.split('userid="')[1].split('"')[0]
            import httpx
            login = httpx.get(url_launch, headers=self.headers, cookies=self.s.cookies)
            raw_token = login.headers['location'].split('token=')[1]
            import base64
            self.token = base64.b64decode(raw_token).decode('utf-8').split(':::')[1]
            logger.info(f'Token: {self.token}')
        else:
            url = URL_LOGIN + 'login/token.php'
            data = {
                'username': USERNAME,
                'password': PASSWORD,
                'service': 'moodle_mobile_app'
            }
            resp = self.s.get(url, headers=self.headers, params=data)
            self.token = resp.json()['token']

    def get_course(self):
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        url = URL_LOGIN + 'webservice/rest/server.php'
        params = {
            'wsfunction': 'tool_mobile_call_external_functions',
            'moodlewsrestformat': 'json'
        }
        data = 'requests[0][function]=core_enrol_get_users_courses&requests[0][arguments]={"userid":"'+self.userid+'","returnusercount":"0"}&requests[0][settingfilter]=1&requests[0][settingfileurl]=1&requests[1][function]=tool_mobile_get_plugins_supporting_mobile&requests[1][arguments]={}&requests[1][settingfilter]=1&requests[1][settingfileurl]=1&requests[2][function]=tool_mobile_get_config&requests[2][arguments]={}&requests[2][settingfilter]=1&requests[2][settingfileurl]=1&moodlewssettinglang=en&wsfunction=tool_mobile_call_external_functions&wstoken=' + self.token
        resp = requests.post(url, headers=self.headers, params=params, data=data)
        self.total_course = json.loads(resp.json()['responses'][0]['data'])


    def get_course_detail(self, courseid):
        courseid = str(courseid)
        self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        url = URL_LOGIN + 'webservice/rest/server.php'
        params = {
            'wsfunction': 'core_course_get_contents',
            'moodlewsrestformat': 'json'
        }
        data = 'requests[0][function]=gradereport_user_get_access_information&requests[0][arguments]={"courseid":"'+courseid+'"}&requests[0][settingfilter]=1&requests[0][settingfileurl]=1&requests[1][function]=core_block_get_course_blocks&requests[1][arguments]={"courseid":"'+courseid+'","returncontents":"1"}&requests[1][settingfilter]=1&requests[1][settingfileurl]=1&requests[2][function]=core_course_get_contents&requests[2][arguments]={"courseid":"'+courseid+'","options":[{"name":"excludemodules","value":"0"},{"name":"excludecontents","value":"1"},{"name":"includestealthmodules","value":"1"}]}&requests[2][settingfilter]=1&requests[2][settingfileurl]=1&moodlewssettinglang=en&wsfunction=tool_mobile_call_external_functions&wstoken=' + self.token
        resp = requests.post(url, headers=self.headers, params=params, data=data)
        return json.loads(resp.json()['responses'][2]['data'])


    def process_data(self, data):
        return_data = []
        for data in data:
            modules = {"name": data['name'], "modules": [], "id": data['id']}
            for module in data['modules']:
                id_module = module['id']
                name = module.get('name', '')
                description = convert_html_to_text(module.get('description', '')).strip()
                url = module.get('url', '')
                modules['modules'].append({"id": id_module, "name": name, "description": description, "url": url})
            return_data.append(modules)
        return return_data


def refresh_course(lms):
    while True:
        moodle.get_course()
        time.sleep(3600)


def FlaskApp():
    app = Flask(__name__)
    @app.route('/', methods=['GET'])
    def index():
        return 'Hello World'
    app.run(host='0.0.0.0', port=7860)


if __name__ == '__main__':
    if not USERNAME or not PASSWORD:
        logger.error('Please provide username and password')
        exit()
    if HUGGINGFACE:
        threading.Thread(target=FlaskApp).start()
    moodle = MOODLE_NOTI()
    moodle.login_moodle()
    moodle.get_course()
    for course in moodle.total_course:
        DATA_COURSE.append({"id": course['id'], "data": moodle.process_data(moodle.get_course_detail(course['id']))})
    DATA_COURSE.sort(key=lambda x: x['id'])
    logger.info(f'Get course success. Total courses: {len(DATA_COURSE)}')
    while True:
        time.sleep(TIME_SLEEP)
        DATA_COURSE_NEW = []
        for course in moodle.total_course:
            DATA_COURSE_NEW.append({"id": course['id'], "data": moodle.process_data(moodle.get_course_detail(course['id']))})
        DATA_COURSE_NEW.sort(key=lambda x: x['id'])
        if DATA_COURSE_NEW != DATA_COURSE:
            logger.info('Change detected')
            ID = [x['id'] for x in DATA_COURSE]
            for data_old in DATA_COURSE:
                for data_new in DATA_COURSE_NEW:
                    if data_new['id'] not in ID:
                        logger.info(f'New course: {data_new["id"]}')
                        send_notification(moodle.NON_CHANGE.copy()['added'].append({'name': data_new['id'], 'url': f'https://moodle.hcmut.edu.vn/course/view.php?id={data_new["id"]}'}))
                        DATA_COURSE.append(data_new)
                        break
                    if data_old['id'] == data_new['id']:
                        if data_old['data'] == data_new['data']:
                            logger.info(f'Data ID: {data_old["id"]} does not change')
                            break
                        changes = diff_compare(data_old['data'], data_new['data'])
                        if changes != moodle.NON_CHANGE:
                            logger.info(f'Change data: {changes}')
                            send_notification(changes)
                            DATA_COURSE.remove(data_old)
                            DATA_COURSE.append(data_new)
                            break
        else:
            logger.info('No change, sleep 5 minutes')
