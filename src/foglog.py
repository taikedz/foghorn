import logging
import sys

LOGS = {}
_LOGFILE = None

class SimpleLogger(logging.Logger):
    FORMAT_STRING = '%(asctime)s | %(levelname)s | %(name)s : %(message)s'
    ERROR = logging.ERROR
    WARN = logging.WARN
    INFO = logging.INFO
    DEBUG = logging.DEBUG

    def __init__(self, name="main", fmt_string=FORMAT_STRING, level=logging.WARNING, console=True, files=None):
        # log level here sets lower limit on all logs - hence hard coded to DEBUG
        logging.Logger.__init__(self, name, logging.DEBUG)
        formatter_obj = logging.Formatter(fmt_string)

        if files is None:
            files = []
        elif isinstance(files, str):
            files = [files]

        def _add_stream(handler:logging.Handler, **kwargs):
            handler = handler(**kwargs)
            handler.setLevel(level)
            handler.setFormatter(formatter_obj)
            self.addHandler(handler)

        if console is True:
            _add_stream(logging.StreamHandler, stream=sys.stdout)

        for filepath in files:
            _add_stream(logging.FileHandler, filename=filepath)


def GetLog(name):
    assert _LOGFILE, "Log file not set."
    if not name in LOGS:
        LOGS[name] = SimpleLogger(name=name, level=SimpleLogger.INFO, console=False, files=[_LOGFILE])
    return LOGS[name]


def InitLogFile(filepath):
    global _LOGFILE
    if not _LOGFILE:
        _LOGFILE = "./foghorn.log"
    _LOGFILE = filepath
