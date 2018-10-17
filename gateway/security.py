# coding: utf-8
import logging

import tornado.escape
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Length
from wtforms_tornado import Form

from gateway import base
from libs import memery_cache as mc
from libs import utils
from libs import mailer
from models import customer


class SendEmailForm(Form):
    token = StringField("token", validators=[])
    email = StringField("email", validators=[DataRequired(), Email()])
    verify_type = StringField("verify_type", validators=[DataRequired()])


class VerifyConfirmForm(Form):
    email = StringField("email", validators=[Email()])
    token = StringField("token", validators=[])
    verify_type = StringField("verify_type", validators=[DataRequired()])
    verify_code = StringField("verify_code", validators=[DataRequired()])


class LoginPasswordForm(Form):
    token = StringField("token", validators=[DataRequired()])
    old_password = StringField("old_password", validators=[DataRequired()])
    new_password = StringField("new_password", validators=[DataRequired(), Length(min=6, max=20)])
    repeat_password = StringField("repeat_password",
                                  validators=[DataRequired(), Length(min=6, max=20),
                                              EqualTo("new_password", message="Passwords must match")])


class TradePasswordForm(Form):
    token = StringField("token", validators=[DataRequired()])
    old_password = StringField("old_password", validators=[DataRequired()])
    new_password = StringField("new_password", validators=[DataRequired(), Length(min=6, max=20)])
    repeat_password = StringField("repeat_password",
                                  validators=[DataRequired(), Length(min=6, max=20),
                                              EqualTo("new_password", message="Passwords must match")])


class ResetLoginPasswordForm(Form):
    email = StringField("email", validators=[DataRequired()])
    verify_code = StringField("verify_code", validators=[DataRequired()])
    new_password = StringField("new_password", validators=[DataRequired(), Length(min=6, max=20)])
    repeat_password = StringField("repeat_password",
                                  validators=[DataRequired(), Length(min=6, max=20),
                                              EqualTo("new_password", message="Passwords must match")])


class ResetTradePasswordForm(Form):
    token = StringField("token", validators=[DataRequired()])
    verify_code = StringField("verify_code", validators=[DataRequired()])
    new_password = StringField("new_password", validators=[DataRequired(), Length(min=6, max=20)])
    repeat_password = StringField("repeat_password",
                                  validators=[DataRequired(), Length(min=6, max=20),
                                              EqualTo("new_password", message="Passwords must match")])


class CheckTradePasswordStateForm(Form):
    token = StringField("token", validators=[DataRequired()])


class SecurityHandler(base.BaseHandler):
    """ 安全设置 """

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "send_verify_email":
                code, message, result = self.send_verify_email(params)
            elif method == "verify_confirm":
                code, message, result = self.verify_confirm(params)
            elif method == "set_login_password":
                code, message, result = self.set_login_password(params)
            elif method == "set_trade_password":
                code, message, result = self.set_trade_password(params)
            elif method == "check_trade_password_state":
                code, message, result = self.check_trade_password_state(params)
            elif method == "reset_login_password":
                code, message, result = self.reset_login_password(params)
            elif method == "reset_trade_password":
                code, message, result = self.reset_trade_password(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def send_verify_email(self, data):
        form = SendEmailForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        email = form.data["email"]
        verify_type = form.data["verify_type"]
        if verify_type not in ("L", "T"):
            return -1, "wrong verify type", {}

        # code = utils.gen_rand_num_str(6)
        code = "123456"
        if verify_type == "L":
            # 找回登录密码不需要登录
            _cust = customer.Customer.on_find_customer_by_email(email)
            if not _cust:
                return -1, "no such a user", {}
            mc.MemVerifyCodeSet.set_code(email, code)
            mailer.send_reset_login_password_verify_email(email, code)
        else:
            # 找回支付密码需要登录
            token = form.data["token"]
            session = mc.MemSession.get_customer(token)
            if not session:
                return -1, "invalid session", {}
            session.set_trade_password_verify_code(code)
            mailer.send_reset_trade_password_verify_email(email, code)
        return 0, "success", {}

    def verify_confirm(self, data):
        form = VerifyConfirmForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        verify_type = form.data["verify_type"]
        verify_code = form.data["verify_code"]

        if verify_type not in ("L", "T"):
            return -1, "wrong verify type", {}

        if verify_type == "L":
            email = form.data["email"]
            code = mc.MemVerifyCodeSet.get_code(email)
            if not code:
                return -1, "incorrect code", {}
            status = code["text"] == verify_code
        else:
            # 找回支付密码需要登录
            token = form.data["token"]
            session = mc.MemSession.get_customer(token)
            if not session:
                return -1, "invalid session", {}
            status = session.check_trade_password_verify_code(verify_code)
        if not status:
            return -1, "incorrect code", {}
        return 0, "success", {}

    def set_login_password(self, data):
        form = LoginPasswordForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        old_password = utils.hash_password(form.data["old_password"])
        new_password = utils.hash_password(form.data["new_password"])
        if cust.login_password == old_password:
            status = customer.Customer.on_set_login_password(cust_id, new_password)
            if status == 0:
                return 0, "success", {}
            else:
                return -1, "failed", {}
        return -1, "incorrect old password", {}

    def set_trade_password(self, data):
        form = TradePasswordForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        old_password = utils.hash_password(form.data["old_password"])
        new_password = utils.hash_password(form.data["new_password"])

        has_trade_password = True
        trade_password = cust.trade_password
        if not trade_password:
            has_trade_password = False
        # 已设置过交易密码
        if has_trade_password:
            if cust.trade_password == old_password:
                status = customer.Customer.on_set_trade_password(cust_id, new_password)
                if status != 0:
                    return -1, "failed", {}
            else:
                return -1, "incorrect old password", {}
        else:
            status = customer.Customer.on_set_trade_password(cust_id, new_password)
            if status != 0:
                return -1, "failed", {}
        return 0, "success", {}

    def check_trade_password_state(self, data):
        form = CheckTradePasswordStateForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        trade_password = cust.trade_password
        has_trade_password = True
        if not trade_password:
            has_trade_password = False
        state = "Y" if has_trade_password else "N"
        result = {
            "state": state
        }
        return 0, "success", result

    def reset_login_password(self, data):
        form = ResetLoginPasswordForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        email = form.data["email"]
        verify_code = form.data["verify_code"]
        new_password = utils.hash_password(form.data["new_password"])

        # 检查验证码
        code = mc.MemVerifyCodeSet.get_code(email)
        if not code:
            return -1, "incorrect code", {}
        status = code["text"] == verify_code
        if not status:
            return -1, "incorrect code", {}
        mc.MemVerifyCodeSet.set_code(email, "")

        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_email(email)
        if not cust:
            return -1, "no permission", {}

        status = customer.Customer.on_set_login_password(cust.cust_id, new_password)
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}

    def reset_trade_password(self, data):
        form = ResetTradePasswordForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        session = mc.MemSession.get_customer(token)
        if not session:
            return -1, "invalid session", {}

        # 检查验证码
        verify_code = form.data["verify_code"]
        status = session.check_trade_password_verify_code(verify_code)
        if not status:
            return -1, "incorrect code", {}
        session.set_trade_password_verify_code("")

        cust_id = session.cust_id
        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        new_password = utils.hash_password(form.data["new_password"])
        status = customer.Customer.on_set_trade_password(cust_id, new_password)
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}
