import json
import logging
import uuid
import warnings
from time import sleep

import requests
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)
file_handler = logging.FileHandler(filename="logs/desney.log")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger("desney")
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

class Desney:
    def __init__(self, username, password, one_day="", one_day_count=0, debug=False):
        self.debug = debug
        self.uuid = str(uuid.uuid4())
        self.default_header = {
            "X-Store-Id": 'shdr_mobile',
            "X-View-Type": 'mobile',
            "X-Source-Type": 'main_cart',
            "X-Language": "zh",
            "x-Conversation-Id": self.uuid,
            "X-Platform": "Hybrid",
            "Connection": "keep-alive",
            "X-Requested-With": "com.disney.shanghaidisneyland_goo",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh",
            "channel": "mobile",
            "Origin": "https://central.shanghaidisneyresort.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh,en-US;q=0.9,en;q=0.8",
        }
        self.session = requests.Session()
        self.status = [200, 201]
        self.messages = []
        self.username = username
        self.password = password
        self.uuid = str(uuid.uuid4())
        self.auth_token = ""
        self.hash = hash(username)
        self.sw_id = None
        self.profile = None
        self.access_token = None
        self.quantity = 0
        self.unit_price = 0
        self.total_price = 0
        self.target_date_en = None
        self.target_date_cn = None
        self.start_time = None
        self.government_id = None
        self.vids = []
        self.first_name = ""
        self.last_name = ""
        self.payment_id = None
        self.order = ""
        self.morning_card = ""
        self.one_day = one_day
        self.one_day_count = one_day_count
        self.card = "321025197912160221"
        self.contact_info = {}
        self.login_url = "https://www.shanghaidisneyresort.com/dprofile/api/v7/guests/login"
        self.sync_url = "https://www.shanghaidisneyresort.com/dprofile/api/login/phpsync"
        self.eligible_url = "https://central.shanghaidisneyresort.com/epep/api/party"
        self.morning_confirm = "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/comfirm"
        self.check_morning_date_url = "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/calender"
        self.check_one_day_url = "https://central.shanghaidisneyresort.com/ticketing/api/v1/tickets/book/information/shdr-theme-park-tickets?storeId=shdr_mobile"
        self.mock_url = "https://central.shanghaidisneyresort.com/ticketing/api/v1/cart/tickets/mock"
        self.one_day_order_url = "https://central.shanghaidisneyresort.com/order/api/order/create"
        self.token_url = "https://central.shanghaidisneyresort.com/order/api/auth/token"
        self.order_url = 'https://central.shanghaidisneyresort.com/order/api/order'
        self.link_order_url = 'https://central.shanghaidisneyresort.com/epep/api/linkOrderFind'
        self.confirm_order_url = 'https://central.shanghaidisneyresort.com/epep/api/linkConfirm'
        self.login_response = None
        self.sync_token_response = None
        self.eligible_response = None
        self.morning_price_response = None
        self.morning_confirm_response = None
        self.check_morning_date_response = None
        self.morning_transaction_response = None
        self.check_one_day_response = None
        self.get_one_day_mock_response = None
        self.one_day_order_response = None
        self.get_token_response = None
        self.get_order_info_response = None
        self.find_link_order_response = None
        self.confirm_link_order_response = None

    def post(self, url, data, header=None, debug=False):
        self.load_cookies()
        post_header = header if header else self.default_header
        try:
            response = self.session.post(url, json=data, headers=post_header, verify=False)
        except Exception as e:
            print(e)
        if debug or self.debug:
            print(response.json())
        if response.status_code in self.status:
            self.store_cookies()
            return response.json()
        print("post end")
        return None

    def get(self, url, data=None, header=None):
        if data is None:
            data = {}
        self.load_cookies()
        post_header = header if header else self.default_header
        response = self.session.get(url, json=data, headers=post_header, verify=False)
        if response.status_code in self.status:
            self.store_cookies()
            return response.json()
        return None

    def get_message(self):
        return self.messages

    def attach_header(self):
        self.default_header['Authorization'] = "bearer {}".format(self.auth_token),

    def store_cookies(self):
        try:
            with open(f"cookies/{self.username}.json", "w") as f:
                json.dump(self.session.cookies.get_dict(), f)
        except Exception as e:
            pass

    def load_cookies(self):
        try:
            with open(f"cookies/{self.username}.json", "r") as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
        except Exception as e:
            pass

    def login(self):
        logger.info(f"开始登录 {self.username}, {self.password}")
        data = {"pinPass": False, "loginType": 1, "loginName": self.username, "mobileAreaNum": "86",
                "mobileCountryISO2": "CN", "functionType": "GUEST_LOGIN_MOBILE",
                "password": self.password,
                "passwordEncrypted": False, "langPref": "zh", "sourceId": "DPRD-SHDR.MOBILE.ANDROID-PROD",
                "sessionid": "undefined"}
        self.login_response = self.post(self.login_url, data)
        if not self.login_response:
            logger.info("用户名密码错误")
            self.messages.append("用户名密码错误")
            raise StopIteration("调用链已在 method1 中断")
        self.profile = self.login_response.get('data', {}).get('profile', {})
        token = self.login_response.get('data', {}).get('token', {})
        self.sw_id = self.profile.get("swid", "")
        self.access_token = token.get("accessToken", "")
        self.first_name = self.profile.get("firstName", "")
        self.last_name = self.profile.get("lastName", "")
        self.contact_info = {
            "firstName": self.profile.get("firstName"),
            "lastName": self.profile.get("lastName"),
            "firstNamePinyin": "",
            "lastNamePinyin": "",
            "idCardType": "ID_CARD",
            "idCard": "321025197912160221",
            "contactWay": "PHONE",
            "countryCode": "86",
            "countryCodeText": "+86 中国内地",
            "mobilePhone": self.profile.get("mobile"),
            "fullName": ""
        }
        logger.info(f"登录完毕 {self.username}, {self.password}")
        return self

    def syn_token(self):
        data = {"swid": self.sw_id, "accessToken": self.access_token}
        self.sync_token_response = self.post(self.sync_url, data=data)
        logger.info(f"完成同步token {self.username}, {self.password}")
        return self

    def get_eligible(self):
        self.default_header = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
            'Authorization': "bearer {}".format(self.auth_token),
            'Connection': 'keep-alive',
            'Content-Type': 'application/json',
            'Origin': 'https://central.shanghaidisneyresort.com',
            'Referer': 'https://central.shanghaidisneyresort.com/commerce/epep/shdr-early-park-entry-pass/confirm',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                          'Chrome/91.0.4472.114 Mobile '
                          'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
            'X-Conversation-Id': self.uuid,
            'X-Correlation-Id': 'dc7cc9ae-a6ee-465d-a5a8-08fbec244457',
            'X-Guest-Token': self.access_token,
            'X-Language': 'zh',
            'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
            'X-Store-Id': 'shdr_mobile',
            'X-Sw-Id': self.sw_id,
            'X-View-Type': 'mobile'
        }
        data = {"param": {"id": "shdr-early-park-entry-pass"}}
        self.eligible_response = self.post(self.eligible_url, data)
        response_body = self.eligible_response.get('data', {})
        eligible = response_body.get('eligible', [])
        not_eligible = response_body.get('nonEligible', [])
        self.quantity = len(eligible)
        logger.info(f"有效绑定数量[{self.quantity}], 过期绑定数量[{len(not_eligible)}]")
        if len(eligible) == 0:
            self.messages.append(f"有效绑定数量[{self.quantity}], 过期绑定数量[{len(not_eligible)}]")
            raise StopIteration("检测早想绑定中断")
        details = eligible[0]
        self.target_date_en = details.get("expireEndTime", "")
        self.target_date_cn = details.get("expireTime", "")
        self.start_time = details.get("startDateTime", "")
        self.vids = [x['visualId'] for x in eligible]
        return self

    def get_morning_price(self):
        url = f"https://central.shanghaidisneyresort.com/epep/api/price-grid/shdr-early-park-entry-pass/{self.target_date_en}"
        self.morning_price_response = self.get(url)
        if not self.morning_price_response:
            self.messages.append("获取价格失败")
            raise StopIteration("调用链已在 get_morning_price 中断")
        prices = self.morning_price_response.get('data', [])
        if len(prices) > 0:
            self.start_time = prices[0].get("startDateTime", "")
            self.unit_price = prices[0].get("unitPrice", 0)
            self.total_price = str(int(self.unit_price) * self.quantity)
            logger.info(f"获取价格成功, 单价[{self.unit_price}], 总价[{self.total_price}], 开始时间[{self.start_time}]")
        else:
            logger.info("获取价格失败")
            self.messages.append("获取价格失败")
            raise StopIteration("调用链已在 get_morning_price 中断")
        return self

    def pay_morning_order(self):
        logger.info("开始支付早享卡")
        data = {"contactForm": {"countrycode": "CN", "phone": "8613127778188", "governmentId": self.card,
                                "items": {"quantity": self.quantity, "productType": "shdr-early-park-entry-pass",
                                          "eventDate": self.target_date_en, "text": "早享卡",
                                          "pricing": {"subtotal": self.unit_price,
                                                      "currency": "CNY",
                                                      "total": self.total_price,
                                                      "tax": "0",
                                                      "taxIncluded": False,
                                                      "startDateTime": self.start_time,
                                                      "sku": "SHCP01OLPKVC1901P",
                                                      "capacityManaged": True,
                                                      "quantity": 1
                                                      }
                                          },
                                "categoryId": "epep",
                                "id": "shdr-early-park-entry-pass",
                                "total": self.total_price,
                                "selectedDay": self.target_date_cn,
                                "visualIdList": self.vids,
                                "firstName": self.first_name,
                                "lastName": self.last_name,
                                "profileId": self.sw_id,
                                "guestToken": self.access_token,
                                "profilePhoneCode": "86",
                                "countryCode": "CN",
                                "needsShowTandCInPayment": False}}
        self.morning_confirm_response = self.post(self.morning_confirm, data, debug=True)
        logger.info("支付返回结果------------->")
        logger.info(self.morning_confirm_response)
        logger.info("<-------------支付返回结果")
        if not self.morning_confirm_response:
            logging.info("支付失败")
            self.messages.append("支付失败")
            raise StopIteration("调用链已在 pay_morning_order 中断")
        data = self.morning_confirm_response.get('data', {})
        error_message = data.get('message', {}).get('errorMessage', "")
        if error_message:
            self.messages.append(error_message)
            logger.info("调用链已在 pay_morning_order 中断")
            logger.info(error_message)
            raise StopIteration("调用链已在 pay_morning_order 中断")
        self.payment_id = data.get('paymentSessionId', '')
        return self

    def check_morning_date(self):
        self.check_morning_date_response = self.get(self.check_morning_date_url)
        if not self.check_morning_date_response:
            logger.info("检查早享卡日期失败")
            self.messages.append("检查早享卡日期失败")
            raise StopIteration("调用链已在 check_morning_date 中断")
        date = self.check_morning_date_response.get('data', {}).get('data', [])
        avalible_date = [x['date'] for x in date if not x.get('soldOut')]
        logger.info(f"可购买日期{avalible_date}")
        if self.target_date_en in avalible_date:
            logger.info("可以购买，等待创建表单")
            return self
        logger.info("不可购买，等待5秒")
        sleep(5)
        return self.check_morning_date()

    def pay_transactiona(self):
        logger.info("生成支付订单")
        url = f"https://apim.shanghaidisneyresort.com/payment-middleware-service/session/{self.payment_id}/transactions"
        data = {"clientIp": "10.0.2.15", "deviceInfo": "Android|Android 12|22041216C", "payChannel": "APP",
                "payOption": "ALIPAY", "region": "cn"}
        headers = {
            "Authorization": "BEARER {}".format(self.access_token),
            "App-Version": "11.5.0",
            "Host": "apim.shanghaidisneyresort.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Accept-Language": "zh-cn",
            "Content-Type": "application/json",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; 22041216C Build/V417IR)",
            "X-Conversation-Id": self.payment_id,
        }
        self.morning_transaction_response = self.post(url, data, headers, debug=True)
        logger.info("订单结果------------->")
        logger.info(self.morning_transaction_response)
        logger.info("<-------------订单结果")
        if not self.morning_transaction_response:
            self.messages.append("获取订单失败")
            raise StopIteration("调用链已在 pay_transactiona 中断")
        self.order = self.morning_transaction_response.get('params', {}).get('response_text', '')
        return self

    def check_one_day(self):
        data = {"piGroup": ["shdr-theme-park-tickets_2017-04-20_1_A_0_0_RF_AF_SOF_41",
                            "shdr-theme-park-tickets_2017-04-20_1_C_0_0_RF_AF_SOF_41",
                            "shdr-theme-park-tickets_2017-04-20_1_S_0_0_RF_AF_SOF_41",
                            "shdr-theme-park-tickets_2021-10-08_1_D_0_0_RF_AF_SOF_41"], "type": None, "sessionId": ""}
        self.check_one_day_response = self.post(self.check_one_day_url, data=data)
        if not self.check_one_day_response:
            self.messages.append("检查一日票日期失败")
            raise StopIteration("调用链已在 check_one_day 中断")
        date = self.check_one_day_response.get("date", {}).get("calendar", {}).get("data", [])
        avalibles = [x['date'] for x in date if x.get('available')]
        logger.info(f"可购买日期{avalibles}")
        if self.one_day in avalibles:
            logger.info("可以购买,等待创建表单")
            return self
        logger.info("不可购买，等待5秒")
        sleep(5)
        return self.check_one_day()

    def get_one_day_mock(self):
        if self.one_day_count <= 0:
            logger.info(f"订购数量必须大于0, 当前数量{self.one_day_count}")
            self.messages.append("订购数量必须大于0")
            raise StopIteration("调用链已在 get_one_day_mock 中断")
        data = {"productGroupId": "ticket-group-shdr-theme-park-tickets-one-day-ticket-hybrid",
                "productTypeId": "shdr-theme-park-tickets", "productCategoryId": "ThemePark",
                "startDate": self.one_day,
                "detail": [{"sku": "SHTP01OLRDQO", "quantity": self.one_day_count}],
                "source": "main_cart", "goodsTag": "",
                "swid": self.sw_id}
        self.get_one_day_mock_response = self.post(self.mock_url, data=data)
        if not self.get_one_day_mock_response:
            logger.info("创建一日票表单失败")
            self.messages.append("创建一日票表单失败")
            raise StopIteration("调用链已在 get_one_day_mock 中断")
        logger.info("创建表单完成，等待创建订单")
        return self

    def get_one_day_order(self):
        logger.info("开始创建一日票订单")
        if not self.get_one_day_mock_response:
            logger.info("未获取预定表单信息")
            self.messages.append("未获取预定表单信息")
            raise StopIteration("调用链已在 get_one_day_order 中断")
        payload = self.get_one_day_mock_response
        payload['contactInfo'] = self.contact_info
        payload['bundles'] = []
        payload['realNameInfos'] = []
        self.default_header['X-Guest-Token'] = self.access_token
        self.default_header['Authorization'] = "bearer {}".format(self.auth_token)
        self.default_header['User-Agent'] = 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh'
        self.default_header['X-Sw-Id'] = self.sw_id
        self.one_day_order_response = self.post(self.one_day_order_url, data=payload, debug=True)
        if not self.one_day_order_response:
            self.messages.append("创建订单失败")
            raise StopIteration("调用链已在 get_one_day_order 中断")
        self.payment_id = self.one_day_order_response.get('data', {}).get('paymentSessionId', '')
        logger.info("完成订单，等待获取支付链接")
        return self

    def get_token(self):
        self.default_header['X-Guest-Token'] = self.access_token
        self.default_header['X-Native-Token'] = self.access_token
        self.default_header['X-Correlation-Id'] = "b4abd3e9-5267-4e55-bfa0-c15dd0631ed6"
        self.default_header['Referer'] = "https://central.shanghaidisneyresort.com/commerce/order/checkout?source=ticketing-v2"
        self.default_header['X-Sw-Id'] = self.sw_id

        data = {"countryCode": "CN", "email": self.contact_info.get("email"),
                "firstName": self.contact_info.get("firstName"),
                "guestToken": self.access_token, "hasFirstName": True, "hasLastName": True,
                "isRecommendToggleOn": True, "isoCountryCode2": "CN", "lastName": self.contact_info.get("lastNAME"),
                "mobileAreaNum": "86",
                "mobileCountryISO2": "CN", "phoneNumber": self.contact_info.get("phoneNumber"),
                "profileId": self.sw_id, "profilePhoneCode": "86",
                "profilePhoneNumber": self.contact_info.get("phoneNumber")}
        self.get_token_response = self.post(self.token_url, data=data)
        if not self.get_token_response:
            self.messages.append("获取token失败")
            raise StopIteration("调用链已在 get_token 中断")
        self.auth_token = self.get_token_response.get("data", {}).get("Authorization")
        return self

    def get_order_info(self):
        self.default_header['X-Guest-Token'] = self.access_token
        self.default_header['X-Native-Token'] = self.access_token
        self.default_header['X-Correlation-Id'] = "b4abd3e9-5267-4e55-bfa0-c15dd0631ed6"
        self.default_header['X-Guest-Token'] = self.access_token
        self.default_header['Authorization'] = "bearer {}".format(self.auth_token)
        self.default_header[
            'User-Agent'] = 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh'
        self.default_header['X-Sw-Id'] = self.sw_id
        self.default_header[
            'Referer'] = "https://central.shanghaidisneyresort.com/commerce/order/checkout?source=ticketing-v2"
        self.default_header['X-Sw-Id'] = self.sw_id
        data = {
            'page': {
                'currentPage': 1,
                'skip': 0,
                'take': 20,
            },
            'w': {
                'include': {
                    'storeId': [
                        'shdr',
                        'shdr_wechat',
                        'shdr_mobile',
                        'shdr_partnership',
                        'shdr_isr',
                        'shdr_drc',
                        'shdr_club33',
                        'shdr_vrc',
                        'shdr_kqwh',
                        'shdr_slpu',
                        'shdr_msp',
                        'shdr_shgnb',
                        'shdr_ssh',
                        'shdr_phsh',
                        'shdr_isr',
                        'shdr_shagh',
                        'shdr_tsrsj',
                        'shdr_pce',
                        'shdr_icexpo',
                        'shdr_shaws',
                        'shdr_khpu',
                        'shdr_rsph',
                        'shdr_jhsh',
                    ],
                },
                'excludePending': [
                    'shdr_drc',
                    'shdr_club33',
                    'shdr_vrc',
                ],
            },
        }
        self.get_order_info_response = self.post(self.order_url, data=data, debug=True)
        orders = self.get_order_info_response.get("data", {}).get("orders", {}).get("list", [])
        return orders[:3]

    def link_order(self, morning_number):
        logger.info("开始确认关联早享卡是否有效")
        self.morning_card = morning_number
        self.default_header['X-Guest-Token'] = self.access_token
        self.default_header['Authorization'] = "bearer {}".format(self.auth_token)
        self.default_header[
            'User-Agent'] = 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh'
        self.default_header['X-Sw-Id'] = self.sw_id
        json_data = {
            'param': {
                'orderNumber': morning_number,
                'countryCode': 'CN',
                'email': self.profile.get("email"),
                'firstName': self.profile.get("firstName"),
                'guestToken': self.access_token,
                'hasFirstName': False,
                'hasLastName': False,
                'isRecommendToggleOn': True,
                'isoCountryCode2': 'CN',
                'lastName': self.last_name,
                'mobileAreaNum': '86',
                'mobileCountryISO2': 'CN',
                'phoneNumber': f'86{self.profile.get("mobile")}',
                'profileId': self.profile.get('swid'),
                'profilePhoneCode': '86',
                'profilePhoneNumber': self.profile.get("mobile"),
                'maskFirstName': True,
            },
        }
        self.find_link_order_response = self.post(self.link_order_url, json_data)
        if not self.find_link_order_response:
            self.messages.append("关联订单失败")
            raise StopIteration("调用链已在 link_order 中断")
        code = self.find_link_order_response.get("data", {}).get("code", "")
        if code != 200:
            self.messages.append("关联码错误")
            raise StopIteration("调用链已在 link_order 中断")
        logger.info(f"账号[{self.username}]和[{morning_number}]可以关联")
        return self



    def confirm_link_order(self):
        logger.info("开始关联早享卡")
        if not self.morning_card:
            self.messages.append("早享卡号码为空")
            raise StopIteration("调用链已在 confirm_link_order 中断")

        self.default_header['X-Guest-Token'] = self.access_token
        self.default_header['Authorization'] = "bearer {}".format(self.auth_token)
        self.default_header[
            'User-Agent'] = 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh'
        self.default_header['X-Sw-Id'] = self.sw_id
        json_data ={"param":{"id":f"{self.morning_card}","type":"order"}}
        self.confirm_link_order_response = self.post(self.confirm_order_url, json_data)
        if not self.confirm_link_order_response:
            self.messages.append("确认关联订单失败")
            raise StopIteration("调用链已在 confirm_link_order 中断")
        code = self.confirm_link_order_response.get("data", {}).get("code", "")
        if code != 200:
            self.messages.append("关联码错误")
            raise StopIteration("调用链已在 confirm_link_order 中断")
        logger.info(f"账号[{self.username}]和[{self.morning_card}]关联成功")
        return self
