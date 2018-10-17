# coding: utf-8
import logging

import tornado.escape
from libs import memery_cache

from handlers import base
from libs.captcha.captcha import gen_captcha


class CaptchaHandler(base.BaseHandler):

    def get(self):
        device_id = self.get_argument("device_id", None)

        text, img = gen_captcha(120, 50)
        self.set_header("Content-Type", "image/gif")
        self.write(img)
        if device_id:
            memery_cache.MemCaptchaSet.set_captcha(device_id, text.lower())
