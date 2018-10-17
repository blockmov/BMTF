# coding:utf-8
import datetime
import logging

from models import BaseModel
from models import DBSession

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from sqlalchemy import func

from libs import json_encoder

class Action(BaseModel):
    '''
    系统所有请求URL
    '''
    __tablename__ = 'actions'

    id = Column(Integer(), primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False, unique=False)
    url = Column(String(256), nullable=False, unique=True)
    created_on = Column(DateTime(), default=datetime.datetime.now)
    updated_on = Column(DateTime(), default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def __init__(self, name, url):
        self.name = name
        self.url = url

    def __repr__(self):
        return '<Action(id=%s, name=%s, url=%s)>' % (self.id, self.name, self.url)

    def to_dict(self):
        return {
            'action_id': self.id,
            'name': self.name,
            'url': self.url,
            "created_on": json_encoder.help_to_json_str(self.created_on),
            "updated_on": json_encoder.help_to_json_str(self.updated_on)
        }

    @classmethod
    def add(cls, name, url):
        ret = True
        session = DBSession()
        record = Action(name, url)
        session.add(record)
        try:
            session.commit()
            session.close()
            logging.info('add action success<name=%s, url=%s>' % (name, url))
        except IntegrityError as error:
            logging.error(str(error))
            ret = False

        return ret

    @classmethod
    def edit(cls, id, name=None, url=None):
        ret = True
        session = DBSession()
        action = session.query(Action).filter(Action.id == id).first()
        if not action:
            logging.error('not fount action<id=%s>' % id)
            return False
        if name:
            action.name = name
        if url:
            action.offset = url
        try:
            session.commit()
            logging.info('edit action success<id=%s, name=%s, url=%s>' % (action.id, action.name, action.url))
            session.close()
        except IntegrityError as error:
            logging.error(str(error))
            ret = False

        return ret

    @classmethod
    def fetch_all(cls):
        session = DBSession()
        actions = session.query(Action).all()
        session.close()
        actions = [action.to_dict() for action in actions]
        return actions

    @classmethod
    def fetch_action(cls, id):
        try:
            session = DBSession()
            action = session.query(Action).filter(Action.id == id).first()
            session.close()
        except IntegrityError as error:
            logging.error(error)
            return {}

        return action.to_dict()

    @classmethod
    def url_exist(cls, url):
        try:
            session = DBSession()
            actions = session.query(Action).filter(Action.url == url).all()
            session.close()
            if actions:
                return True

        except IntegrityError as error:
            logging.error(error)
            return False

        return False

    @classmethod
    def update_action_exist(cls, id, url):
        try:
            session = DBSession()
            actions = session.query(Action).filter(Action.url == url).filter(Action.id != id).all()
            session.close()
            if actions:
                return True
        except IntegrityError as error:
            logging.error(error)
            return False

        return False

    @classmethod
    def fetch_filter(cls, start_index, count, keywords, sort_field, sort_method):
        try:
            session = DBSession()
            _sort = cls._sort_field(sort_field, sort_method)
            if keywords:
                keywords = unicode("%{0}%".format(keywords.encode('utf-8')), "utf-8")
            else:
                keywords = "%"

            _condition = or_(Action.name.like(keywords), Action.url.like(keywords))
            _action = session.query(Action).filter(_condition)
            actions = _action.order_by(_sort).limit(count).offset(start_index).all()
            total = _action.with_entities(func.count(Action.id)).scalar()
            session.close()
        except IntegrityError as error:
            print error
            logging.error(error)
            return {}

        return total, [action.to_dict() for action in actions]

    @classmethod
    def delete(cls, id):
        ret = True
        session = DBSession()
        actions = session.query(Action).filter(Action.id == id).all()
        if actions:
            try:
                session.delete(actions[0])
                session.commit()
                session.close()
            except IntegrityError as error:
                logging.error(error)
                ret = False
        else:
            logging.error('Action not found')
            ret = False

        return ret

    @classmethod
    def _sort_field(cls, sort_field, sort_method):
        if sort_field == "name":
            if sort_method == "desc":
                _sort = Action.name.desc()
            else:
                _sort = Action.name.asc()

        elif sort_field == "url":
            if sort_method == "desc":
                _sort = Action.url.desc()
            else:
                _sort = Action.url.asc()

        elif sort_field == "created_on":
            if sort_method == "desc":
                _sort = Action.created_on.desc()
            else:
                _sort = Action.created_on.asc()

        elif sort_field == "updated_on":
            if sort_method == "desc":
                _sort = Action.updated_on.desc()
            else:
                _sort = Action.updated_on.asc()

        else:
            _sort = Action.id.asc()

        return _sort