# coding: utf-8
import logging
import uuid

import tornado.escape
import wtforms.validators
from wtforms.fields import StringField
from wtforms.fields import IntegerField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms.validators import EqualTo
from wtforms_tornado import Form

from configs.cbs import configs
from gateway import base
from libs import mailer
from libs import utils
from libs import memery_cache as mc
from models import customer
from models import customer_wallet


class RegisterForm(Form):
    company_id = IntegerField("company_id", validators=[DataRequired()])
    cust_type = StringField('cust_type', validators=[DataRequired(), Length(min=2, max=2)])
    email = StringField('email', validators=[DataRequired(), wtforms.validators.Email()])
    captcha = StringField('captcha', validators=[DataRequired()])
    device_id = StringField('device_id', validators=[DataRequired()])
    password = StringField('password', validators=[DataRequired(), Length(min=6, max=20)])
    repeat_password = StringField("repeat_password",
                                  validators=[DataRequired(), Length(min=6, max=20),
                                              EqualTo("password", message="Passwords must match")])


class ConfirmForm(Form):
    company_id = IntegerField("company_id", validators=[DataRequired()])
    cust_type = StringField('cust_type', validators=[DataRequired(), Length(min=2, max=2)])
    email = StringField('email', validators=[DataRequired(), wtforms.validators.Email()])
    password = StringField('password', validators=[DataRequired()])
    code = StringField('code', validators=[DataRequired()])


class RegisterHandler(base.BaseHandler):

    def get(self):
        self.render("front/register.tpl", configs=configs)

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            # if method == "send_register_code":
            #     code, message, result = self.send_register_code(params)
            # elif method == "register_confirm":
            #     code, message, result = self.register_confirm(params)
            if method == "register_new_customer":
                code, message, result = self.register_new_customer(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def _can_register(self, email):
        cust = customer.Customer.on_find_customer_by_email(email)
        if not cust:
            return True
        return False

    def _check_captcha(self, cid, captcha_text):
        saved_captcha_text = mc.MemCaptchaSet.get_captcha(cid)
        if not saved_captcha_text:
            return False
        return saved_captcha_text["text"] == captcha_text.lower()

    def register_new_customer(self, data):
        form = RegisterForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        # 验证码
        captcha_text = form.data["captcha"]
        cid = form.data["device_id"]
        if not self._check_captcha(cid, captcha_text):
            return -1, "wrong captcha code", {}
        mc.MemCaptchaSet.del_captcha(cid)

        email = form.data["email"]
        if not self._can_register(email):
            return -1, "user already exists", {}

        company_id = form.data["company_id"]
        cust_type = form.data["cust_type"]
        login_password = utils.hash_password(form.data['password'])

        cust = customer.Customer.on_add_new_customer(company_id, cust_type, email, login_password)
        if not cust:
            return -1, "failed", {}
        wallet_name = str(uuid.uuid4())
        wallet = customer_wallet.Wallet.on_add_new_wallet(cust.cust_id, wallet_name)
        if not wallet:
            logging.error("create wallet failed: <{}>".format(email))
        mailer.send_register_welcome_email(email)
        return 0, "success", {}

    # def send_register_code(self, data):
    #     form = RegisterForm.from_json(data)
    #     if not form.validate():
    #         return -1, str(form.errors), {}
    #
    #     email = form.data["email"]
    #     login_password = utils.hash_password(form.data['password'])
    #     cust_type = form.data['cust_type']
    #     company_id = form.data['company_id']
    #
    #     if not self._can_register(email):
    #         return -1, "user already exists", {}
    #
    #     register_code = utils.gen_rand_num_str()
    #     self.session["r_email"] = email
    #     self.session["r_login_password"] = login_password
    #     self.session["r_cust_type"] = cust_type
    #     self.session["r_company_id"] = company_id
    #     self.session["r_register_code"] = register_code
    #     mailer.send_register_verify_email(email, register_code)
    #     return 0, "success", {}
    #
    # def register_confirm(self, data):
    #     form_data = {
    #         "company_id": self.session["r_company_id"],
    #         "cust_type": self.session["r_cust_type"],
    #         "email": self.session["r_email"],
    #         "password": self.session["r_login_password"],
    #         "code": data.get("code", None)
    #     }
    #     logging.info(form_data)
    #
    #     form = ConfirmForm.from_json(form_data)
    #     if not form.validate():
    #         return -1, str(form.errors), {}
    #
    #     register_code = form.data["code"]
    #     if register_code != self.session["r_register_code"]:
    #         return -1, "incorrect code", {}
    #
    #     company_id = form.data["company_id"]
    #     cust_type = form.data["cust_type"]
    #     email = form.data["email"]
    #     login_password = form.data["password"]
    #     cust = customer.Customer.on_add_new_customer(company_id, cust_type, email, login_password)
    #     if not cust:
    #         return -1, "failed", {}
    #     del self.session["r_company_id"]
    #     del self.session["r_cust_type"]
    #     del self.session["r_email"]
    #     del self.session["r_login_password"]
    #     return 0, "success", {}


class RegisterResultHandler(base.BaseHandler):
    def get(self, status):
        if status in ('complete', 'success', 'error'):
            self.render("front/register_%s.tpl" % status, configs=configs)
        else:
            self.render("error/404.tpl", configs=configs)
