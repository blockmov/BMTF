# coding: utf-8
import imghdr
import logging
import os
import uuid

import tornado.escape
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo
from wtforms.validators import Length
from wtforms_tornado import Form

import const
from handlers import base
from libs import memery_cache as mc
from libs import utils
from models import customer


class GetInfoForm(Form):
    token = StringField("token", validators=[DataRequired()])


class ChangePasswordForm(Form):
    token = StringField("token", validators=[DataRequired()])
    old_password = StringField("old_password", validators=[DataRequired()])
    new_password = StringField("new_password", validators=[DataRequired(), Length(min=6, max=20)])
    repeat_password = StringField("repeat_password",
                                  validators=[DataRequired(), Length(min=6, max=20),
                                              EqualTo("new_password", message="Passwords must match")])


class SetVerificationForm(Form):
    token = StringField("token", validators=[DataRequired()])
    account_name = StringField("account_name", validators=[DataRequired()])
    passport_id = StringField("passport_id", validators=[DataRequired()])
    birthday = DateField("birthday", validators=[DataRequired()])


class SetAvatarForm(Form):
    token = StringField("token", validators=[DataRequired()])


class SetLangForm(Form):
    token = StringField("token", validators=[DataRequired()])
    lang = StringField("lang", validators=[DataRequired()])


class SetTimezoneForm(Form):
    timezone = StringField("timezone", validators=[DataRequired()])


class SetCurrencyForm(Form):
    token = StringField("token", validators=[DataRequired()])
    currency = StringField("currency", validators=[DataRequired()])


class SetPersonCertForm(Form):
    token = StringField("token", validators=[DataRequired()])
    cust_name = StringField('cust_name', validators=[Length(max=100)])
    cust_first_name = StringField('cust_first_name', validators=[DataRequired(), Length(max=100)])
    cust_last_name = StringField('cust_last_name', validators=[DataRequired(), Length(max=100)])
    mobile_phone = StringField('mobile_phone', validators=[DataRequired(), Length(max=100)])
    per_birthday = DateField('per_birthday', validators=[DataRequired()])
    per_country = StringField('per_country', validators=[DataRequired(), Length(max=100)])
    per_city = StringField('per_city', validators=[Length(max=100)])
    per_address1 = StringField('per_address1', validators=[DataRequired(), Length(max=200)])
    per_address2 = StringField('per_address2', validators=[Length(max=200)])
    per_postcode = StringField('per_postcode', validators=[Length(max=20)])
    # per_cert_scan = StringField('per_cert_scan', validators=[DataRequired(), Length(max=4096)])


class SetCorporationCertForm(Form):
    token = StringField("token", validators=[DataRequired()])
    co_name = StringField('co_name', validators=[DataRequired(), Length(max=100)])
    co_business_card_no = StringField('co_business_card_no', validators=[DataRequired(), Length(max=100)])
    co_business_scope = StringField('co_business_scope', validators=[DataRequired(), Length(max=100)])
    co_country = StringField('co_country', validators=[DataRequired(), Length(max=100)])
    co_city = StringField('co_city', validators=[Length(max=100)])
    co_address1 = StringField('co_address1', validators=[DataRequired(), Length(max=200)])
    co_address2 = StringField('co_address2', validators=[Length(max=200)])
    co_postcode = StringField('co_postcode', validators=[Length(max=20)])
    co_business_type = StringField('co_business_type', validators=[Length(max=20)])
    co_website = StringField('co_website', validators=[Length(max=20)])
    co_title = StringField('co_title', validators=[Length(max=20)])
    # co_cert_scan = StringField('co_cert_scan', validators=[DataRequired(), Length(max=4096)])


class ProfileHandler(base.BaseHandler):
    """ 客户资料 """

    def put(self):
        try:
            method = self.get_body_argument("method", None)
            params = tornado.escape.json_decode(self.get_body_argument("params", None))
        except Exception as why:
            code, message, result = -1, "data format error", {}
        else:
            if method == "update_person_cert":
                code, message, result = self.update_person_certificate(params)
            elif method == "update_corporation_cert":
                code, message, result = self.update_corporation_certificate(params)
            elif method == "update_avatar":
                code, message, result = self.update_avatar(params)
            else:
                code, message, result = -1, "wrong method", {}
        self.send_json_response(code, message, result)

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "get_general_info":
                code, message, result = self.get_general_info(params)
            elif method == "set_avatar":
                code, message, result = self.set_avatar(params)
            elif method == "set_lang":
                code, message, result = self.set_lang(params)
            elif method == "set_timezone":
                code, message, result = self.set_timezone(params)
            elif method == "set_currency":
                code, message, result = self.set_currency(params)
            elif method == "get_person_cert":
                code, message, result = self.get_person_cert(params)
            elif method == "get_corporation_cert":
                code, message, result = self.get_corporation_cert(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def get_general_info(self, data):
        form = GetInfoForm.from_json(data)
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

        # 支付密码设置状态
        trade_password = cust.trade_password
        has_trade_password = True
        if not trade_password:
            has_trade_password = False
        if_trade_password = "Y" if has_trade_password else "N"

        cust_info = cust.to_dict()
        result = {
            "cust_id": cust_info["cust_id"],
            "cust_type": cust_info["cust_type"],
            # "cust_name": cust_info["cust_name"],
            "cust_name": "{} {}".format(cust_info["cust_first_name"], cust_info["cust_last_name"]),
            "if_trust_name": cust_info["if_trust_name"],
            "if_certificate": cust_info["if_certificate"],
            "if_mobile": cust_info["if_mobile"],
            "if_email_alarm": cust_info["if_email_alarm"],
            "if_mobile_alarm": cust_info["if_mobile_alarm"],
            "state": cust_info["state"],
            "lang": cust_info["lang"],
            "timezone": cust_info["timezone"],
            "currency": cust_info["currency"],
            "mobile_phone": cust_info["mobile_phone"],
            "email": cust_info["email"],
            "avatar": cust_info["avatar"],
            "last_login_on": cust_info["last_login_on"],
            "created_on": cust_info["created_on"],
            "if_trade_password": if_trade_password,
        }
        return 0, "success", result

    def set_avatar(self, data):
        form = SetAvatarForm.from_json(data)
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

        # 处理图片
        upload_path = const.AVATAR_FILE_PATH
        file_metas = self.request.files.get("image_avatar", None)
        if not file_metas:
            return -1, "failed: no image files", {}
        meta = file_metas[0]
        filename = utils.gen_rand_avatar_name()
        file_path = os.path.join(upload_path, filename)
        try:
            with open(file_path, "wb") as fp:
                fp.write(meta["body"])
        except Exception as why:
            logging.error(why)
            return -1, "failed: something wrong on server", {}
        img_type = imghdr.what(file_path)
        if not img_type:
            os.remove(file_path)
            return -1, "failed: no image files", {}
        avatar_file_path = "{0}/{1}.{2}".format(const.AVATAR_FILE_PATH, filename, img_type)
        os.rename(file_path, avatar_file_path)

        # 保存图片位置到数据库中
        status = customer.Customer.on_set_avatar(cust_id, avatar_file_path)
        if status == 0:
            return 0, "success", {}
        return -1, "failed", {}

    def set_lang(self, data):
        form = SetLangForm.from_json(data)
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

        lang = form.data["lang"]
        status = customer.Customer.on_set_lang(cust_id, lang)
        if status == 0:
            return 0, "success", {}
        return -1, "failed", {}

    def set_timezone(self, data):
        form = SetTimezoneForm.from_json(data)
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

        timezone = form.data["timezone"]
        status = customer.Customer.on_set_timezone(cust_id, timezone)
        if status == 0:
            return 0, "success", {}
        return -1, "failed", {}

    def set_currency(self, data):
        form = SetCurrencyForm.from_json(data)
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

        currency = form.data["currency"]
        status = customer.Customer.on_set_currency(cust_id, currency)
        if status == 0:
            return 0, "success", {}
        return -1, "failed", {}

    def update_person_certificate(self, data):
        token = data.get("token", None)
        if not token:
            return -1, "invalid session", {}
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        # if cust.state in ("01", "02", "04"):
        #     return 0, "success", {}

        if cust.if_trust_name == "Y":
            return 0, "You have already completed the authentication.", {}

        # step 1, 处理证件图片资料
        upload_path = const.IDENTITY_FILE_PATH
        file_metas = self.request.files.get("per_cert_scan", None)
        if not file_metas:
            return -1, "failed: no image files", {}

        filelist = []
        for meta in file_metas:
            # meta = file_metas[0]
            filename = str(uuid.uuid4())
            file_path = os.path.join(upload_path, filename)

            try:
                with open(file_path, "wb") as fp:
                    fp.write(meta["body"])
                img_type = imghdr.what(file_path)
                if not img_type:
                    os.remove(file_path)
                    return -1, "failed: no image files", {}
                filename = "{}.{}".format(filename, img_type)
                new_file_path = "{}".format(os.path.join(const.IDENTITY_FILE_PATH, filename))
                os.rename(file_path, new_file_path)
                filelist.append(filename)
            except Exception as why:
                logging.error(why)
                return -1, "failed: something wrong on server", {}

        # step 2, 处理文字资料
        form = SetPersonCertForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        cust_name = form.data["cust_name"]
        cust_first_name = form.data["cust_first_name"]
        cust_last_name = form.data["cust_last_name"]
        mobile_phone = form.data["mobile_phone"]
        per_birthday = form.data["per_birthday"]
        per_country = form.data["per_country"]
        per_city = form.data["per_city"]
        per_address1 = form.data["per_address1"]
        per_address2 = form.data["per_address2"]
        per_postcode = form.data["per_postcode"]
        per_cert_scan = ",".join(filelist)
        status = customer.Customer.on_set_person_certificate(cust_id, cust_name, cust_first_name, cust_last_name,
                                                             mobile_phone, per_birthday, per_country, per_city,
                                                             per_address1, per_address2, per_postcode, per_cert_scan)
        if status != 0:
            return -1, "failed", {}
        # 修改客户状态为`待审核`
        status = customer.Customer.on_set_state(cust_id, state="01")
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}

    def update_corporation_certificate(self, data):
        token = data.get("token", None)
        if not token:
            return -1, "invalid session", {}
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        # step 1, 检查账户是否存在
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        # if cust.state in ("01", "02", "04"):
        #     return 0, "success", {}

        # if cust.if_trust_name != "Y":
        #     return -1, "Please submit your personal information first. ", {}

        # step 1, 处理证件图片资料
        upload_path = const.IDENTITY_FILE_PATH
        file_metas = self.request.files.get("co_cert_scan", None)
        if not file_metas:
            return -1, "failed: no image files", {}

        filelist = []
        for meta in file_metas:
            # meta = file_metas[0]
            filename = str(uuid.uuid4())
            file_path = os.path.join(upload_path, filename)

            try:
                with open(file_path, "wb") as fp:
                    fp.write(meta["body"])
                img_type = imghdr.what(file_path)
                if not img_type:
                    os.remove(file_path)
                    return -1, "failed: no image files", {}
                filename = "{}.{}".format(filename, img_type)
                new_file_path = "{}".format(os.path.join(const.IDENTITY_FILE_PATH, filename))
                os.rename(file_path, new_file_path)
                filelist.append(filename)
            except Exception as why:
                logging.error(why)
                return -1, "failed: something wrong on server", {}

        form = SetCorporationCertForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        co_name = form.data["co_name"]
        co_business_card_no = form.data["co_business_card_no"]
        co_business_scope = form.data["co_business_scope"]
        co_country = form.data["co_country"]
        co_city = form.data["co_city"]
        co_address1 = form.data["co_address1"]
        co_address2 = form.data["co_address2"]
        co_postcode = form.data["co_postcode"]
        co_business_type = form.data["co_business_type"]
        co_website = form.data["co_website"]
        co_title = form.data["co_title"]
        co_cert_scan = ",".join(filelist)
        status = customer.Customer. \
            on_set_corporation_certificate(cust_id, co_name, co_business_card_no, co_business_scope, co_country,
                                           co_city, co_address1, co_address2, co_postcode, co_business_type, co_website,
                                           co_title, co_cert_scan)
        if status != 0:
            return -1, "failed", {}
        # 修改客户状态为`待审核`
        status = customer.Customer.on_set_state(cust_id, state="01")
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}

    def get_person_cert(self, data):
        form = GetInfoForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        cust_info = cust.to_dict()
        if cust_info["per_cert_scan"]:
            per_cert_scan = ["/i/" + i for i in cust_info["per_cert_scan"].split(",")]
        else:
            per_cert_scan = []
        # 个人资料
        result = {
            "cust_first_name": cust_info["cust_first_name"],
            "cust_last_name": cust_info["cust_last_name"],
            "mobile_phone": cust_info["mobile_phone"],
            "per_birthday": cust_info["per_birthday"],
            "per_country": cust_info["per_country"],
            "per_city": cust_info["per_city"],
            "per_address1": cust_info["per_address1"],
            "per_address2": cust_info["per_address2"],
            "per_postcode": cust_info["per_postcode"],
            "per_cert_scan": per_cert_scan,
        }
        return 0, "success", result

    def get_corporation_cert(self, data):
        form = GetInfoForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        cust_info = cust.to_dict()
        if cust_info["co_cert_scan"]:
            co_cert_scan = ["/i/" + i for i in cust_info["co_cert_scan"].split(",")]
        else:
            co_cert_scan = []
        # 企业资料
        result = {
            "co_name": cust_info["co_name"],
            "co_business_card_no": cust_info["co_business_card_no"],
            "co_business_scope": cust_info["co_business_scope"],
            "co_country": cust_info["co_country"],
            "co_city": cust_info["co_city"],
            "co_address1": cust_info["co_address1"],
            "co_address2": cust_info["co_address2"],
            "co_postcode": cust_info["co_postcode"],
            "co_business_type": cust_info["co_business_type"],
            "co_website": cust_info["co_website"],
            "co_title": cust_info["co_title"],
            "co_cert_scan": co_cert_scan,
        }
        return 0, "success", result

    def update_avatar(self, data):
        form = GetInfoForm.from_json(data)
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

        upload_path = const.AVATAR_FILE_PATH
        file_metas = self.request.files.get("avatar", None)
        if not file_metas:
            return -1, "failed: no image files", {}

        meta = file_metas[0]
        filename = str(uuid.uuid4())
        file_path = os.path.join(upload_path, filename)

        try:
            with open(file_path, "wb") as fp:
                fp.write(meta["body"])
            img_type = imghdr.what(file_path)
            if not img_type:
                os.remove(file_path)
                return -1, "failed: no image files", {}
            filename = "{}.{}".format(filename, img_type)
            new_file_path = "{}".format(os.path.join(const.AVATAR_FILE_PATH, filename))
            os.rename(file_path, new_file_path)
        except Exception as why:
            logging.error(why)
            return -1, "failed: something wrong on server", {}

        avatar = filename
        status = customer.Customer.on_set_avatar(cust_id, avatar)
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}
