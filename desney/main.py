import json
import uuid
from time import sleep

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def convert(headers):
    st1 = headers.split('\n')
    headers_dict = {}
    for text1 in st1:
        s1 = text1.replace(': ', '#$', 1)
        st2 = s1.split('#$')
        headers_dict[st2[0]] = st2[1]
    return headers_dict


class Ticket():
    def __init__(self, id):
        self.default_headers = {
            "X-Store-Id": 'shdr_mobile',
            "X-View-Type": 'mobile',
            "X-Source-Type": 'main_cart',
            "X-Language": "zh",
            "x-Conversation-Id": id,
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
        self.mock_url = "https://central.shanghaidisneyresort.com/ticketing/api/v1/cart/tickets/mock"
        self.create_url = "https://central.shanghaidisneyresort.com/order/api/order/create"
        self.token_url = "https://central.shanghaidisneyresort.com/order/api/auth/token"
        self.token_auth = "https://central.shanghaidisneyresort.com/ticketing/api/v1/user/getTokenAuth/nmMQLRTozrdFPmieogQuAD"
        self.login_url = "https://www.shanghaidisneyresort.com/dprofile/api/v7/guests/login"
        self.one_day_url = "https://central.shanghaidisneyresort.com/ticketing/api/v1/tickets/book/information/shdr-theme-park-tickets?storeId=shdr_mobile"
        self.php_sync_url = "https://www.shanghaidisneyresort.com/dprofile/api/login/phpsync"
        self.cur_auth = "https://authorization.shanghaidisneyresort.com/curoauth/v1/token"
        self.session = requests.Session()
        self.uuid = id
        self.access_token = ""
        self.sw_id = ""
        self.bearer_token = ""
        self.order_payload = {}
        self.contact_info = {}

    def store_cookies(self):
        try:
            with open("cookies.json", "w") as f:
                json.dump(self.session.cookies.get_dict(), f)
        except Exception as e:
            print(e)

    def load_cookies(self):
        try:
            with open("cookies.json", "r") as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
        except Exception as e:
            print(e)

    def check_one_day(self, target_date):
        self.load_cookies()
        data = {"piGroup": ["shdr-theme-park-tickets_2017-04-20_1_A_0_0_RF_AF_SOF_41",
                            "shdr-theme-park-tickets_2017-04-20_1_C_0_0_RF_AF_SOF_41",
                            "shdr-theme-park-tickets_2017-04-20_1_S_0_0_RF_AF_SOF_41",
                            "shdr-theme-park-tickets_2021-10-08_1_D_0_0_RF_AF_SOF_41"], "type": None, "sessionId": ""}
        response = self.session.post(self.one_day_url, json=data, headers=self.default_headers, verify=False)
        if response.status_code == 200:
            self.session.cookies.set("Conversation_UUID", self.uuid)
            self.store_cookies()
            res = response.json()
            array = res.get("date", {}).get("calendar", {}).get("data", {})
            for item in array:
                if item.get("date") == target_date and item.get("available"):
                    return True
            return False

        else:
            print(response.status_code)
            return False

    def login(self, username, password):
        headers = self.default_headers
        headers[
            'User-Agent'] = 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36'
        headers['Origin'] = 'https://www.shanghaidisneyresort.com'
        headers['Referer'] = 'https://www.shanghaidisneyresort.com/dprofile/zh/phone/password/login'
        data = {"pinPass": False, "loginType": 1, "loginName": username, "mobileAreaNum": "86",
                "mobileCountryISO2": "CN", "functionType": "GUEST_LOGIN_MOBILE",
                "password": password,
                "passwordEncrypted": False, "langPref": "zh", "sourceId": "DPRD-SHDR.MOBILE.ANDROID-PROD",
                "sessionid": "undefined"}
        response = self.session.post(self.login_url, json=data, headers=self.default_headers, verify=False)
        if response.status_code == 200:
            self.store_cookies()
            res = response.json()
            self.access_token = res.get("data", {}).get("token", {}).get("accessToken")
            self.sw_id = res.get("data", {}).get("token", {}).get("swid")
            profile = res.get("data", {}).get("profile")
            self.contact_info = {
                "firstName": profile.get("firstName"),
                "lastName": profile.get("lastName"),
                "firstNamePinyin": "",
                "lastNamePinyin": "",
                "idCardType": "ID_CARD",
                "idCard": "321025197912160221",
                "contactWay": "PHONE",
                "countryCode": "86",
                "countryCodeText": "+86 中国内地",
                "mobilePhone": profile.get("mobile"),
                "fullName": ""
            }
        else:
            print(response.json())

    def php_sync(self):
        data = {"swid": self.sw_id, "accessToken": self.access_token}
        response = self.session.post(self.php_sync_url, headers=self.default_headers, verify=False, json=data)
        print(response.json())

    def get_mock(self, date, count=1):
        self.load_cookies()
        data = {"productGroupId": "ticket-group-shdr-theme-park-tickets-one-day-ticket-hybrid",
                "productTypeId": "shdr-theme-park-tickets", "productCategoryId": "ThemePark",
                "startDate": date,
                "detail": [{"sku": "SHTP01OLRDQO", "quantity": count}],
                "source": "main_cart", "goodsTag": "",
                "swid": self.sw_id}
        response = self.session.post(self.mock_url, headers=self.default_headers, verify=False, json=data)
        if response.status_code == 200:
            self.store_cookies()
            self.order_payload = response.json()
        else:
            print(response.status_code)

    def create_order(self):
        self.load_cookies()
        data = self.order_payload
        data['contactInfo'] = self.contact_info
        data['bundles'] = []
        data['realNameInfos'] = []
        headers = self.default_headers
        bearer_token = self.bearer_token
        headers['X-Guest-Token'] = self.access_token
        headers['Authorization'] = "bearer {}".format(bearer_token)
        headers[
            'User-Agent'] = 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Mobile Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh'
        headers['X-Sw-Id'] = self.sw_id
        response = self.session.post(self.create_url, headers=headers, verify=False,
                                     json=data)
        if response.status_code in (200, 201):
            self.store_cookies()
            res = response.json()
            return True, {"orderNumber": res.get("data", {}).get("orderNumber"),
                          "totalPaymentAmount": res.get("data", {}).get("totalPaymentAmount")}
        else:
            return False, {}

    def get_token(self):
        self.load_cookies()
        headers = self.default_headers
        headers['X-Guest-Token'] = self.access_token
        headers['X-Native-Token'] = self.access_token
        headers['X-Correlation-Id'] = "b4abd3e9-5267-4e55-bfa0-c15dd0631ed6"
        headers['Referer'] = "https://central.shanghaidisneyresort.com/commerce/order/checkout?source=ticketing-v2"
        headers['X-Sw-Id'] = self.sw_id

        data = {"countryCode": "CN", "email": self.contact_info.get("email"),
                "firstName": self.contact_info.get("firstName"),
                "guestToken": self.access_token, "hasFirstName": True, "hasLastName": True,
                "isRecommendToggleOn": True, "isoCountryCode2": "CN", "lastName": self.contact_info.get("lastNAME"),
                "mobileAreaNum": "86",
                "mobileCountryISO2": "CN", "phoneNumber": self.contact_info.get("phoneNumber"),
                "profileId": self.sw_id, "profilePhoneCode": "86",
                "profilePhoneNumber": self.contact_info.get("phoneNumber")}
        response = self.session.post(self.token_url, headers=headers, verify=False, json=data)
        if response.status_code == 200 or response.status_code == 201:
            self.store_cookies()
            self.bearer_token = response.json().get("data", {}).get("Authorization")
            print(self.bearer_token)
        else:
            print(response.text)

    def get_auth(self):
        headers = {
            "App-Version": "11.5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept-Language": "zh-cn",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 12; DCO-AL00 Build/V417IR)",
            "Host": "authorization.shanghaidisneyresort.com",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "Content-Length": "82",
        }
        form = {
            "grant_type": "assertion",
            "assertion_type": "public",
            'client_id': 'DPRD-SHDR.MOBILE.ANDROID-PROD',
        }
        response = self.session.post(self.cur_auth, headers=headers, verify=False, data=form)
        res = response.json()
        self.access_token = res.get("access_token")
        self.refresh_token = res.get("refresh_token")

    def get_commerce_token(self):
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/order',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Correlation-Id': 'f72f3608-3b5f-42c6-9451-5ae530a2e00f',
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Platform': 'Hybrid',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Source-Type': 'main_cart',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {"countryCode": "CN", "email": self.contact_info.get("email"),
                "firstName": self.contact_info.get("firstName"),
                "guestToken": self.access_token, "hasFirstName": True, "hasLastName": True,
                "isRecommendToggleOn": True, "isoCountryCode2": "CN", "lastName": self.contact_info.get("lastNAME"),
                "mobileAreaNum": "86",
                "mobileCountryISO2": "CN", "phoneNumber": self.contact_info.get("phoneNumber"),
                "profileId": self.sw_id, "profilePhoneCode": "86",
                "profilePhoneNumber": self.contact_info.get("phoneNumber")}
        response = self.session.post("https://central.shanghaidisneyresort.com/order/api/auth/token", headers=headers,
                                     verify=False, data=json.dumps(data))
        res = response.json()
        token = res.get("data", {}).get("Authorization")
        return token

    def get_commerce_orders(self):
        token = self.get_commerce_token()
        print(token)
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': f'bearer {token}',
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/order',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Platform': 'Hybrid',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Source-Type': 'main_cart',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {"page": {"currentPage": 1, "skip": 0, "take": 20}, "w": {"include": {
            "storeId": ["shdr", "shdr_wechat", "shdr_mobile", "shdr_partnership", "shdr_isr", "shdr_drc", "shdr_club33",
                        "shdr_vrc", "shdr_kqwh", "shdr_slpu", "shdr_msp", "shdr_shgnb", "shdr_ssh", "shdr_phsh",
                        "shdr_isr",
                        "shdr_shagh", "shdr_tsrsj", "shdr_pce", "shdr_icexpo", "shdr_shaws", "shdr_khpu", "shdr_rsph",
                        "shdr_jhsh"]}, "excludePending": ["shdr_drc", "shdr_club33", "shdr_vrc"]}}
        data = {"page": {"currentPage": 2, "skip": 40, "take": 20, "total": 4, "totalPage": 1}, "w": {"include": {
            "storeId": ["shdr", "shdr_wechat", "shdr_mobile", "shdr_partnership", "shdr_isr", "shdr_drc", "shdr_club33",
                        "shdr_vrc", "shdr_kqwh", "shdr_slpu", "shdr_msp", "shdr_shgnb", "shdr_ssh", "shdr_phsh",
                        "shdr_isr", "shdr_shagh", "shdr_tsrsj", "shdr_pce", "shdr_icexpo", "shdr_shaws", "shdr_khpu",
                        "shdr_rsph", "shdr_jhsh"]}, "excludePending": ["shdr_drc", "shdr_club33", "shdr_vrc"]}}

        response = self.session.post("https://central.shanghaidisneyresort.com/order/api/order", headers=headers,
                                     verify=False, data=json.dumps(data))
        res = response.json()
        print(res)

    def discard_order(self, order_number):
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
                   'Connection': 'keep-alive',
                   'Content-Length': '38',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/order/result?orderNumber=SC010931690427322368&from=hybridOrderHistory',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Correlation-Id': 'dffc1134-7656-424a-9066-0cd454dded44',
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Platform': 'Hybrid',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Source-Type': 'main_cart',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {"orderNumber": order_number}
        response = self.session.post("https://central.shanghaidisneyresort.com/order/api/order/discard",
                                     headers=headers,
                                     verify=False, data=json.dumps(data))
        if response.status_code in (200, 201):
            return True
        return False

    def link_card(self, gla):
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
                   'Connection': 'keep-alive',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/epep/shdr-early-park-entry-pass/linkTicket',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Correlation-Id': '545c411a-d2fb-42a2-8387-939d252a2390',
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {"param": {"orderNumber": gla,
                          "countryCode": "CN", "email": self.contact_info.get("email"),
                          "firstName": self.contact_info.get("firstName"),
                          "guestToken": self.access_token, "hasFirstName": True, "hasLastName": True,
                          "isRecommendToggleOn": True, "isoCountryCode2": "CN",
                          "lastName": self.contact_info.get("lastNAME"),
                          "mobileAreaNum": "86",
                          "mobileCountryISO2": "CN", "phoneNumber": self.contact_info.get("phoneNumber"),
                          "profileId": self.sw_id, "profilePhoneCode": "86",
                          "profilePhoneNumber": self.contact_info.get("phoneNumber")}}
        response = self.session.post("https://central.shanghaidisneyresort.com/epep/api/linkOrderFind",
                                     headers=headers,
                                     verify=False, data=json.dumps(data))
        if response.status_code in (200, 201):
            res = response.json()
            detail = res.get("data", {}).get("ticketsList", [])[0]
            return True, detail['id'], detail['expireTime']
        return False, {}

    def date_to_str(self, date_str):
        from datetime import datetime, timedelta
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        time_obj = datetime.combine(date_obj, datetime.min.time())
        time_obj += timedelta(hours=5)  # 设置时间为5点
        time_obj = time_obj.replace(microsecond=0)
        timezone_offset = timedelta(hours=8)
        aware_datetime_obj = time_obj.replace(tzinfo=timezone_offset)
        formatted_datetime_str = aware_datetime_obj.isoformat()
        return formatted_datetime_str

    def confirm_morning_order(self, vids, id_card, start_time, en_date, cn_date, price, total_price):
        result = self.get_morning_target_day_price(target_date)
        if not result:
            return None

        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
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
                   'X-View-Type': 'mobile'}
        data = {"contactForm": {"countrycode": "CN", "phone": "8613127778188", "governmentId": id_card,
                                "items": {"quantity": len(vids), "productType": "shdr-early-park-entry-pass",
                                          "eventDate":en_date, "text": "早享卡",
                                          "pricing": {"subtotal": price,
                                                      "currency": "CNY",
                                                      "total": total_price,
                                                      "tax": "0",
                                                      "taxIncluded": False,
                                                      "startDateTime": start_time,
                                                      "sku": "SHCP01OLPKVC1901P",
                                                      "capacityManaged": True,
                                                      "quantity": 1
                                                      }
                                          },
                                "categoryId": "epep",
                                "id": "shdr-early-park-entry-pass",
                                "total": total_price,
                                "selectedDay": cn_date,
                                "visualIdList": vids,
                                "firstName": self.contact_info['firstName'],
                                "lastName": self.contact_info['lastName'],
                                "profileId": self.sw_id,
                                "guestToken": self.access_token,
                                "profilePhoneCode": "86",
                                "countryCode": "CN",
                                "needsShowTandCInPayment": False}}
        response = self.session.post(
            "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/comfirm",
            headers=headers,
            verify=False, data=json.dumps(data))
        print(response.json())
        if response.status_code in (200, 201):
            res = response.json()
            status = int(res.get("data", {}).get("code", 0))
            if status > 201:
                error_msg = res.get("data", {}).get("message",{}).get("errorMessage")
                error_type = res.get("data", {}).get("message",{}).get("errorType")
                error_code = res.get("data", {}).get("message",{}).get("errorCode")
                print(error_code, error_type, error_msg)
                return False
            return True
        if response.status_code == 400:
            res = response.json()
            error_msg = res.get("data", {}).get("message",{}).get("errorMessage")
            print(error_msg)
            return False
        return False

    def check_monirng_calander(self):
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
                   'Connection': 'keep-alive',
                   'Content-Length': '38',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/order/result?orderNumber=SC010931690427322368&from=hybridOrderHistory',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Correlation-Id': 'dffc1134-7656-424a-9066-0cd454dded44',
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Platform': 'Hybrid',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Source-Type': 'main_cart',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {}
        response = self.session.get(
            "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/calender",
            headers=headers,
            verify=False, data=json.dumps(data))
        print(response.json())
        if response.status_code in (200, 201):
            res = response.json()
            all_date = res.get("data", {}).get("data", [])
            valid_date = [x['date'] for x in all_date if x['soldOut'] is False]
            return True, valid_date
        return False, []

    def get_morning_target_day_price(self, target):
        url = f"https://central.shanghaidisneyresort.com/epep/api/price-grid/shdr-early-park-entry-pass/{target}"
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
                   'Connection': 'keep-alive',
                   'Content-Length': '38',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/order/result?orderNumber=SC010931690427322368&from=hybridOrderHistory',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Correlation-Id': 'dffc1134-7656-424a-9066-0cd454dded44',
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Platform': 'Hybrid',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Source-Type': 'main_cart',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {}
        response = self.session.get(
            url,
            headers=headers,
            verify=False, data=json.dumps(data))
        print(response.json())
        if response.status_code in (200, 201):
            res = response.json()
            data = res.get("data", [])[0]
            price = data['price']
            sku = data['sku']
            start_time = data['startDateTime']
            total_price = data['subtotal']
            return {"price": price, "sku": sku, "startDateTime": start_time, "totalPrice": total_price}
        return None

    def check_eligible_morning_cards(self):
        url = "https://central.shanghaidisneyresort.com/epep/api/party"
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
                   'Connection': 'keep-alive',
                   'Content-Length': '38',
                   'Content-Type': 'application/json',
                   'Origin': 'https://central.shanghaidisneyresort.com',
                   'Referer': 'https://central.shanghaidisneyresort.com/commerce/order/result?orderNumber=SC010931690427322368&from=hybridOrderHistory',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Linux; Android 12; DCO-AL00 Build/V417IR; wv) '
                                 'AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 '
                                 'Chrome/91.0.4472.114 Mobile '
                                 'Safari/537.36,DISNEY_MOBILE_ANDROID/11500,language/zh',
                   'X-Conversation-Id': self.uuid,
                   'X-Correlation-Id': 'dffc1134-7656-424a-9066-0cd454dded44',
                   'X-Guest-Token': self.access_token,
                   'X-Language': 'zh',
                   'X-Platform': 'Hybrid',
                   'X-Requested-With': 'com.disney.shanghaidisneyland_goo',
                   'X-Source-Type': 'main_cart',
                   'X-Store-Id': 'shdr_mobile',
                   'X-Sw-Id': self.sw_id,
                   'X-View-Type': 'mobile'}
        data = {"param": {"id": "shdr-early-park-entry-pass"}}
        response = self.session.get(
            "https://central.shanghaidisneyresort.com/epep/api/shdr-early-park-entry-pass/calender",
            headers=headers,
            verify=False, data=json.dumps(data))
        print(response.json())
        if response.status_code in (200, 201):
            res = response.json()
            data = res.get("data", []).get("eligible", [])
        return None

    def date_str_format_cn(self, date_str):
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y年%m月%d日")

    def date_str_format_en(self, date_str):
        from datetime import datetime
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%Y-%m-%d")

    def get_current_eligible(self):
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh,en-US;q=0.9,en;q=0.8',
                   'Authorization': "bearer {}".format(self.bearer_token),
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
                   'X-View-Type': 'mobile'}
        data= {"param":{"id":"shdr-early-park-entry-pass"}}
        response = self.session.post(
            "https://central.shanghaidisneyresort.com/epep/api/party",
            headers=headers,
            verify=False, data=json.dumps(data))
        if response.status_code in (200, 201):
            res = response.json()
            array = res.get("data", {}).get("eligible", [])
            vids = [x['visualId'] for x in array]
            target_date_en = array[0]['expireEndTime']
            target_date_cn = array[0]['expireTime']
            start_time = array[0]['startDateTime']
            return {"vids": vids, "target_date_en": target_date_en, "target_date_cn": target_date_cn, "start_time": start_time}
        return None

if __name__ == '__main__':
    target_date = "2024-04-21"
    conversation = str(uuid.uuid4())
    ticket = Ticket(conversation)
    users = [
        {
            "username": "15000128787",
            "password": "odzLFgdFUXlhxaXbIZocK1OxduX3WJvip+4LpOtNLX7cI6aI1jYNdKF+9HHyYVxs9s6SSoi73N4qJdsqcmh7rQrwOvRPY21awl66y4nGKGg39Vpa62WZTw1seGmoGfl+oWhns5IWFTzUZ4MfnShIRJLnh9/GviBbDfSLnJq/t3sTmOPc3eyfebasI1fr7PtltN2t11Fd8XIMPnnIoQie0kn0GgtXc7EEECdVcnQ3iXUiap7YeI5iE5j8aIcSXZ/WFvprIwveyCCYZRuD1T31SmwliddtEmQh6OmqPZvFZYkQV4YtSv/FwAY1+THqFPoA7W2eFpw5QKORlGlHtr49hQ=="
        },
        {
            "username": "13052739901",
            "password": "abcd@1234"
        },
        {
            "username": "15000128787",
            "password": "qwe12345"
        }
    ]
    ticket.login(*users[2].values())
    ticket.get_commerce_token()
    result = ticket.get_current_eligible()
    vids = result['vids']
    target_date_en = result['target_date_en']
    target_date_cn = result['target_date_cn']
    quantity = len(vids)
    result = ticket.get_morning_target_day_price(result['target_date_en'])
    start_time = result['startDateTime']
    price = result['price']
    total_price = str(int(result['totalPrice']) * quantity)
    result = ticket.confirm_morning_order(vids, "321025197912160221",
                                          start_time,
                                          target_date_en,
                                          target_date_cn,
                                          price,
                                          total_price)
    # print(result)
    # ticket.get_commerce_orders()
    # print(result)
    # result = ticket.check_monirng_calander()
    # print(result)
    # link_success, vid, target = ticket.link_card("GAL2073023028053262")


