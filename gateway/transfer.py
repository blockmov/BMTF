# coding: utf-8
import os
import uuid
import logging
import imghdr

import tornado.escape
from wtforms.fields import DateField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms_tornado import Form

from handlers import base
from models import customer
from models import customer_card
from models import customer_contact
from models import customer_message
from models import customer_wallet
from models import transfer
from libs import memery_cache as mc
from libs import utils
import const


class GetInfoForm(Form):
    token = StringField("token", validators=[DataRequired()])
    transfer_id = IntegerField("transfer_id", validators=[DataRequired()])


class RegisterNewTransferForm(Form):
    token = StringField("token", validators=[DataRequired()])
    amount = StringField("amount", validators=[DataRequired()], )
    currency = StringField("currency", validators=[DataRequired()])
    note = StringField("note", validators=[])
    dst_contact_id = StringField("dst_contact_id", validators=[DataRequired()])
    dst_bank_card_name = StringField("dst_bank_card_name", validators=[DataRequired()])
    dst_bank_card_number = StringField("dst_bank_card_number", validators=[DataRequired()])
    dst_bank_swift_code = StringField("dst_bank_swift_code", validators=[DataRequired()])
    dst_bank_name = StringField("dst_bank_name", validators=[DataRequired()])
    dst_bank_city = StringField("dst_bank_city", validators=[DataRequired()])
    dst_bank_country = StringField("dst_bank_country", validators=[DataRequired()])
    dst_bank_address = StringField("dst_bank_address", validators=[DataRequired()])
    trade_password = StringField("trade_password", validators=[DataRequired()])


class ListForm(Form):
    token = StringField("token", validators=[DataRequired()])
    index = IntegerField("index", validators=[DataRequired()])
    count = IntegerField("count", validators=[DataRequired()])
    sEcho = IntegerField("sEcho")
    state = IntegerField("state")
    dst_contact_id = IntegerField("dst_contact_id")
    begin_date = DateField("begin_date", validators=[])
    end_date = DateField("end_date", validators=[])


class TransferHandler(base.BaseHandler):
    """ 转账 """

    def put(self):
        try:
            method = self.get_body_argument("method", None)
            params = tornado.escape.json_decode(self.get_body_argument("params", None))
        except Exception as why:
            logging.info(why)
            code, message, result = -1, "data format error", {}
        else:
            if method == "register_new_transfer":
                code, message, result = self.register_new_transfer(params)
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
            if method == "get_transfer_info":
                code, message, result = self.get_transfer_info(params)
            elif method == "list_transfers":
                code, message, result = self.list_transfers(params)
            else:
                code, message, result = -1, "no permission", {}
        self.send_json_response(code, message, result)

    def get_transfer_info(self, data):
        form = GetInfoForm.from_json(data)
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

        transfer_id = form.data["transfer_id"]
        _transfer = transfer.Transfer.on_find_transfer_by_transfer_id(transfer_id)
        if not _transfer:
            return -1, "failed", {}
        if _transfer.cust_id != cust_id:
            return -1, "no permission", {}
        contact_info = {}
        if _transfer.dst_contact_id:
            _contact = customer_contact.Contact.on_find_contact_by_id(_transfer.dst_contact_id)
            if _contact:
                contact_info = _contact.to_dict()
        dst_bank_country_info = utils.find_country_by_code(_transfer.dst_bank_country_code)
        result = _transfer.api_to_dict()
        result["contact_info"] = contact_info
        result["dst_bank_country_info"] = dst_bank_country_info
        if result["upload_business_contract"]:
            result["upload_business_contract"] = ["/t/" + i for i in result["upload_business_contract"].split(",")]
        if result["upload_invoice"]:
            result["upload_invoice"] = ["/t/" + i for i in result["upload_invoice"].split(",")]
        if result["upload_receipt_form"]:
            result["upload_receipt_form"] = ["/t/" + i for i in result["upload_receipt_form"].split(",")]
        if result["dst_bm_payment_photo"]:
            result["dst_bm_payment_photo"] = ["/t/" + i for i in result["dst_bm_payment_photo"].split(",")]
        return 0, "success", result

    def register_new_transfer(self, data):
        form = RegisterNewTransferForm.from_json(data)
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

        trade_password = utils.hash_password(form.data["trade_password"])
        if trade_password != cust.trade_password:
            return -1, "incorrect password", {}

        company_id = cust.company_id
        transfer_type = cust.cust_type
        amount = form.data["amount"]
        currency = form.data["currency"]
        note = form.data["note"]

        dst_contact_id = form.data["dst_contact_id"]
        dst_bank_card_name = form.data["dst_bank_card_name"]
        dst_bank_card_number = form.data["dst_bank_card_number"]
        dst_bank_swift_code = form.data["dst_bank_swift_code"]
        dst_bank_name = form.data["dst_bank_name"]
        dst_bank_city = form.data["dst_bank_city"]
        dst_bank_country = form.data["dst_bank_country"]
        dst_bank_address = form.data["dst_bank_address"]

        _country = utils.find_country_by_name(dst_bank_country)
        if not _country:
            return -1, "invalid country", {}
        dst_bank_country_code = _country["alpha_2"]

        # 检查联系人是否正确
        can_do_transfer = False
        if dst_contact_id:
            _contact = customer_contact.Contact.on_find_contact_by_id(dst_contact_id)
            if _contact and _contact.cust_id == cust_id:
                can_do_transfer = True
        if not can_do_transfer:
            return -1, "invalid contact", {}

        # TODO: 检查银行卡信息

        # TODO: 检查交易合法性

        # TODO: 扫描件
        upload_business_contract_filelist = []
        upload_invoice_filelist = []
        upload_receipt_form_filelist = []
        upload_path = const.TRANSFER_FILE_PATH
        for upload_type in ("upload_business_contract", "upload_invoice", "upload_receipt_form"):
            file_metas = self.request.files.get(upload_type, None)
            if not file_metas:
                return -1, "failed: no image files", {}

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
                    new_file_path = "{}".format(os.path.join(const.TRANSFER_FILE_PATH, filename))
                    os.rename(file_path, new_file_path)
                except Exception as why:
                    logging.error(why)
                    return -1, "failed: something wrong on server", {}
                if upload_type == "upload_business_contract":
                    upload_business_contract_filelist.append(filename)
                elif upload_type == "upload_invoice":
                    upload_invoice_filelist.append(filename)
                else:
                    upload_receipt_form_filelist.append(filename)
        upload_business_contract = ",".join(upload_business_contract_filelist)
        upload_invoice = ",".join(upload_invoice_filelist)
        upload_receipt_form = ",".join(upload_receipt_form_filelist)
        fee_proportion = 0.038
        fee_amount = 14089.00
        _transfer = transfer.Transfer.on_register_new_transfer(company_id, transfer_type, cust_id, amount, currency,
                                                               note, dst_contact_id, dst_bank_card_name,
                                                               dst_bank_card_number, dst_bank_swift_code,
                                                               dst_bank_name,
                                                               dst_bank_country_code, dst_bank_city,
                                                               dst_bank_address,
                                                               upload_business_contract, upload_invoice,
                                                               upload_receipt_form, fee_proportion, fee_amount)
        if not _transfer:
            return -1, "failed", {}
        contact_info = {}
        if _transfer.dst_contact_id:
            _contact = customer_contact.Contact.on_find_contact_by_id(_transfer.dst_contact_id)
            if _contact:
                contact_info = _contact.to_dict()
        dst_bank_country_info = utils.find_country_by_code(_transfer.dst_bank_country_code)

        result = _transfer.api_to_dict()
        result["contact_info"] = contact_info
        result["dst_bank_country_info"] = dst_bank_country_info
        if result["upload_business_contract"]:
            result["upload_business_contract"] = ["/t/" + i for i in result["upload_business_contract"].split(",")]
        if result["upload_invoice"]:
            result["upload_invoice"] = ["/t/" + i for i in result["upload_invoice"].split(",")]
        if result["upload_receipt_form"]:
            result["upload_receipt_form"] = ["/t/" + i for i in result["upload_receipt_form"].split(",")]
        if result["dst_bm_payment_photo"]:
            result["dst_bm_payment_photo"] = ["/t/" + i for i in result["dst_bm_payment_photo"].split(",")]
        return 0, "success", result

    def list_transfers(self, data):
        form = ListForm.from_json(data)
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

        index = form.data["index"] - 1
        count = form.data["count"]
        dst_contact_id = form.data["dst_contact_id"]
        state = form.data["state"]
        begin_date = form.data["begin_date"]
        end_date = form.data["end_date"]
        company_id = cust.company_id
        bm_card_id = None
        agent_deal_state = None
        finance_deal_state = None
        dst_finance_deal_state = None

        all_transfers = transfer.Transfer.on_find_all_transfers(company_id, bm_card_id, cust_id, dst_contact_id, state,
                                                                agent_deal_state, finance_deal_state,
                                                                dst_finance_deal_state, begin_date, end_date)
        items = []
        for i in all_transfers:
            transfer_info = i.api_to_dict()
            contact_info = {}
            if i.dst_contact_id:
                _contact = customer_contact.Contact.on_find_contact_by_id(i.dst_contact_id)
                if _contact:
                    contact_info = _contact.to_dict()

            dst_bank_country_info = utils.find_country_by_code(i.dst_bank_country_code)
            transfer_info["contact_info"] = contact_info
            transfer_info["dst_bank_country_info"] = dst_bank_country_info
            if transfer_info["upload_business_contract"]:
                transfer_info["upload_business_contract"] = ["/t/" + i for i in
                                                             transfer_info["upload_business_contract"].split(",")]
            if transfer_info["upload_invoice"]:
                transfer_info["upload_invoice"] = ["/t/" + i for i in
                                                   transfer_info["upload_invoice"].split(",")]
            if transfer_info["upload_receipt_form"]:
                transfer_info["upload_receipt_form"] = ["/t/" + i for i in
                                                        transfer_info["upload_receipt_form"].split(",")]
            if transfer_info["dst_bm_payment_photo"]:
                transfer_info["dst_bm_payment_photo"] = ["/t/" + i for i in
                                                         transfer_info["dst_bm_payment_photo"].split(",")]
            items.append(transfer_info)
        result = {
            "sum": len(items),
            "count": len(items[index:index + count]),
            "data": items[index:index + count]
        }
        return 0, "success", result
