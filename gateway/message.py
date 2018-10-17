# coding: utf-8
import logging

import tornado.escape
from wtforms.fields import DateField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms_tornado import Form

from handlers import base
from models import customer
from models import customer_message
from libs import memery_cache as mc


class ListForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField("index", validators=[DataRequired()])
    count = IntegerField("count", validators=[DataRequired()])
    state = StringField("state")
    message_type = StringField("message_type")
    begin_date = DateField("begin_date")
    end_date = DateField("end_date")


class MessageOperForm(Form):
    token = StringField("token", validators=[DataRequired()])
    message_id = IntegerField("message_id", validators=[DataRequired()])


class MessageHandler(base.BaseHandler):
    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.info(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "list_messages":
                code, message, result = self.list_messages(params)
            elif method == "delete_message":
                code, message, result = self.delete_message(params)
            elif method == "mark_read_message":
                code, message, result = self.mark_read_message(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def list_messages(self, data):
        form = ListForm.from_json(data)
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

        index = form.data["index"] - 1
        count = form.data["count"]
        state = form.data["state"]
        message_type = form.data["message_type"]
        begin_date = form.data["begin_date"]
        end_date = form.data["end_date"]

        all_messages = customer_message.CustomerMessage.on_find_all_messages(cust_id, message_type, state, begin_date,
                                                                             end_date)
        items = [i.to_dict() for i in all_messages if i.state != "02"]
        result = {
            "sum": len(items),
            "count": len(items[index:index + count]),
            "data": items[index:index + count]
        }
        return 0, "success", result

    def delete_message(self, data):
        form = MessageOperForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}

        # 检查账户是否存在
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        message_id = form.data["message_id"]
        _msg = customer_message.CustomerMessage.on_find_message_by_id(message_id)
        if _msg is None or _msg.cust_id != cust_id:
            return -1, "no permission", {}

        status = customer_message.CustomerMessage.on_update_state(message_id, "02")
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}

    def mark_read_message(self, data):
        form = MessageOperForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}

        # 检查账户是否存在
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        message_id = form.data["message_id"]
        _msg = customer_message.CustomerMessage.on_find_message_by_id(message_id)
        if _msg is None or _msg.cust_id != cust_id:
            return -1, "no permission", {}

        status = customer_message.CustomerMessage.on_update_state(message_id, "01")
        if status != 0:
            return -1, "failed", {}
        return 0, "success", {}
