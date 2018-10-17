import hashlib
import os
import time

import settings

_create_session_id = lambda: hashlib.sha1(bytes('%s%s' % (
    os.urandom(16), time.time()))).hexdigest()

class SessionFactory:

    @staticmethod
    def get_session(handler):
        session = None

        if settings.SESSION_TYPE == "cache":
            session = CacheSession(handler)
        return session


class CacheSession:
    session_container = {}
    session_id = "__session_id__"

    def __init__(self, handler):
        self.handler = handler
        client_random_str = handler.get_secure_cookie(CacheSession.session_id, None)
        if client_random_str and client_random_str in CacheSession.session_container:
            self.random_str = client_random_str
        else:
            self.random_str = _create_session_id()
            CacheSession.session_container[self.random_str] = {}

        expires_time = time.time() + settings.SESSION_EXPIRES
        handler.set_secure_cookie(CacheSession.session_id, self.random_str, expires=expires_time)

    def __getitem__(self, key):
        item = CacheSession.session_container[self.random_str].get(key, None)
        return item

    def __setitem__(self, key, value):
        CacheSession.session_container[self.random_str][key] = value

    def __delitem__(self, key):
        if key in CacheSession.session_container[self.random_str]:
            del CacheSession.session_container[self.random_str][key]
