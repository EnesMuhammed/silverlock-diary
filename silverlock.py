from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QLineEdit, QToolBar,
    QFileDialog, QInputDialog, QTextBrowser,
    QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QSizePolicy, QSpacerItem)
from PySide6.QtGui import (
    QAction, QFont, QTextCursor, QTextCharFormat, QTextListFormat,
    QDesktopServices, QMouseEvent, QIntValidator, QColor)
from PySide6.QtCore import Qt, QUrl, QSize
import sys

if len(sys.argv) > 1:
    AUTOSAVE_PATH = sys.argv[1]
else:
    AUTOSAVE_PATH = "content.html" # Varsayılan yol
