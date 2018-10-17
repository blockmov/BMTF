# coding: utf-8
import logging

import tornado.escape
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import EqualTo

from wtforms.validators import Length
from wtforms_tornado import Form

from handlers import base
from libs import memery_cache as mc
from models import customer
from models import customer_contact
from libs import utils


class AddForm(Form):
    token = StringField("token", validators=[DataRequired()])
    contact_name = StringField("contact_name", validators=[DataRequired(), Length(max=100)])
    bank_card_name = StringField("bank_card_name", validators=[DataRequired(), Length(max=100),
                                                               EqualTo("contact_name",
                                                                       message="contact_name/bank_card_name must match")])
    bank_card_number = StringField("bank_card_number", validators=[DataRequired(), Length(max=100)])
    bank_swift_code = StringField("bank_swift_code", validators=[DataRequired(), Length(max=255)])
    bank_name = StringField("bank_name", validators=[DataRequired(), Length(max=255)])
    bank_country = StringField('bank_country', validators=[DataRequired(), Length(max=255)])
    bank_city = StringField('bank_city', validators=[DataRequired(), Length(max=255)])
    bank_address = StringField("bank_address", validators=[DataRequired(), Length(max=100)])


class DeleteForm(Form):
    token = StringField("token", validators=[DataRequired()])
    contact_id = IntegerField("contact_id", validators=[DataRequired()])


class UpdateForm(Form):
    token = StringField("token", validators=[DataRequired()])
    contact_id = IntegerField("contact_id", validators=[DataRequired()])
    contact_name = StringField("contact_name", validators=[Length(max=100)])
    bank_card_name = StringField("bank_card_name", validators=[Length(max=100),
                                                               EqualTo("contact_name",
                                                                       message="contact_name/bank_card_name must match")])
    bank_card_number = StringField("bank_card_number", validators=[Length(max=100)])
    bank_swift_code = StringField("bank_swift_code", validators=[Length(max=255)])
    bank_name = StringField("bank_name", validators=[Length(max=255)])
    bank_country = StringField('bank_country', validators=[Length(max=255)])
    bank_city = StringField('bank_city', validators=[Length(max=255)])
    bank_address = StringField("bank_address", validators=[Length(max=100)])


class ListContactsForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField("index", validators=[DataRequired()])
    count = IntegerField("count", validators=[DataRequired()])


class ContactHandler(base.BaseHandler):
    """ 联系人管理 """

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "add_new_contact":
                code, message, result = self.add_new_contact(params)
            elif method == "delete_contact":
                code, message, result = self.delete_contact(params)
            elif method == "update_contact":
                code, message, result = self.update_contact(params)
            elif method == "list_all_contacts":
                code, message, result = self.list_all_contacts(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def add_new_contact(self, data):
        form = AddForm.from_json(data)
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

        contact_name = form.data["contact_name"]
        bank_card_name = form.data["bank_card_name"]
        bank_card_number = form.data["bank_card_number"]
        bank_swift_code = form.data["bank_swift_code"]
        bank_name = form.data["bank_name"]
        bank_country = form.data["bank_country"]
        bank_city = form.data["bank_city"]
        bank_address = form.data["bank_address"]

        _country = utils.find_country_by_name(bank_country)
        if not _country:
            return -1, "invalid country", {}
        bank_country_code = _country["alpha_2"]
        _contact = customer_contact.Contact.on_add_new_contact(cust_id, contact_name, bank_card_name, bank_card_number,
                                                               bank_swift_code, bank_name, bank_country_code, bank_city,
                                                               bank_address)
        if not _contact:
            return -1, "failed", {}
        return 0, "success", {}

    def delete_contact(self, data):
        form = DeleteForm.from_json(data)
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

        contact_id = form.data["contact_id"]
        contact_info = cust.contacts
        for ct in contact_info:
            if contact_id == ct.contact_id:
                status = customer_contact.Contact.on_remove_contact(contact_id)
                if status == 0:
                    return 0, "success", {}
                return -1, "failed", {}
        return 0, "success", {}

    def update_contact(self, data):
        form = UpdateForm.from_json(data)
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

        contact_id = form.data["contact_id"]
        contact_name = form.data["contact_name"]
        bank_card_name = form.data["bank_card_name"]
        bank_card_number = form.data["bank_card_number"]
        bank_swift_code = form.data["bank_swift_code"]
        bank_name = form.data["bank_name"]
        bank_country = form.data["bank_country"]
        bank_city = form.data["bank_city"]
        bank_address = form.data["bank_address"]

        _country = utils.find_country_by_name(bank_country)
        if not _country:
            return -1, "invalid country", {}
        bank_country_code = _country["alpha_2"]
        status = customer_contact.Contact.on_update_contact(contact_id, contact_name, bank_card_name, bank_card_number,
                                                            bank_swift_code, bank_name, bank_country_code, bank_city,
                                                            bank_address)
        if status != 0:
            return -1, "failed", {}

        return 0, "success", {}

    def list_all_contacts(self, data):
        form = ListContactsForm.from_json(data)
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

        # 查询联系人信息
        index = form.data["index"] - 1
        count = form.data["count"]
        items = []
        contact_info = cust.contacts

        contacts = {}
        for ct in contact_info:
            # 过滤掉已标记删除的对象
            if ct.state == "01":
                continue
            c = ct.to_dict()
            if c["bank_country_code"]:
                country_info = utils.find_country_by_code(c["bank_country_code"])
                c["country_info"] = country_info
            else:
                c["country_info"] = {}
            if ct.contact_name in contacts:
                contacts[ct.contact_name].append(c)
            else:
                contacts[ct.contact_name] = []
                contacts[ct.contact_name].append(c)
        for name, info in contacts.items():
            items.append({"contact_name": name, "card_info": info})
        total = len(items)
        result = {
            "sum": total,
            "count": len(items[index:index + count]),
            "data": items[index:index + count]
        }
        return 0, "success", result
