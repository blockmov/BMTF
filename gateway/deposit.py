# coding: utf-8
import imghdr
import logging
import os
import uuid

import tornado.escape
from wtforms.fields import DateField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms_tornado import Form

from handlers import base
from models import customer
from models import deposit
from libs import memery_cache as mc
import const
from libs import utils


class GetInfoForm(Form):
    token = StringField("token", validators=[DataRequired()])
    deposit_id = IntegerField("deposit_id", validators=[DataRequired()])


class RegisterNewDepositForm(Form):
    token = StringField("token", validators=[DataRequired()])
    bank_name = StringField("bank_name", validators=[DataRequired()])
    swift_code = StringField("swift_code", validators=[DataRequired()])
    bank_card_name = StringField("bank_card_name", validators=[DataRequired()])
    bank_card_number = StringField("bank_card_number", validators=[DataRequired()])
    amount = StringField("amount", validators=[DataRequired()], )
    currency = StringField("currency", validators=[DataRequired()])
    payment_date = DateField("payment_date", validators=[DataRequired()])
    # credence_photo = StringField("credence_photo", validators=[DataRequired()])
    note = StringField("note", validators=[])
    bm_card_id = StringField("bm_card_id", validators=[DataRequired()])
    bm_card_name = StringField("bm_card_name", validators=[DataRequired()])
    bm_card_number = StringField("bm_card_number", validators=[DataRequired()])
    bm_bank_swift_code = StringField("bm_bank_swift_code", validators=[DataRequired()])
    bm_bank_name = StringField("bm_bank_name", validators=[DataRequired()])
    bm_bank_address = StringField("bm_bank_address", validators=[DataRequired()])
    trade_password = StringField("trade_password", validators=[DataRequired()])


class CancelForm(Form):
    token = StringField("token", validators=[DataRequired()])
    deposit_id = IntegerField("deposit_id", validators=[DataRequired()])


class ListForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField("index", validators=[DataRequired()])
    count = IntegerField("count", validators=[DataRequired()])
    state = StringField("state")
    agent_deal_state = StringField("agent_deal_state")
    finance_deal_state = StringField("finance_deal_state")
    begin_date = DateField("begin_date")
    end_date = DateField("end_date")


class DepositHandler(base.BaseHandler):
    """ 充值管理 """

    def put(self):
        try:
            method = self.get_body_argument("method", None)
            params = tornado.escape.json_decode(self.get_body_argument("params", None))
        except Exception as why:
            code, message, result = -1, "data format error", {}
        else:
            if method == "register_new_deposit":
                code, message, result = self.register_new_deposit(params)
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
            if method == "get_deposit_info":
                code, message, result = self.get_deposit_info(params)
            elif method == "list_deposits":
                code, message, result = self.list_deposits(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def get_deposit_info(self, data):
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

        deposit_id = form.data["deposit_id"]
        _deposit = deposit.Deposit.on_find_deposit_by_deposit_id(deposit_id)
        if not _deposit:
            return -1, "failed", {}
        if _deposit.cust_id != cust_id:
            return -1, "no permission", {}
        result = _deposit.api_to_dict()
        if result["credence_photo"]:
            result["credence_photo"] = ["/d/" + x for x in result["credence_photo"].split(",")]
        return 0, "success", result

    def register_new_deposit(self, data):
        form = RegisterNewDepositForm.from_json(data)
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

        # step 1, 处理图片资料
        upload_path = const.DEPOSIT_FILE_PATH
        file_metas = self.request.files.get("credence_photo", None)
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
                new_file_path = "{}".format(os.path.join(const.DEPOSIT_FILE_PATH, filename))
                os.rename(file_path, new_file_path)
                filelist.append(filename)
            except Exception as why:
                logging.error(why)
                return -1, "failed: something wrong on server", {}

        # step 2, 处理文字资料
        form = RegisterNewDepositForm.from_json(data)
        if not form.validate():
            return -1, str(form.errors), {}

        trade_password = utils.hash_password(form.data["trade_password"])
        if trade_password != cust.trade_password:
            return -1, "incorrect password", {}

        # step 4, 创建充值单
        cust_type = cust.cust_type
        cust_first_name = cust.cust_first_name
        cust_last_name = cust.cust_last_name

        bank_name = form.data["bank_name"]
        swift_code = form.data["swift_code"]
        bank_card_name = form.data["bank_card_name"]
        bank_card_number = form.data["bank_card_number"]
        amount = form.data["amount"]
        currency = form.data["currency"]
        payment_date = form.data["payment_date"]
        credence_photo = ",".join(filelist)
        note = form.data["note"]

        company_id = cust.company_id
        company_name = cust.company.company_name

        bm_card_id = form.data["bm_card_id"]
        bm_card_name = form.data["bm_card_name"]
        bm_card_number = form.data["bm_card_number"]
        bm_bank_swift_code = form.data["bm_bank_swift_code"]
        bm_bank_name = form.data["bm_bank_name"]
        bm_bank_address = form.data["bm_bank_address"]

        _deposit = deposit.Deposit.on_register_new_deposit(cust_id, cust_type, cust_first_name, cust_last_name,
                                                           bank_name, swift_code, bank_card_name, bank_card_number,
                                                           amount, currency, payment_date, credence_photo,
                                                           company_id,
                                                           company_name, bm_card_id, bm_card_name, bm_card_number,
                                                           bm_bank_swift_code, bm_bank_name, bm_bank_address, note)
        if not _deposit:
            logging.info("register new deposit failed")
            return -1, "failed", {}
        result = _deposit.api_to_dict()
        if result["credence_photo"]:
            result["credence_photo"] = ["/d/" + x for x in result["credence_photo"].split(",")]
        return 0, "success", result

    def list_deposits(self, data):
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
        agent_deal_state = form.data["agent_deal_state"]
        finance_deal_state = form.data["finance_deal_state"]
        begin_date = form.data["begin_date"]
        end_date = form.data["end_date"]

        all_deposits = deposit.Deposit.on_find_all_deposits(company_id=None, bm_card_id=None, cust_id=cust_id,
                                                            state=state, agent_deal_state=agent_deal_state,
                                                            finance_deal_state=finance_deal_state,
                                                            begin_date=begin_date, end_date=end_date)
        items = [i.api_to_dict() for i in all_deposits]
        for i in items:
            if i["credence_photo"]:
                i["credence_photo"] = ["/d/" + x for x in i["credence_photo"].split(",")]
        result = {
            "sum": len(items),
            "count": len(items[index:index + count]),
            "data": items[index:index + count]
        }
        return 0, "success", result
