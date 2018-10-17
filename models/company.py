# coding: utf-8
import datetime
import logging
import decimal

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Time
from sqlalchemy.orm import relationship

from libs import json_encoder
from models import BaseModel
from models import DBSession
from models import MetaMixin


class Company(BaseModel, MetaMixin):
    """ BM公司
        company_id                  公司ID
        company_name                公司名称
        country                     国家
        city                        城市
        address                     地址
        timezone                    时区
        currency                    货币单位
        note                        备注
        state                       状态
                                            # 00：营业
                                            # 01：停业
                                            # 02：注销

        opening_hours               工作日上班时间
        opening_hours               工作日下班时间
        created_on                  创建时间
        updated_on                  更新时间
        admin_user_id               管理人员ID（User）
    """
    __tablename__ = "companies"

    company_id = Column(Integer(), primary_key=True, autoincrement=True)

    # 基本信息
    company_name = Column(String(100), nullable=False, unique=True)
    country = Column(String(40), nullable=False)
    city = Column(String(40), nullable=False)
    address = Column(String(100), nullable=False)
    timezone = Column(String(40), nullable=False)
    currency = Column(String(10), nullable=False)
    note = Column(String(200))

    # 状态
    # 00：营业
    # 01：关闭
    # 02：注销
    state = Column(String(2), nullable=False, default="01")

    # 营业时间
    opening_hours = Column(Time())
    closing_hours = Column(Time())

    created_on = Column(DateTime(), nullable=False, default=datetime.datetime.now)
    updated_on = Column(DateTime(), nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    admin_user_id = Column(Integer(), ForeignKey("users.user_id"), nullable=True)
    admin_user = relationship("User", uselist=False, foreign_keys=admin_user_id, lazy='subquery')

    def to_dict(self):
        return {
            "company_id": self.company_id,
            "company_name": self.company_name,
            "country": self.country,
            "city": self.city,
            "address": self.address,
            "timezone": self.timezone,
            "currency": self.currency,
            "note": self.note,
            "state": self.state,
            "opening_hours": json_encoder.help_to_json_str(self.opening_hours),
            "closing_hours": json_encoder.help_to_json_str(self.closing_hours),
            "created_on": json_encoder.help_to_json_str(self.created_on),
            "updated_on": json_encoder.help_to_json_str(self.updated_on),
            "admin_user_id": self.admin_user_id,
        }

    @classmethod
    def on_add_new_company(cls, company_name, country, city, address, timezone, currency, note):
        """ 添加新公司 """
        session = DBSession()
        com = cls()
        com.company_name = company_name
        com.country = country
        com.city = city
        com.address = address
        com.timezone = timezone
        com.currency = currency
        com.note = note
        try:
            session.add(com)
            session.commit()
        except Exception as why:
            session.rollback()
            message = "companies.on_add_new_company: {0}".format(why)
            logging.info(message)
            com = None
        return com

    @classmethod
    def on_set_state(cls, company_id, state):
        """ 设置公司状态 """
        if state not in ("00", "01", "02"):
            message = "companies.on_set_state: wrong state: {0}".format(state)
            logging.info(message)
            return -1

        session = DBSession()
        com = session.query(cls).filter(cls.company_id == company_id).first()
        if com:
            com.state = state
            try:
                session.add(com)
                session.commit()
            except Exception as why:
                message = "companies.on_set_state: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_set_admin_user(cls, company_id, user_id):
        """ 设置公司管理用户 """
        session = DBSession()
        com = session.query(cls).filter(cls.company_id == company_id).first()
        if com:
            com.admin_user_id = user_id
            try:
                session.add(com)
                session.commit()
            except Exception as why:
                session.rollback()
                message = "companies.on_set_admin_user: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_remove_admin_user(cls, company_id):
        """ 删除公司管理员用户 """
        session = DBSession()
        com = session.query(cls).filter(cls.company_id == company_id).first()
        if com:
            com.admin_user_id = None
            try:
                session.add(com)
                session.commit()
            except Exception as why:
                message = "companies.on_remove_admin_user: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_set_business_hours(cls, company_id, opening_hours, closing_hours):
        """ 设置公司营业时间 """
        session = DBSession()
        com = session.query(cls).filter(cls.company_id == company_id).first()
        if com:
            com.opening_hours = opening_hours
            com.closing_hours = closing_hours
            try:
                session.add(com)
                session.commit()
            except Exception as why:
                session.rollback()
                message = "companies.on_set_business_hours: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_set_base_info(cls, company_id, company_name=None, country=None, city=None, address=None, timezone=None,
                         currency=None, note=None):
        """ 设置公司基础信息 """
        session = DBSession()
        com = session.query(cls).filter(cls.company_id == company_id).first()
        if com:
            if company_name:
                com.company_name = company_name
            if country:
                com.country = country
            if city:
                com.city = city
            if address:
                com.address = address
            if timezone:
                com.timezone = timezone
            if currency:
                com.currency = currency
            if note:
                com.note = note
            try:
                session.add(com)
                session.commit()
            except Exception as why:
                session.rollback()
                message = "companies.on_set_base_info: {0}".format(why)
                logging.info(message)
                return -1
        return 0

    @classmethod
    def on_find_company_by_name(cls, company_name):
        session = DBSession()
        try:
            com = session.query(cls).filter(cls.company_name == company_name).first()
        except Exception as why:
            message = "companies.on_find_company_by_name: {0}".format(why)
            logging.info(message)
            com = None
        return com

    @classmethod
    def on_find_company_by_id(cls, company_id):
        session = DBSession()
        try:
            com = session.query(cls).filter(cls.company_id == company_id).first()
        except Exception as why:
            message = "companies.on_find_company_by_id: {0}".format(why)
            logging.info(message)
            com = None
        return com

    @classmethod
    def on_get_all_bank_cards_amount(cls, company_id):
        """ 获取公司所有银行卡总余额 """
        session = DBSession()
        try:
            com = session.query(cls).filter(cls.company_id == company_id).first()
            amount = decimal.Decimal(0.0)
            for card in com.bank_cards:
                # 过滤已注销的银行卡
                if card.state != "02":
                    amount += card.amount
        except Exception as why:
            message = "companies.on_get_all_bank_cards_amount: {0}".format(why)
            logging.info(message)
            amount = decimal.Decimal(0.0)
        return amount

    @classmethod
    def on_list_all(cls,):
        session = DBSession()
        try:
            items = session.query(cls).all()
        except Exception as why:
            message = "companies.on_list_all: {0}".format(why)
            logging.info(message)
            items = []
        return items
