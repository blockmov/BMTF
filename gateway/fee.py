# coding: utf-8
import logging

import tornado.escape
from wtforms.fields import IntegerField
from wtforms.fields import DecimalField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms_tornado import Form

from gateway import base
from libs import memery_cache as mc
from models import customer
from models import fee_method
from libs import utils


class ListForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField('index', validators=[DataRequired()])
    count = IntegerField('count', validators=[DataRequired()])


class FeeCalcForm(Form):
    token = StringField("token", validators=[DataRequired()])
    # src_country = StringField("src_country", validators=[DataRequired()])
    dst_country = StringField("dst_country", validators=[DataRequired()])
    amount = DecimalField("amount", validators=[InputRequired()])


class FeeHandler(base.BaseHandler):
    """ 收费标准 """

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            print method
            if method == "get_fee_info":
                code, message, result = self.get_fee_info(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def get_fee_info(self, data):
        form = ListForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        token = form.data["token"]
        index = form.data["index"] - 1
        count = form.data["count"]

        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        company_id = cust.company_id
        fee_method_type = "00"
        if cust.cust_type == "01":
            fee_method_type = "01"
        all_fee_methods = fee_method.FeeMethod.on_list_all(company_id, fee_method_type)
        items = []
        for method in all_fee_methods:
            fee_method_info = method.to_dict()
            src_country_info = utils.find_country_by_code(fee_method_info["src_country"])
            dst_country_info = utils.find_country_by_code(fee_method_info["dst_country"])
            fee_method_info["src_country_info"] = src_country_info
            fee_method_info["dst_country_info"] = dst_country_info
            if method.fee_details:
                fee_detail_info = [fee_detail.to_dict() for fee_detail in method.fee_details]
            else:
                fee_detail_info = []
            info = {
                "fee_method_info": fee_method_info,
                "fee_detail_info": fee_detail_info,
            }
            items.append({"item": info})

        result = {
            "sum": len(items),
            "count": len(items[index:index + count]),
            "data": items[index:index + count]}
        return 0, "success", result

    def fee_calc(self, data):
        form = FeeCalcForm.from_json(data)
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

        # src_country = form.data["src_country"]
        src_country = cust.company.country
        dst_country = form.data["dst_country"]
        amount = form.data["amount"]

        if not utils.find_country_by_code(src_country):
            return -1, "invalid country", {}
        if not utils.find_country_by_code(dst_country):
            return -1, "invalid country", {}

        fee_method_type = "00"
        if cust.cust_type == "01":
            fee_method_type = "01"
        status, _, fee_amount = utils.fee_calc(src_country, dst_country, fee_method_type, amount)
        if status != 0:
            result = {
                "status": "not support",
                "fee_method_type": fee_method_type,
                "fee_amount": "0.00",
                "amount": str(amount),
            }
        else:
            result = {
                "status": "ok",
                "fee_method_type": fee_method_type,
                "fee_amount": str(fee_amount),
                "amount": str(amount),
            }
        return 0, "success", result
