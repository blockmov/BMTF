# coding: utf-8
import datetime
import logging

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Numeric
from sqlalchemy import String
from sqlalchemy import and_
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship

from libs import json_encoder
from models import BaseModel
from models import DBSession
from models import MetaMixin


class BankCard(BaseModel, MetaMixin):
    """ 银行卡信息
        说明：
            card_id                 银行卡ID
            card_name               账户名
            card_number             卡号
            bank_swift_code         银行编码
            bank_address            银行地址
            bank_name               银行名称
            bank_address            地址

            state                   状态
                                        # 00：正常
                                        # 01：冻结
                                        # 02：注销

            balance                 账户余额
            currency                货币
            amount                  总金额
            deposit_amount          累计入账
            withdrawal_amount       累计出账
            refund_amount           累计退款
            turnover_amount         累计交易额


    """
    __tablename__ = "company_cards"

    card_id = Column(Integer(), primary_key=True, autoincrement=True)
    company_id = Column(Integer(), ForeignKey("companies.company_id"), nullable=False)

    # 银行卡信息
    card_name = Column(String(255), nullable=False)
    card_number = Column(String(100), nullable=False)

    # 银行信息
    bank_swift_code = Column(String(100), nullable=False)
    bank_name = Column(String(255), nullable=False)
    bank_address = Column(String(255), nullable=False)

    balance = Column(Numeric(20, 2), nullable=False, default=0.00)
    currency = Column(String(10), nullable=False)
    amount = Column(Numeric(20, 2), nullable=False, default=0.00)
    # deposit_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    # withdrawal_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    # refund_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    # turnover_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    state = Column(String(2), nullable=False, default="00")

    created_on = Column(DateTime(), nullable=False, default=datetime.datetime.now)
    updated_on = Column(DateTime(), nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    company = relationship("Company", backref=backref("bank_cards", order_by=card_id, lazy='subquery'))

    def to_dict(self):
        return {
            "card_id": self.card_id,
            "card_name": self.card_name,
            "card_number": self.card_number,
            "bank_swift_code": self.bank_swift_code,
            "bank_name": self.bank_name,
            "bank_address": self.bank_address,
            # "balance": json_encoder.help_to_json_str(self.balance),
            "currency": self.currency,
            "amount": json_encoder.help_to_json_str(self.amount),
            # "deposit_amount": self.deposit_amount,
            # "withdrawal_amount": self.withdrawal_amount,
            # "refund_amount": self.refund_amount,
            # "turnover_amount": self.turnover_amount,
            "state": self.state,
            "created_on": json_encoder.help_to_json_str(self.created_on),
            "updated_on": json_encoder.help_to_json_str(self.updated_on),
            "company_id": self.company_id,
        }

    @classmethod
    def on_add_new_bank_card(cls, company_id, card_name, card_number, bank_swift_code, bank_name, bank_address,
                             currency, amount):
        """ 添加银行卡"""
        session = DBSession()
        card = cls()
        card.company_id = company_id
        card.card_name = card_name
        card.card_number = card_number
        card.bank_swift_code = bank_swift_code
        card.bank_name = bank_name
        card.bank_address = bank_address
        card.currency = currency
        card.amount = amount
        try:
            session.add(card)
            session.commit()
        except Exception as why:
            session.rollback()
            message = "bank_cards.on_add_new_bank_card: {0}".format(why)
            logging.info(message)
            card = None
        return card

    @classmethod
    def on_set_state(cls, card_id, state):
        """ 设置公司状态 """
        if state not in ("00", "01", "02"):
            message = "bank_cards.on_set_state: wrong state: {0}".format(state)
            logging.info(message)
            return -1

        session = DBSession()
        card = session.query(cls).filter(cls.card_id == card_id).first()
        if card:
            card.state = state
            try:
                session.add(card)
                session.commit()
            except Exception as why:
                session.rollback()
                message = "bank_cards.on_set_state: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_set_base_info(cls, card_id, company_id=None, card_name=None, card_number=None, bank_swift_code=None,
                         bank_name=None, bank_address=None, currency=None, amount=None):
        """ 修改银行卡信息"""
        session = DBSession()
        card = session.query(cls).filter(cls.card_id == card_id).first()
        if card:
            if company_id:
                card.company_id = company_id
            if card_name:
                card.card_name = card_name
            if card_number:
                card.card_number = card_number
            if bank_swift_code:
                card.bank_swift_code = bank_swift_code
            if bank_name:
                card.bank_name = bank_name
            if bank_address:
                card.bank_address = bank_address
            if currency:
                card.currency = currency
            if amount is not None:
                card.amount = amount
            try:
                session.add(card)
                session.commit()
            except Exception as why:
                message = "bank_cards.on_set_base_info: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_find_bank_card_by_id(cls, card_id):
        session = DBSession()
        try:
            card = session.query(cls).filter(cls.card_id == card_id).first()
        except Exception as why:
            message = "bank_cards.on_find_bank_card_by_id: {0}".format(why)
            logging.info(message)
            card = None
        return card

    @classmethod
    def on_list_all(cls, company_id=None, state=None):
        session = DBSession()
        try:
            q = session.query(cls)
            if company_id:
                q = q.filter(and_(cls.company_id == company_id))
            if state:
                q = q.filter(and_(cls.state == state))
            items = q
        except Exception as why:
            message = "bank_cards.on_list_all_bank_cards: {0}".format(why)
            logging.info(message)
            items = []
        return items
