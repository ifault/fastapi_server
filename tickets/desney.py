import json
import uuid
import warnings
from time import sleep
from typing import Dict

import requests
from urllib3.exceptions import InsecureRequestWarning

warnings.filterwarnings("ignore", category=InsecureRequestWarning)


class Desney:
    def __init__(self, username, password):
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
        self.card = "321025197912160221"
        self.login_url = "https://www.shanghaidisneyresort.com/dprofile/api/v7/guests/login"
        self.sync_url = "https://www.shanghaidisneyresort.com/dprofile/api/login/phpsync"
        self.eligible_url = "https://central.shanghaidisneyresort.com/epep/api/party"
        self.morning_confirm = "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/comfirm"
        self.check_morning_date_url = "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/calender"
        self.login_response = None
        self.sync_token_response = None
        self.eligible_response = None
        self.morning_price_response = None
        self.morning_confirm_response = None
        self.check_morning_date_response = None
        self.morning_transaction_response = None

    def post(self, url, data, header=None, debug=False):
        self.load_cookies()
        post_header = header if header else self.default_header
        response = self.session.post(url, json=data, headers=post_header, verify=False)
        if debug:
            print(response.json())
        if response.status_code in self.status:
            self.store_cookies()
            return response.json()
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
            with open(f"cookies/{self.hash}.json", "w") as f:
                json.dump(self.session.cookies.get_dict(), f)
        except Exception as e:
            print(e)

    def load_cookies(self):
        try:
            with open(f"cookies/{self.hash}.json", "r") as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
        except Exception as e:
            print(e)

    def login(self):
        data = {"pinPass": False, "loginType": 1, "loginName": self.username, "mobileAreaNum": "86",
                "mobileCountryISO2": "CN", "functionType": "GUEST_LOGIN_MOBILE",
                "password": self.password,
                "passwordEncrypted": False, "langPref": "zh", "sourceId": "DPRD-SHDR.MOBILE.ANDROID-PROD",
                "sessionid": "undefined"}
        self.login_response = self.post(self.login_url, data)
        if not self.login_response:
            self.messages.append("用户名密码错误")
            raise StopIteration("调用链已在 method1 中断")
        profile = self.login_response.get('data', {}).get('profile', {})
        token = self.login_response.get('data', {}).get('token', {})
        self.sw_id = profile.get("swid", "")
        self.access_token = token.get("accessToken", "")
        self.first_name = profile.get("firstName", "")
        self.last_name = profile.get("lastName", "")
        return self

    def syn_token(self):
        data = {"swid": self.sw_id, "accessToken": self.access_token}
        self.sync_token_response = self.post(self.sync_url, data=data)
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
        else:
            self.messages.append("获取价格失败")
            raise StopIteration("调用链已在 get_morning_price 中断")
        return self

    def pay_morning_order(self):
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
        if not self.morning_confirm_response:
            self.messages.append("支付失败")
            raise StopIteration("调用链已在 pay_morning_order 中断")
        data = self.morning_confirm_response.get('data', {})
        error_message = data.get('message', {}).get('errorMessage', "")
        if not error_message:
            self.messages.append(error_message)
            raise StopIteration("调用链已在 pay_morning_order 中断")
        self.payment_id = data.get('paymentSessionId', '')
        return self

    def check_morning_date(self):
        self.check_morning_date_response = self.get(self.check_morning_date_url)
        if not self.check_morning_date_response:
            self.messages.append("检查早享卡日期失败")
            raise StopIteration("调用链已在 check_morning_date 中断")
        date = self.check_morning_date_response.get('data', {}).get('data', [])
        avalible_date = [x['date'] for x in date if not x.get('soldOut')]
        if self.target_date_en in avalible_date:
            return self
        sleep(5)
        self.check_morning_date()

    def pay_transactiona(self):
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
        if not self.morning_transaction_response:
            self.messages.append("获取订单失败")
            raise StopIteration("调用链已在 pay_transactiona 中断")
        self.order = self.morning_transaction_response.get('params', {}).get('response_text', {})
        return self
