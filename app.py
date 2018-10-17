# coding: utf-8
import logging
import logging.handlers
import decimal
import os
import ssl
import sys

import tornado.httpserver
import tornado.ioloop
import tornado.log
import tornado.options
import tornado.web
from tornado.log import access_log
from tornado.options import define
from tornado.options import options
from tornado.web import url

from handlers import resource
from handlers import common

from handlers.backend import login as backend_login
from handlers.backend import logout as backend_logout
from handlers.backend import message as backend_message
from handlers.backend import file as backend_file
from handlers.backend import admin

# handlers
from handlers.cbs import contacts as cbs_contacts, index
from handlers.cbs import deposit as cbs_deposit
from handlers.cbs import withdraw as cbs_withdraw
from handlers.cbs import transfer as cbs_transfer
from handlers.cbs import fee as cbs_fee
from handlers.cbs import auth as cbs_auth
from handlers.cbs import main as cbs_main
from handlers.cbs import profile as cbs_profile
from handlers.cbs import register as cbs_register
from handlers.cbs import public as cbs_public
from handlers.cbs import wallet as cbs_wallet
from handlers.cbs import security as cbs_security
from handlers.cbs import message as cbs_message
from handlers.cbs import captcha as cbs_captcha

import const
import settings

reload(sys)
sys.setdefaultencoding('utf-8')
decimal.getcontext().prec = 6

# Options
define("host", default="0.0.0.0", help="run on the given host", type=str)
define("port", default=8000, help="run on the given port", type=int)
define("debug", default=True, type=bool)


def log_init(logfile, force_ground=False, debug_mode=True):
    access_handler = logging.handlers.RotatingFileHandler("log/cbs_access.log", maxBytes=10 * 1024 * 1024,
                                                          backupCount=10)
    access_log.propagate = False
    access_log.addHandler(access_handler)

    logger = logging.getLogger()
    if debug_mode:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    formatter = tornado.log.LogFormatter()
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
            "login_url": "/cbs/login",
            "autoreload": False
        }
        urls = [
            url(r"/static/(.*)", tornado.web.StaticFileHandler, dict(path=settings["static_path"])),
            url(r"/i/(.*)", tornado.web.StaticFileHandler, {"path": const.IDENTITY_FILE_PATH}),
            url(r"/d/(.*)", tornado.web.StaticFileHandler, {"path": const.DEPOSIT_FILE_PATH}),
            url(r"/w/(.*)", tornado.web.StaticFileHandler, {"path": const.WITHDRAW_FILE_PATH}),
            url(r"/t/(.*)", tornado.web.StaticFileHandler, {"path": const.TRANSFER_FILE_PATH}),
            url(r"/avatar/(.*)", tornado.web.StaticFileHandler, {"path": const.AVATAR_FILE_PATH}),
            url(r"/flags/(.*)", tornado.web.StaticFileHandler, {"path": const.FLAGS_FILE_PATH}),
            url(r"/captcha.gif", cbs_captcha.CaptchaHandler, name="cbs_captcha"),
            url(r"/resource", resource.ResourceHandler, name="resource"),
            url(r"/common/(.*)", common.CommonHandler, name="common"),

            url(r"/", index.IndexHandler, name="index"),

            # backend
            url(r"/backend", backend_login.LoginHandler),
            url(r"/backend/login", backend_login.LoginHandler),
            url(r"/backend/logout", backend_logout.LogoutHandler),
            url(r"/backend/message", backend_message.MessageHandler),
            url(r"/backend/file", backend_file.FileHandler),

            url(r"/backend/dashboard", admin.dashboard.DashboardHandler),
            url(r"/backend/role", admin.role.RoleHandler),
            url(r"/backend/company", admin.company.CompanyHandler),
            url(r"/backend/user", admin.user.UserHandler),
            url(r"/backend/bankcard", admin.bank_card.BankCardHandler),
            url(r"/backend/customer", admin.customer.CustomerHandler),
            url(r"/backend/fee", admin.fee.FeeHandler),
            url(r"/backend/deposit", admin.deposit.DepositHandler),
            url(r"/backend/withdraw", admin.withdraw.WithdrawHandler),
            url(r"/backend/transfer", admin.transfer.TransferHandler),

            url(r"/backend/action", admin.action.ActionHandler),
            url(r"/backend/config", admin.config.ConfigHandler),

            # cbs
            url(r"/cbs/register", cbs_register.RegisterHandler, name="cbs_register"),
            url(r"/cbs/login", cbs_auth.LoginHandler, name="cbs_login"),
            url(r"/cbs/logout", cbs_auth.LogoutHandler, name="cbs_logout"),
            url(r"/cbs/public", cbs_public.PublicHandler, name="cbs_public"),
            url(r"/cbs/fee", cbs_fee.FeeHandler, name="cbs_fee"),
            url(r"/cbs/wallet", cbs_wallet.WalletHandler, name="cbs_wallet"),
            url(r"/cbs/contact", cbs_contacts.ContactHandler, name="cbs_contact"),
            url(r"/cbs/deposit", cbs_deposit.DepositHandler, name="cbs_deposit"),
            url(r"/cbs/withdraw", cbs_withdraw.WithdrawHandler, name="cbs_withdraw"),
            url(r"/cbs/transfer", cbs_transfer.TransferHandler, name="cbs_transfer"),
            url(r"/cbs/profile", cbs_profile.ProfileHandler, name="cbs_profile"),
            url(r"/cbs/security", cbs_security.SecurityHandler, name="cbs_security"),
            url(r"/cbs/message", cbs_message.MessageHandler, name="cbs_message"),

            # template
            url(r"/backend/(manager|agent|finance|users)/(.*)", admin.template.TemplateHandler),
            # url(r"/admin/(manager|agent|finance|users)/(.*)", admin.template.TemplateHandler),
            url(r"/cbs/main/(.*)", cbs_main.MainHandler, name="cbs_main"),

        ]
        tornado.web.Application.__init__(self, urls, **settings)


def main():
    log_init("log/cbs_app.log", True, True)

    tornado.options.parse_command_line()
    logging.basicConfig(level=settings.LOG_LEVEL)

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
