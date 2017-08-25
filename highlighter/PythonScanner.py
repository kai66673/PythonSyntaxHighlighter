from enum import IntEnum


class PythonScanner(object):
    keywords = {
        "and", "as", "assert", "break", "class", "continue", "def", "del", "elif",
        "else", "except", "exec", "finally", "for", "from", "global", "if", "import",
        "in", "is", "lambda", "not", "or", "pass", "print", "raise", "return", "try",
        "while", "with", "yield"
    }
    magics = {
        "__init__", "__del__",
        "__str__", "__repr__", "__unicode__",
        "__setattr__", "__getattr__", "__delattr__",
        "__add__", "__sub__", "__mul__", "__truediv__", "__floordiv__", "__mod__",
        "__pow__", "__and__", "__or__", "__xor__", "__eq__", "__ne__", "__gt__",
        "__lt__", "__ge__", "__le__", "__lshift__", "__rshift__", "__contains__",
        "__pos__", "__neg__", "__inv__", "__abs__", "__len__",
        "__getitem__", "__setitem__", "__delitem__", "__getslice__", "__setslice__",
        "__delslice__",
        "__cmp__", "__hash__", "__nonzero__", "__call__", "__iter__", "__reversed__",
        "__divmod__", "__int__", "__long__", "__float__", "__complex__", "__hex__",
        "__oct__", "__index__", "__copy__", "__deepcopy__", "__sizeof__", "__trunc__",
        "__format__",
        "__name__", "__module__", "__dict__", "__bases__", "__doc__"
    }

    builtins = {
        "range", "xrange", "int", "float", "long", "hex", "oct" "chr", "ord",
        "len", "abs", "None", "True", "False"
    }

    operators = { '=', '!', '<', '>', '+', '-', '*', '/', '\%', '^', '|', '&', '~', '.', ',', ':', ';' }

    braces = { '{', '}', '(', ')', '[', ']' }

    class State(IntEnum):
        Default = 0
        StringSingleQuote = 1
        StringDoubleQuote = 2
        MultiLineStringSingleQuote = 3
        MultiLineStringDoubleQuote = 4

    class FormatToken(object):
        class Format(IntEnum):
            Number = 0
            String = 1
            Keyword = 2
            Type = 3
            ClassField = 4
            MagicAttr = 5
            Operator = 6
            Braces = 7
            Comment = 8
            Doxygen = 9
            Identifier = 10
            Whitespace = 11
            ImportedModule = 12
            Unknown = 13
            FormatsAmount = 14

        class SpecialKeyword(IntEnum):
            ImportOrFrom = 0
            Class = 1
            Def = 2
            Other = 3

        def __init__(self, format = Format.FormatsAmount, position = -1, length = -1):
            self.format = format
            self.position = position
            self.length = length

        def isEndOfBlock(self):
            return self.position == -1

        def keywordKind(self, text):
            v = text[self.position: self.position + self.length]
            if v == "import" or v == "from":
                return PythonScanner.FormatToken.SpecialKeyword.ImportOrFrom
            elif v == 'class':
                return PythonScanner.FormatToken.SpecialKeyword.Class
            elif v == "def":
                return PythonScanner.FormatToken.SpecialKeyword.Def
            return PythonScanner.FormatToken.SpecialKeyword.Other

        def isImportKeyword(self, text):
            v = text[self.position : self.position + self.length]
            return v == "import" or v == "from"

        def isClassKeyword(self, text):
            v = text[self.position: self.position + self.length]

    def __init__(self, text, state):
        self.text = text
        self.state = state

        self.position = 0
        self.markedPosition = 0
        self.textLength = len(text)

    def read(self):
        self.markedPosition = self.position
        if self.position >= self.textLength:
            return PythonScanner.FormatToken()
        if self.state == PythonScanner.State.StringSingleQuote:
            return self.readStringLiteral("'")
        elif self.state == PythonScanner.State.StringDoubleQuote:
            return self.readStringLiteral('"')
        elif self.state == PythonScanner.State.MultiLineStringSingleQuote:
            return self.readMultiLineStringLiteral("'")
        elif self.state == PythonScanner.State.MultiLineStringDoubleQuote:
            return self.readMultiLineStringLiteral('"')
        return self.onDefaultState()

    def peek(self, offset = 0):
        pos = self.position + offset
        return self.text[pos] if pos < self.textLength else '\0'

    def onDefaultState(self):
        first = self.peek()
        self.position += 1

        if first == '\\' and self.peek() == '\n':
            self.position += 1
            return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Whitespace,
                                             self.markedPosition, 2)

        if first == '.' and self.peek().isdigit():
            return self.readFloatNumber()

        if first == '"' or first == "'":
            return self.readStringLiteral(first)

        if first.isalpha() or first == '_':
            return self.readIdentifier()

        if first.isdigit():
            return self.readNumber()

        if first == '#':
            if self.peek() == '#':
                return self.readDoxygenComment()
            return self.readComment()

        if first.isspace():
            return self.readWhiteSpace()

        return self.readOther()

    def checkEscapeSequence(self, quoteChar):
        if self.peek() == '\\':
            self.position += 1
            ch = self.peek()
            if ch == '\n' or ch == '\0':
                self.state = PythonScanner.State.StringSingleQuote if quoteChar == "'" else PythonScanner.State.StringDoubleQuote

    def readStringLiteral(self, quoteChar):
        ch = self.peek()
        if ch == quoteChar and self.peek(1) == quoteChar:
            self.state = PythonScanner.State.MultiLineStringSingleQuote if quoteChar == "'" else PythonScanner.State.MultiLineStringDoubleQuote
            return self.readMultiLineStringLiteral(quoteChar)

        while ch != quoteChar and ch != '\0':
            self.checkEscapeSequence(quoteChar)
            self.position += 1
            ch = self.peek()

        if ch == quoteChar:
            self.state = PythonScanner.State.Default

        self.position += 1
        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.String,
                                         self.markedPosition, self.position - self.markedPosition)

    def readMultiLineStringLiteral(self, quoteChar):
        while True:
            ch = self.peek()
            if ch == '\0':
                break
            if ch == quoteChar and self.peek(1) == quoteChar and self.peek(2) == quoteChar:
                self.state = PythonScanner.State.Default
                self.position += 3
                break
            self.position += 1

        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.String,
                                         self.markedPosition, self.position - self.markedPosition)

    def readIdentifier(self):
        ch = self.peek()
        while ch.isalnum() or ch == '_':
            self.position += 1
            ch = self.peek()

        v = self.text[self.markedPosition:self.position]
        tkFormat = PythonScanner.FormatToken.Format.Identifier
        if v == "self":
            tkFormat = PythonScanner.FormatToken.Format.ClassField
        elif v in PythonScanner.builtins:
            tkFormat = PythonScanner.FormatToken.Format.Type
        elif v in PythonScanner.magics:
            tkFormat = PythonScanner.FormatToken.Format.MagicAttr
        elif v in PythonScanner.keywords:
            tkFormat = PythonScanner.FormatToken.Format.Keyword

        return PythonScanner.FormatToken(tkFormat, self.markedPosition, self.position - self.markedPosition)

    def isBinaryDigit(self, ch):
        return ch == '0' or ch == '1'

    def isOctalDigit(self, ch):
        return ch.isdigit() and ch != '8' and ch != '9'

    def isHexDigit(self, ch):
        return ch.isDigit() or (ch >= 'a' and ch <= 'f') or (ch >= 'A' and ch <= 'F')

    def isValidIntegerSuffix(self, ch):
        return ch == 'l' or ch == 'L'

    def readNumber(self):
        if self.position < self.textLength:
            ch = self.peek()
            if ch.lower() == 'b':
                self.position += 1
                while self.isBinaryDigit(self.peek()):
                    self.position += 1
            elif ch.lower() == 'o':
                self.position += 1
                while self.isOctalDigit(self.peek()):
                    self.position += 1
            elif ch.lower() == 'x':
                self.position += 1
                while self.isHexDigit(self.peek()):
                    self.position += 1
            else:
                return self.readFloatNumber()
            if self.isValidIntegerSuffix(self.peek()):
                self.position += 1

        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Number,
                                         self.markedPosition, self.position - self.markedPosition)

    def readFloatNumber(self):
        state = 1 if self.peek(-1) == '.' else 0

        while True:
            ch = self.peek()
            if ch == '\0':
                break

            if state == 0:
                if ch == '.':
                    state = 1
                elif not ch.isdigit():
                    break
            elif state == 1:
                if ch == 'e' or ch == 'E':
                    ch1 = self.peek(1)
                    ch2 = self.peek(2)
                    isExp = ch1.isdigit() or ((ch1 == '-' or ch1 == '+') and ch2.isdigit())
                    if isExp:
                        self.position += 1
                        state = 2
                    else:
                        break
                elif not ch.isdigit():
                    break
            elif not ch.isdigit():
                break
            self.position += 1

        ch = self.peek()
        if state == 0 and ch in ['l', 'L', 'j', 'J']:
            self.position += 1

        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Number,
                                         self.markedPosition, self.position - self.markedPosition)

    def readComment(self):
        ch = self.peek()
        while ch != '\n' and ch != '\0':
            self.position += 1
            ch = self.peek()
        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Comment,
                                         self.markedPosition, self.position - self.markedPosition)

    def readDoxygenComment(self):
        ch = self.peek()
        while ch != '\n' and ch != '\0':
            self.position += 1
            ch = self.peek()
        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Doxygen,
                                         self.markedPosition, self.position - self.markedPosition)

    def readWhiteSpace(self):
        while self.peek().isspace():
            self.position += 1
        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Whitespace,
                                         self.markedPosition, self.position - self.markedPosition)

    def readOther(self):
        ch = self.peek(-1)

        if ch in PythonScanner.operators:
            ch = self.peek()
            while ch in PythonScanner.operators:
                self.position += 1
                ch = self.peek()
            return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Operator,
                                             self.markedPosition, self.position - self.markedPosition)

        if ch in PythonScanner.braces:
            return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Braces,
                                             self.markedPosition, self.position - self.markedPosition)

        # Unknown character
        return PythonScanner.FormatToken(PythonScanner.FormatToken.Format.Unknown,
                                         self.markedPosition, self.position - self.markedPosition)


