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
from models import customer_card
from models import withdraw
from libs import memery_cache as mc
from libs import utils


class GetInfoForm(Form):
    token = StringField("token", validators=[DataRequired()])
    withdraw_id = IntegerField("withdraw_id", validators=[DataRequired()])


class RegisterNewWithdrawForm(Form):
    token = StringField("token", validators=[DataRequired()])
    card_id = IntegerField("card_id", validators=[DataRequired()])
    amount = StringField("amount", validators=[DataRequired()], )
    currency = StringField("currency", validators=[DataRequired()])
    note = StringField("note", validators=[DataRequired()])
    trade_password = StringField("trade_password", validators=[DataRequired()])


class CancelForm(Form):
    token = StringField("token", validators=[DataRequired()])
    withdraw_id = IntegerField("withdraw_id", validators=[DataRequired()])


class ListForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField("index", validators=[DataRequired()])
    count = IntegerField("count", validators=[DataRequired()])
    sEcho = IntegerField("sEcho")
    card_id = IntegerField("card_id")
    state = StringField("state")
    finance_deal_state = StringField("finance_deal_state")
    begin_date = DateField("begin_date")
    end_date = DateField("end_date")


class WithdrawHandler(base.BaseHandler):
    """ 账户管理 """

    def post(self):
        try:
            json_data = tornado.escape.json_decode(self.request.body)
            method = json_data.get("method", None)
            params = json_data.get("params", None)
        except Exception as why:
            logging.debug(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "get_withdraw_info":
                code, message, result = self.get_withdraw_info(params)
            elif method == "register_new_withdraw":
                code, message, result = self.register_new_withdraw(params)
            elif method == "list_withdraws":
                code, message, result = self.list_withdraws(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def get_withdraw_info(self, data):
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

        withdraw_id = form.data["withdraw_id"]
        _withdraw = withdraw.Withdraw.on_find_withdraw_by_withdraw_id(withdraw_id)
        if not _withdraw:
            return -1, "failed", {}
        if _withdraw.cust_id != cust_id:
            return -1, "no permission", {}
        result = _withdraw.api_to_dict()

        # 客户银行卡信息
        _card = customer_card.Card.on_find_card_by_id(_withdraw.card_id)
        card_info = _card.to_dict()
        country_info = utils.find_country_by_code(card_info["bank_country_code"])
        card_info["country_info"] = country_info
        result["card_info"] = card_info
        if result["bm_payment_photo"]:
            result["bm_payment_photo"] = ["/w/" + x for x in result["bm_payment_photo"].split(",")]
        return 0, "success", result

    def register_new_withdraw(self, data):
        form = RegisterNewWithdrawForm.from_json(data)
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

        trade_password = utils.hash_password(form.data["trade_password"])
        if trade_password != cust.trade_password:
            return -1, "incorrect password", {}

        withdraw_type = cust.cust_type
        card_id = form.data["card_id"]
        amount = form.data["amount"]
        currency = form.data["currency"]
        company_id = cust.company_id
        note = form.data["note"]
        fee_proportion = 0.03
        fee_amount = 100.00

        can_withdraw = False
        for card in cust.wallet.cards:
            if card.card_id == card_id:
                can_withdraw = True
                break
        if not can_withdraw:
            return -1, "invalid bank card ", {}

        _withdraw = withdraw.Withdraw.on_register_new_withdraw(withdraw_type, cust_id, card_id, amount, currency,
                                                               company_id, fee_proportion, fee_amount, note)
        if not _withdraw:
            return -1, "failed", {}
        result = _withdraw.api_to_dict()

        # 客户银行卡信息
        _card = customer_card.Card.on_find_card_by_id(card_id)
        card_info = _card.to_dict()
        country_info = utils.find_country_by_code(card_info["bank_country_code"])
        card_info["country_info"] = country_info
        result["card_info"] = card_info
        if result["bm_payment_photo"]:
            result["bm_payment_photo"] = ["/w/" + x for x in result["bm_payment_photo"].split(",")]
        return 0, "success", result

    def list_withdraws(self, data):
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
        echo = form.data["sEcho"]
        state = form.data["state"]
        card_id = form.data["card_id"]
        finance_deal_state = form.data["finance_deal_state"]
        begin_date = form.data["begin_date"]
        end_date = form.data["end_date"]

        all_withdraws = withdraw.Withdraw.on_find_all_withdraws(None, None, cust_id, card_id, state, finance_deal_state,
                                                                begin_date, end_date)
        items = []
        for i in all_withdraws:
            withdraw_info = i.api_to_dict()
            # 客户银行卡信息
            _card = customer_card.Card.on_find_card_by_id(i.card_id)
            card_info = _card.to_dict()
            country_info = utils.find_country_by_code(card_info["bank_country_code"])
            card_info["country_info"] = country_info
            withdraw_info["card_info"] = card_info
            if withdraw_info["bm_payment_photo"]:
                withdraw_info["bm_payment_photo"] = ["/w/" + x for x in withdraw_info["bm_payment_photo"].split(",")]
            items.append(withdraw_info)
        result = {
            "sum": len(items),
            "sEcho": echo,
            "count": len(items[index:index + count]),
            "data": items[index:index + count]
        }
        return 0, "success", result
