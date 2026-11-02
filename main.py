# main.py

import sys
from bootstrap import Application, CrashHandler, configure_environment
configure_environment()

if __name__ == "__main__":
    sys.excepthook = CrashHandler().handle
    sys.exit(Application().run())