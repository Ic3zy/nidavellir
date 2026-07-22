from .patterns import MASTER_REGEX
import re

class Lexer:
    def __init__(self, source_code):
        self.sp = source_code.split("\n")
        self.tokens = []
        self.line_count = 0
        self.last_indent = 0

    def indent_calc(self, line):
        space_count = 0
        for i in list(line):
            if i == " ":
                space_count += 1
            else:
                break

        if space_count and space_count % 4 == 0:
            return space_count // 4
        elif space_count:
            raise Exception("indentation error")
        else:
            return 0

    def tokenize_line(self, line, line_number):
        line_tokens = []
        for match in re.finditer(MASTER_REGEX, line):
            kind = match.lastgroup
            value = match.group(kind) 
            
            if kind == "NAME":
                if value in ("def", "elif", "if", "else", "return", "True", "False", "None"):
                    kind = value.upper() 
            
            line_tokens.append((kind, value, line_number))
            
        return line_tokens

    def tokenize(self):
        for line in self.sp:
            self.line_count += 1

            if not line.strip() or line.strip().startswith("#"):
                continue

            indent = self.indent_calc(line)

            if indent > self.last_indent:
                indent_diff = indent - self.last_indent

                for _ in range(indent_diff):
                    self.tokens.append(("INDENT", None, self.line_count))

            elif indent < self.last_indent:
                indent_diff = self.last_indent - indent

                for _ in range(indent_diff):
                    self.tokens.append(("DEDENT", None, self.line_count))

            line_tokens = self.tokenize_line(line, self.line_count)
            self.tokens.extend(line_tokens)

            self.last_indent = indent

        while self.last_indent > 0:
            self.tokens.append("DEDENT")
            self.last_indent -= 1

        return self.tokens