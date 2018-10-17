# coding: utf-8
import logging

import tornado.escape
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms_tornado import Form

from handlers import base
from models import company
from models import customer
from libs import memery_cache as mc
from libs import utils

CBS_SUPPORTED_LANG = ["English", "Chinese"]
# CBS_SUPPORTED_CURRENCY = ["USD", "CYN"]
CBS_SUPPORTED_CURRENCY = ["USD"]


class GetBmcardsForm(Form):
    token = StringField("token", validators=[DataRequired()])


class PublicHandler(base.BaseHandler):
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
            if method == "supported_languages":
                code, message, result = supported_languages()
            elif method == "supported_currencies":
                code, message, result = supported_currencies()
            elif method == "supported_countries":
                code, message, result = supported_countries()
            elif method == "bm_cards":
                code, message, result = bm_cards(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)


def bm_cards(data):
    form = GetBmcardsForm.from_json(data)
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

    company_id = cust.company_id
    company_info = company.Company.on_find_company_by_id(company_id)
    if not company_info:
        return -1, "invalid operation", {}

    items = []
    all_bank_cards = [card for card in company_info.bank_cards]
    for card in all_bank_cards:
        if card.state == "00":
            card_info = {
                "card_id": card.card_id,
                "card_name": card.card_name,
                "card_number": card.card_number,
                "bank_swift_code": card.bank_swift_code,
                "bank_name": card.bank_name,
                "bank_address": card.bank_address,
            }
            items.append(card_info)
    result = {
        "count": len(items),
        "data": items
    }
    return 0, "success", result


def supported_languages():
    items = CBS_SUPPORTED_LANG
    result = {
        "count": len(items),
        "data": items
    }
    return 0, "success", result


def supported_currencies():
    items = CBS_SUPPORTED_CURRENCY
    result = {
        "count": len(items),
        "data": items
    }
    return 0, "success", result


def supported_countries():
    items = []
    all_companies = company.Company.on_list_all()
    for i in all_companies:
        country_code = i.country
        country_info = utils.find_country_by_code(country_code)
        items.append({
            "country_info": country_info,
            "company_id": i.company_id
        })
    result = {
        "count": len(items),
        "data": items
    }
    return 0, "success", result
