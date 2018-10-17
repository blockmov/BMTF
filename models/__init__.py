from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import settings

DB = create_engine(settings.DATABASE_URI, echo=settings.DATABASE_DEBUG)
BaseModel = declarative_base()
# DBSession = sessionmaker(bind=DB, expire_on_commit=True)

class DBSession(object):
    def __new__(cls, *args, **kw):
        if not hasattr(cls, '_instance'):
            session = sessionmaker(bind=DB, expire_on_commit=True)
            cls._instance = session()
        return cls._instance


class MetaMixin(object):

    def __init__(self):
        super(MetaMixin, self).__init__()

    # def __repr__(self):
    #     raise NotImplementedError()

    def to_dict(self):
        raise NotImplementedError()

    @classmethod
    def insert(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def delete(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def select(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def update(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def count(cls):
        raise NotImplementedError()

