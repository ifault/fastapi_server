import requests

from common.service import is_valid_id
from tickets.desney import Desney

def desney_test():
    desney = Desney("13127778188", "qwer1234")
    try:
        # desney.check_one_day().login().syn_token().get_one_day_mock().get_token().get_one_day_order()
        desney.login()
    except StopIteration:
        messages = desney.get_message()
        print("\n".join(messages))
    except Exception:
        messages = desney.get_message()
        print("\n".join(messages))


def connect_test():
    url = 'https://www.baidu.com'
    response = requests.get(url)
    if response.status_code == 200:
        print("百度首页可以正常访问，状态码：", response.status_code)
    else:
        print("无法访问百度首页，状态码：", response.status_code)

if __name__ == '__main__':
    desney_test()
    # print(is_valid_id("222403198502200011"))



