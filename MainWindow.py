from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QMainWindow, QPlainTextEdit

from highlighter.PythonSyntaxHighlighter import PythonSyntaxHighlighter


class MainWindow(QMainWindow):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        self.editor = QPlainTextEdit()
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(12)
        self.editor.setFont(font)
        self.highlighter = PythonSyntaxHighlighter(self.editor.document())
        self.setCentralWidget(self.editor)
        self.setWindowTitle("Python Syntax Highlighter")