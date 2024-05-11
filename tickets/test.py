from tickets.desney import Desney

if __name__ == '__main__':
    desney = Desney("19807910929", "H1234567")
    try:
        # desney.login().syn_token().get_eligible().get_morning_price().pay_morning_order()
        # desney.login().syn_token().get_eligible().check_morning_date()
        desney.payment_id = "824559152b56c46477fdeee5c880ba18"
        desney.login().syn_token().pay_transactiona()
    except StopIteration:
        messages = desney.get_message()
        print("\n".join(messages))
    except Exception:
        messages = desney.get_message()
        print("\n".join(messages))
