import functools

import tornado.escape
import tornado.web
import wtforms_json

wtforms_json.init()


class BaseHandler(tornado.web.RequestHandler):

    def send_json_response(self, code, message, result):
        data = {'code': code,
                'message': message,
                'result': result
                }
        output = tornado.escape.json_encode(data)
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        self.write(output)
        self.finish()

