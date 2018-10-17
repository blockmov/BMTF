import datetime

_mem_session = {}

_mem_captcha_set = {}


class CustomerSession(object):
    def __init__(self, cust_id, cust_type):
        self.cust_id = cust_id
        self.cust_type = cust_type
        self.login_password_verify_code = ""
        self.trade_password_verify_code = ""

    def set_login_password_verify_code(self, code):
        self.login_password_verify_code = code
        self.login_password_verify_code_created_on = datetime.datetime.now()

    def set_trade_password_verify_code(self, code):
        self.trade_password_verify_code = code
        self.trade_password_verify_code_created_on = datetime.datetime.now()

    def check_login_password_verify_code(self, code):
        return self.login_password_verify_code == code

    def check_trade_password_verify_code(self, code):
        return self.trade_password_verify_code == code


class MemSession(object):
    @classmethod
    def set_customer(cls, token, val):
        if not token:
            return False
        _mem_session[token] = val
        return True

    @classmethod
    def get_customer(cls, token):
        if not token:
            return None
        return _mem_session.get(token, None)

    @classmethod
    def del_customer(cls, token):
        if _mem_session.get(token, None):
            del _mem_session[token]

class MemCaptchaSet(object):
    @classmethod
    def set_captcha(self, cid, text):
        created_on = datetime.datetime.now()
        item = {
            "text": text,
            "created_on": created_on,
        }
        _mem_captcha_set[cid] = item

    @classmethod
    def get_captcha(self, cid):
        if not cid:
            return None
        return _mem_captcha_set.get(cid, None)

    @classmethod
    def del_captcha(cls, cid):
        if _mem_captcha_set.get(cid, None):
            del _mem_captcha_set[cid]

class MemVerifyCodeSet(object):
    @classmethod
    def set_code(self, email, text):
        created_on = datetime.datetime.now()
        item = {
            "text": text,
            "created_on": created_on,
        }
        _mem_captcha_set[email] = item

    @classmethod
    def get_code(self, email):
        if not email:
            return None
        return _mem_captcha_set.get(email, None)

    @classmethod
    def del_code(cls, email):
        if _mem_captcha_set.get(email, None):
            del _mem_captcha_set[email]

