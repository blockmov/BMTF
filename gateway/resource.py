# coding: utf-8
import logging
from decimal import getcontext

import exchange
import pycountry
import tornado.escape
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms_tornado import Form

from handlers import base
from libs import phone_codes

getcontext().prec = 6

ALL_COUNTRIES = pycountry.countries
ALL_CURRENCIES = pycountry.currencies


class ExchangeForm(Form):
    currency_from = StringField("currency_from", validators=[DataRequired(), Length(min=3, max=3)])
    currency_to = StringField("currency_to", validators=[DataRequired(), Length(min=3, max=3)])


class ResourceHandler(base.BaseHandler):
    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "country_info":
                code, message, result = self.country_info()
            elif method == "exchange_rate":
                code, message, result = self.exchange_rate(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def country_info(self):
        code_list = all_phone_code_list()
        countries = []
        for c in pycountry.countries:
            if c.alpha_2 not in code_list:
                phone_code = 0
            else:
                phone_code = code_list[c.alpha_2]
            uri = "/flags/" + c.alpha_2.lower() + ".gif"
            countries.append(
                {
                    "alpha_2": c.alpha_2,
                    "name": c.name,
                    "numeric": c.numeric,
                    "uri": uri,
                    "phone_code": phone_code
                }
            )

        return 0, "success", countries

    def exchange_rate(self, data):
        form = ExchangeForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        currency_from = form.data["currency_from"].upper()
        currency_to = form.data["currency_to"].upper()

        if currency_from not in all_currencies():
            return -1, "wrong currency", {}

        if currency_to not in all_currencies():
            return -1, "wrong currency", {}
        times = 0
        while True:
            times += 1
            ex = exchange.rate(currency_from, currency_to)
            if ex or times == 5:
                break
        if not ex:
            return -1, "timeout", {}
        result = {
            "currency_from": currency_from,
            "currency_to": currency_to,
            "rate": str(ex),
        }
        return 0, "success", result

def all_countries():
    ALL_COUNTRIES = [c for c in pycountry.countries]
    result = {}
    for c in ALL_COUNTRIES:
        result[c.alpha_2] = c
    return result

def all_currencies():
    ALL_CURRENCIES = [c for c in pycountry.currencies]
    result = {}
    for c in ALL_CURRENCIES:
        result[c.alpha_3] = c
    return result

def all_phone_code_list():
    code_list = {}
    for c in phone_codes.codes_list:
        code_list[c[1]] = c[0]
    return code_list