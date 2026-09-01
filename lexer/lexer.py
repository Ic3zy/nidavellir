from .patterns import MASTER_REGEX
import re

KEYWORDS = {
    "def",
    "elif",
    "if",
    "else",
    "return",
    "True",
    "False",
    "None",
    "for",
    "while",
    "in",
    "pass",
    "raise",
    "import",
    "from",
    "as",
    "break",
    "continue",
}


class Lexer:
    def __init__(self, source_code):
        self.sp = source_code.split("\n")
        self.tokens = []
        self.line_count = 0
        self.last_indent = 0
        self.paren_level = 0

    def indent_calc(self, line):
        space_count = 0
        for char in line:
            if char == " ":
                space_count += 1
            else:
                break

        if space_count % 4 != 0:
            raise Exception(
                f"IndentationError: Line {self.line_count} has invalid indentation ({space_count} spaces)"
            )

        return space_count // 4

    def tokenize_line(self, line, line_number):
        line_tokens = []

        for match in re.finditer(MASTER_REGEX, line):
            kind = match.lastgroup
            value = match.group(kind)

            if kind == "STRING":
                value = value[1:-1]

            if kind in ("LPAREN", "LBRACKET", "LBRACE"):
                self.paren_level += 1
            elif kind in ("RPAREN", "RBRACKET", "RBRACE"):
                self.paren_level = max(0, self.paren_level - 1)

            if kind == "NAME" and value in KEYWORDS:
                kind = value.upper()

            line_tokens.append((kind, value, line_number))

        return line_tokens

    def tokenize(self):
        for line in self.sp:
            self.line_count += 1

            code_part = line.split("#")[0]

            if not code_part.strip():
                continue

            indent = self.indent_calc(code_part)

            if self.paren_level == 0:
                if indent > self.last_indent:
                    indent_diff = indent - self.last_indent
                    for _ in range(indent_diff):
                        self.tokens.append(("INDENT", None, self.line_count))
                    self.last_indent = indent

                elif indent < self.last_indent:
                    indent_diff = self.last_indent - indent
                    for _ in range(indent_diff):
                        self.tokens.append(("DEDENT", None, self.line_count))
                    self.last_indent = indent

            line_tokens = self.tokenize_line(code_part, self.line_count)
            self.tokens.extend(line_tokens)

            if self.paren_level == 0:
                self.tokens.append(("NEWLINE", None, self.line_count))

        while self.last_indent > 0:
            self.tokens.append(("DEDENT", None, self.line_count))
            self.last_indent -= 1

        return self.tokens
