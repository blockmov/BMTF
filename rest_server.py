# coding: utf-8
import logging
import logging.handlers
import os
import ssl
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.options
import tornado.web
from tornado.web import StaticFileHandler
from tornado.log import access_log
from tornado.options import define
from tornado.options import options
from tornado.web import url

import models.all

# handlers
from gateway import auth
from gateway import fee
from gateway import contacts
from gateway import profile
from gateway import wallet
from gateway import deposit
from gateway import withdraw
from gateway import transfer
from gateway import public
from gateway import register
from gateway import security
from gateway import captcha
from gateway import resource
from gateway import message

import const

reload(sys)
sys.setdefaultencoding('utf-8')

# Options
define("host", default="0.0.0.0", help="run on the given host", type=str)
define("port", default=8060, help="run on the given port", type=int)
define("debug", default=True, type=bool)


def log_init(logfile, force_ground=False, debug_mode=True):
    access_handler = logging.handlers.RotatingFileHandler("log/cbs_rest_access.log", maxBytes=10 * 1024 * 1024,
                                                          backupCount=10)
    access_log.propagate = False
    access_log.addHandler(access_handler)

    logger = logging.getLogger()
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = tornado.log.LogFormatter()
    # formatter = logging.Formatter("%(asctime)-25s %(levelname)-8s %(filename)s:%(lineno)d %(message)s")
    handler = logging.handlers.RotatingFileHandler(logfile, maxBytes=10 * 1024 * 1024, backupCount=10)
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    if force_ground:
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    tornado.log.enable_pretty_logging(logger=logger)


class Application(tornado.web.Application):

    def __init__(self, options):
        settings = {
            "static_path": os.path.join(os.path.dirname(__file__), "static"),
            "template_path": os.path.join(os.path.dirname(__file__), "templates"),
            "cookie_secret": "aZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
            "xsrf_cookies": False,
            "autoreload": False
        }
        urls = [
            # cbs
            url(r"/i/(.*)", StaticFileHandler, {"path": const.IDENTITY_FILE_PATH}),
            url(r"/d/(.*)", tornado.web.StaticFileHandler, {"path": const.DEPOSIT_FILE_PATH}),
            url(r"/w/(.*)", tornado.web.StaticFileHandler, {"path": const.WITHDRAW_FILE_PATH}),
            url(r"/t/(.*)", tornado.web.StaticFileHandler, {"path": const.TRANSFER_FILE_PATH}),
            url(r"/avatar/(.*)", tornado.web.StaticFileHandler, {"path": const.AVATAR_FILE_PATH}),
            url(r"/flags/(.*)", tornado.web.StaticFileHandler, {"path": const.FLAGS_FILE_PATH}),
            url(r"/resource", resource.ResourceHandler, name="resource"),
            url(r"/auth/(login|logout)", auth.AuthHandler),
            url(r"/cbs/register", register.RegisterHandler),
            url(r"/cbs/security", security.SecurityHandler),
            url(r"/cbs/fee", fee.FeeHandler),
            url(r"/cbs/contact", contacts.ContactHandler),
            url(r"/cbs/profile", profile.ProfileHandler),
            url(r"/cbs/wallet", wallet.WalletHandler),
            url(r"/cbs/deposit", deposit.DepositHandler),
            url(r"/cbs/withdraw", withdraw.WithdrawHandler),
            url(r"/cbs/transfer", transfer.TransferHandler),
            url(r"/cbs/public", public.PublicHandler),
            url(r"/cbs/message", message.MessageHandler),
            url(r"/captcha.gif", captcha.CaptchaHandler),

        ]
        tornado.web.Application.__init__(self, urls, **settings)


def main():
    log_init("log/cbs_rest_server.log", True, True)

    tornado.options.parse_command_line()
    logging.basicConfig(level=logging.DEBUG)

    # ssl
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain("data/cbs_cert.crt", "data/cbs_private.key")
    http_server = tornado.httpserver.HTTPServer(Application(options), ssl_options=ssl_ctx)
    logging.info("Starting server at http://{0}:{1}/".format(options.host, options.port))
    try:
        http_server.listen(options.port, options.host)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as why:
        logging.error(str(why))
    finally:
        http_server.stop()
        tornado.ioloop.IOLoop.instance().stop()


if __name__ == "__main__":
    main()
