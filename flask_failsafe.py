import functools
import sys
import traceback

import flask


if sys.version_info[0] == 2:
  from py2 import reraise
else:
  from py3 import reraise


def failsafe(func, config=dict()):
  """
  Wraps an app factory to provide a fallback in case of import errors.

  Takes a factory function to generate a Flask app. If there is an error
  creating the app, it will return a dummy app that just returns the Flask
  error page for the exception.

  This works with the Flask code reloader so that if the app fails during
  initialization it will still monitor those files for changes and reload
  the app.
  """

  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    extra_files = []
    try:
      app = func(*args, **kwargs)
      config.update(app.config.items())
      return app
    except:
      exc_type, exc_val, exc_tb = sys.exc_info()
      traceback.print_exc()

    tb = exc_tb
    while tb:
      filename = tb.tb_frame.f_code.co_filename
      extra_files.append(filename)
      tb = tb.tb_next

    if isinstance(exc_val, SyntaxError):
      extra_files.append(exc_val.filename)

    app = _FailSafeFlask(extra_files)
    app.config.update(config)
    app.debug = True

    @app.route('/')
    @app.route('/<path:path>')
    def index(path='/'):
      reraise(exc_type, exc_val, exc_tb)

    return app

  return wrapper


class _FailSafeFlask(flask.Flask):
  """
  Binds the extra_args parameter of run() to include the extra files we want to
  monitor for changes.
  """

  def __init__(self, extra_files):
    flask.Flask.__init__(self, __name__)
    self.extra_files = extra_files

  def run(self, *args, **kwargs):
    extra_files = self.extra_files
    if 'extra_files' in kwargs:
      extra_files = extra_files + kwargs['extra_files']
    kwargs['extra_files'] = extra_files
    flask.Flask.run(self, *args, **kwargs)

# Modeline parameters for Vim since this script uses non-pep8-compliant
# indenting
# vim: set ts=2 sw=2 :
