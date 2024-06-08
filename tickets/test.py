import requests

from tickets.desney import Desney
from tickets.responses import order_info_response


def desney_test():
    desney = Desney("13052739901", "abcd@1234", debug=True)
    try:
        desney = desney.login().syn_token().get_order_info()
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
    desney = Desney("13052739901", "abcd@1234", debug=False)
    # desney = Desney("13767116418", "XY123456", debug=True)
    try:
        desney = desney.login().syn_token().get_token().link_order("GAL6305323007882207")
        messages = desney.get_message()
        print("\n".join(messages))
    except StopIteration:
        messages = desney.get_message()
        print("\n".join(messages))
    except Exception:
        messages = desney.get_message()
        print("\n".join(messages))
    # print(is_valid_id("222403198502200011"))


