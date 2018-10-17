# coding=utf-8
import logging

import tornado.escape
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms_tornado import Form

from gateway import base
from libs import memery_cache as mc
from libs import utils
from models import customer


class LogoutForm(Form):
    token = StringField("token", validators=[DataRequired()])


class LoginForm(Form):
    email = StringField('email', validators=[DataRequired(), Email()])
    password = StringField('password', validators=[DataRequired()])


class AuthHandler(base.BaseHandler):

    def post(self, action):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
        except Exception as why:
            logging.debug("{}".format(why))
            code, message, result = -1, "data format error", {}
        else:
            if action == "login":
                code, message, result = self.login(json_data)
            elif action == "logout":
                code, message, result = self.logout(json_data)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def login(self, data):
        form = LoginForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        email = form.data["email"]
        password = form.data['password']
        _customer = customer.Customer.on_find_customer_by_email(email)
        if not self._can_do_login(_customer):
            return -1, "no such a user", {}

        if _customer.login_password == utils.hash_password(password):
            cust_id, cust_type = _customer.cust_id, _customer.cust_type
            token = utils.gen_access_token()
            session = mc.CustomerSession(cust_id, cust_type)
            mc.MemSession.set_customer(token, session)
            result = {"token": token}
            return 0, "success", result
        return -1, "incorrect password", {}

    def logout(self, data):
        form = LogoutForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        mc.MemSession.del_customer(token)
        return 0, "success", {}

    def _can_do_login(self, cust):
        if not cust:
            return False
        if cust.state in ("03", "04"):
            return False
        return True
