import sys
import asyncio

from PyQt5.QtWidgets import QApplication
from gui import MainWindow  # gui.py から MainWindow をインポート
import qasync

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    try:
        sys.exit(loop.run_forever())
    finally:
        loop.close()