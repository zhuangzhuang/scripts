#coding: utf-8
from werkzeug.wrappers import Request
import sys
import os

class LiveBpMiddleware(object):
    def __init__(self, app, use_exception=Exception("Break Here")):
        '''url中加入?livebp=(filename):(line)即可触发异常'''
        self.app = app
        self.tracing = False
        self.org_trace = sys.gettrace()
        self.use_exception = use_exception

    def __call__(self, environ, start_response):
        request = Request(environ)
        livebp = request.args.get('livebp', u'')
        if livebp and livebp.count(u':') == 1:
            model, line = livebp.split(u':')
            filename = self.lookupmodule(model)
            if filename:
                self.trace_filename = filename
                self.trace_line = int(line)
                self.tracing = True
                sys.settrace(self.trace_fun)
        res = self.app(environ, start_response)
        if self.tracing:
            self.remove_trace()
        return res

    def remove_trace(self):
        sys.settrace(self.org_trace)
        self.tracing = False

    def trace_fun(self, frame, event, arg):
        if event == 'line':
            line_no = frame.f_lineno
            filename = frame.f_code.co_filename
            if line_no == self.trace_line and os.path.realpath(filename) == os.path.realpath(self.trace_filename):
                print line_no, filename
                sys.settrace(self.org_trace)
                self.tracing = False
                raise self.use_exception
        return self.trace_fun

    def lookupmodule(self, filename):
        'copy from pdb model'
        filename = filename.replace('.', os.path.sep)
        if os.path.isabs(filename) and os.path.exists(filename):
            return filename
        f = os.path.join(sys.path[0], filename)
        if os.path.exists(f):
            return f
        root, ext = os.path.splitext(filename)
        if ext == '':
            filename = filename + '.py'
        if os.path.isabs(filename):
            return filename
        for dirname in sys.path:
            while os.path.islink(dirname):
                dirname = os.readlink(dirname)
            fullname = os.path.join(dirname, filename)
            if os.path.exists(fullname):
                return fullname
        return None


if __name__ == '__main__':
    '''Test'''
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        a = 1
        b = 2
        c = 3
        return 'Hello'

    app.wsgi_app = LiveBpMiddleware(app.wsgi_app)
    app.run(debug=True)