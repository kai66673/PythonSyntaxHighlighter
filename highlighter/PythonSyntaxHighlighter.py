from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QTextOption

from enum import Enum

from highlighter.PythonScanner import PythonScanner


class FontStyle(Enum):
    Normal = 0
    Bold = 1
    Italic = 2
    BoldItalic = 3


def _fillFormat(color, style=None):
    _color = QColor(color)
    _format = QTextCharFormat()
    _format.setForeground(_color)

    if not style:
        style = FontStyle.Normal
    if style == FontStyle.Bold:
        _format.setFontWeight(QFont.Bold)
    elif style == FontStyle.Italic:
        _format.setFontItalic(True)
    elif style == FontStyle.BoldItalic:
        _format.setFontWeight(QFont.Bold)
        _format.setFontItalic(True)

    return _format


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super(PythonSyntaxHighlighter, self).__init__(document)

        self.formats = [
            _fillFormat('brown'),                           # numbers
            _fillFormat('magenta'),                         # string
            _fillFormat('blue'),                            # keyword
            _fillFormat('blueviolet', FontStyle.Bold),      # type
            _fillFormat('black', FontStyle.Italic),         # ClassField
            _fillFormat('black', FontStyle.BoldItalic),     # MagicAttr
            _fillFormat('saddlebrown'),                     # operator
            _fillFormat('sandybrown'),                      # braces
            _fillFormat('green'),                           # comment
            _fillFormat('darkgreen', FontStyle.Bold),       # doxygen
            _fillFormat('lightslategray'),                  # identifier
            _fillFormat('gray'),                            # whitespace
            _fillFormat('darkmagenta', FontStyle.Italic),   # ImportedModule
            _fillFormat('red', FontStyle.BoldItalic),       # unknown
            _fillFormat('olivedrab', FontStyle.BoldItalic), # classdef
            _fillFormat('olive', FontStyle.BoldItalic),     # functiondef
        ]

        option = document.defaultTextOption()
        option.setFlags(option.flags() | QTextOption.ShowTabsAndSpaces)
        document.setDefaultTextOption(option)

    def highlightBlock(self, text):
        initialState = self.previousBlockState()
        if initialState == -1:
            initialState += 1
        self.setCurrentBlockState(self.highlightLine(text, initialState))

    def highlightLine(self, text, initialState):
        scanner = PythonScanner(text, initialState)

        hasOnlyWhitespace = True
        tk = scanner.read()
        while not tk.isEndOfBlock():
            fmt = tk.format
            self.setFormat(tk.position, tk.length, self.formats[fmt])

            if fmt == PythonScanner.FormatToken.Format.Keyword and hasOnlyWhitespace:
                keywordKind = tk.keywordKind(text)
                if keywordKind == PythonScanner.FormatToken.SpecialKeyword.ImportOrFrom:
                    self.highlightImport(scanner)
                elif keywordKind == PythonScanner.FormatToken.SpecialKeyword.Class:
                    self.highlightDeclarationIdentifier(scanner, self.formats[-2])
                elif keywordKind == PythonScanner.FormatToken.SpecialKeyword.Def:
                    self.highlightDeclarationIdentifier(scanner, self.formats[-1])
                else:
                    self.setFormat(tk.position, tk.length, self.formats[tk.format])

            if fmt != PythonScanner.FormatToken.Format.Whitespace:
                hasOnlyWhitespace = False

            tk = scanner.read()

        return scanner.state

    def highlightDeclarationIdentifier(self, scanner, fmt):
        tk = scanner.read()
        while tk.format == PythonScanner.FormatToken.Format.Whitespace:
            self.setFormat(tk.position, tk.length, self.formats[tk.format])
            tk = scanner.read()
        if tk.isEndOfBlock():
            return
        elif tk.format == PythonScanner.FormatToken.Format.Identifier:
            self.setFormat(tk.position, tk.length, fmt)
        else:
            self.setFormat(tk.position, tk.length, self.formats[tk.format])

    def highlightImport(self, scanner):
        tk = scanner.read()
        while not tk.isEndOfBlock():
            fmt = PythonScanner.FormatToken.Format.ImportedModule\
                if tk.format == PythonScanner.FormatToken.Format.Identifier\
                else tk.format
            self.setFormat(tk.position, tk.length, self.formats[fmt])
            tk = scanner.read()
