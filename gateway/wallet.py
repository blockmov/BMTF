# coding: utf-8
import logging

import tornado.escape
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import Length
from wtforms_tornado import Form

from handlers import base
from libs import memery_cache as mc
from models import customer
from models import customer_card
from models import customer_wallet
from libs import utils


class WalletInfoForm(Form):
    token = StringField("token", validators=[DataRequired()])


class GetInfoForm(Form):
    token = StringField("token", validators=[DataRequired()])
    card_id = IntegerField('card_id', validators=[DataRequired()])


class AddCardForm(Form):
    token = StringField("token", validators=[DataRequired()])
    bank_card_name = StringField('bank_card_name', validators=[DataRequired(), Length(max=255)])
    bank_card_number = StringField('bank_card_number', validators=[DataRequired(), Length(max=100)])
    bank_swift_code = StringField('bank_swift_code', validators=[DataRequired(), Length(max=100)])
    bank_name = StringField('bank_name', validators=[DataRequired(), Length(max=255)])
    bank_country = StringField('bank_country', validators=[DataRequired(), Length(max=255)])
    bank_city = StringField('bank_city', validators=[DataRequired(), Length(max=255)])
    bank_address = StringField('bank_address', validators=[DataRequired(), Length(max=255)])


class DeleteCardForm(Form):
    token = StringField("token", validators=[DataRequired()])
    card_id = IntegerField('card_id', validators=[DataRequired()])


class ListCardsForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField('index', validators=[DataRequired()])
    count = IntegerField('count', validators=[DataRequired()])


class WalletHandler(base.BaseHandler):
    """ 钱包管理（银行卡） """

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "add_new_card":
                code, message, result = self.add_new_card(params)
            elif method == "delete_card":
                code, message, result = self.delete_card(params)
            elif method == "list_all_cards":
                code, message, result = self.list_all_cards(params)
            elif method == "wallet_info":
                code, message, result = self.wallet_info(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def wallet_info(self, data):
        form = WalletInfoForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        # 检查会话
        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}

        # 检查账户
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        _wallet = customer_wallet.Wallet.on_find_wallet_by_cust_id(cust_id)
        if not _wallet:
            return -1, "account not activated", {}
        wallet_info = _wallet.api_to_dict()
        wallet_info["last_month_expenditure_amount"] = "0.00"
        wallet_info["last_month_income_amount"] = "0.00"
        wallet_info["currency"] = cust.currency
        return 0, "success", wallet_info

    def add_new_card(self, data):
        form = AddCardForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        # 检查会话
        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}

        # 检查账户
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        wallet = cust.wallet
        if not wallet:
            return -1, "account not activated", {}

        wallet_id = cust.wallet.wallet_id
        bank_card_name = form.data["bank_card_name"]
        bank_card_number = form.data["bank_card_number"]
        bank_swift_code = form.data["bank_swift_code"]
        bank_country = form.data["bank_country"]
        bank_city = form.data["bank_city"]
        bank_name = form.data["bank_name"]
        bank_address = form.data["bank_address"]

        _country = utils.find_country_by_name(bank_country)
        if not _country:
            return -1, "invalid country", {}
        bank_country_code = _country["alpha_2"]

        _card = customer_card.Card.on_add_new_card(wallet_id, bank_card_name, bank_card_number, bank_swift_code,
                                                   bank_name, bank_country_code, bank_city, bank_address)
        if not _card:
            return -1, "failed", {}
        return 0, "success", {}

    def delete_card(self, data):
        form = DeleteCardForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        # 检查会话
        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}

        # 检查账户
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        card_id = form.data["card_id"]
        wallet_info = cust.wallet
        if wallet_info:
            cards = wallet_info.cards
            for card in cards:
                if card.card_id == card_id:
                    status = customer_card.Card.on_delete_card(card_id)
                    if status != 0:
                        return -1, "failed", {}
                    break
        return 0, "success", {}

    def list_all_cards(self, data):
        form = ListCardsForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        # 检查会话
        token = form.data["token"]
        cust = mc.MemSession.get_customer(token)
        if not cust:
            return -1, "invalid session", {}

        # 检查账户
        cust_id = cust.cust_id
        cust = customer.Customer.on_find_customer_by_id(cust_id)
        if not cust:
            return -1, "no permission", {}

        index = form.data["index"] - 1
        count = form.data["count"]
        # 查询银行卡信息
        items = []
        wallet_info = cust.wallet
        if wallet_info:
            cards = wallet_info.cards
            for card in cards:
                if card.state == "03":
                    continue
                card_info = card.to_dict()
                if card_info["bank_country_code"]:
                    country_info = utils.find_country_by_code(card_info["bank_country_code"])
                    card_info["country_info"] = country_info
                else:
                    card_info["country_info"] = {}
                items.append(card_info)
        result = {
            "sum": len(items),
            "count": len(items[index:index + count]),
            "data": items[index:index + count]
        }
        return 0, "success", result
