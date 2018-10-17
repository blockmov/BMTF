import logging
import threading
import smtplib
from email.mime.text import MIMEText
import types

import settings

logging.getLogger(__file__)


def send_email(msg, subject, recipients):
    status = 0
    try:
        if isinstance(recipients, (types.StringType, types.UnicodeType)):
            recipients = recipients.split(";")

        smtp = smtplib.SMTP()
        smtp.connect(settings.SMTP_HOST, 25)
        smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        html = MIMEText(msg, 'html', _charset='utf8')
        sender = settings.SMTP_SENDER
        html['Subject'] = subject
        html['From'] = sender
        html['To'] = ";".join(recipients)
        smtp.sendmail(sender, recipients, html.as_string())
    except Exception as e:
        logging.error("send email failed: {0}".format(str(e)))
        status = -1
    return status


def send_register_welcome_email(email_address):
    msg = "Thank you for joining CBS"
    info = "send_register_welcome_email: {}".format(email_address)
    logging.info(info)
    t = threading.Thread(target=send_email, args=(msg, "CBS Register", email_address))
    t.start()
    return 0


def send_reset_login_password_verify_email(email_address, code):
    msg = "You are resetting the login password, the following is your verification code: <h2>{}</h2>.".format(code)
    info = "send_reset_login_password_verify_email: {} -> {}".format(email_address, code)
    logging.info(info)
    t = threading.Thread(target=send_email, args=(msg, "CBS", email_address))
    t.start()
    return 0


def send_reset_trade_password_verify_email(email_address, code):
    msg = "You are resetting the trade password, the following is your verification code: <h2>{}</h2>.".format(code)
    info = "send_reset_trade_password_verify_email: {} -> {}".format(email_address, code)
    logging.info(info)
    t = threading.Thread(target=send_email, args=(msg, "CBS", email_address))
    t.start()
    return 0


def send_register_verify_email(email_address, code):
    msg = "Thank you for joining CBS. Here is your registration confirmation code: <h2>{}</h2>.".format(code)
    info = "send_register_verify_email: {} -> {}".format(email_address, code)
    logging.info(info)
    t = threading.Thread(target=send_email, args=(msg, "CBS", email_address))
    t.start()
    return 0


def send_forget_password_email(email_address, code):
    msg = "Reset password confirmation code: <h2>{}</h2>.".format(code)
    info = "send_forget_password_email: {} -> {}".format(email_address, code)
    logging.info(info)
    t = threading.Thread(target=send_email, args=(msg, "CBS", email_address))
    t.start()
    return 0


def send_forget_user_password_email(email_address, token):
    '''
    admin user forget password email
    :param email_address:
    :param token:
    :return:
    '''
    url = "https://{0}/admin/users/reset_password?email={1}&token={2}".format(settings.SERVER_HOST, email_address,
                                                                              token)
    print "send_forget_password_email: {0}".format(url)
    logging.debug("send_forget_password_email: {0}".format(url))
    msg = "<a href='%s'>%s</a>" % (url, url)
    t = threading.Thread(target=send_email, args=(msg, "CBS", email_address))
    t.start()
    return 0
