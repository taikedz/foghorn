import signal
import sys

def signal_handler(sig, frame):
    print('INTERRUPTED')
    sys.exit(0)

def setup():
    signal.signal(signal.SIGTERM, signal_handler)
