from .base import *
from .keys import create_keywords
import sys


class Parser:
    def __init__(self, lexer):
        self.tokens = lexer.tokenize()
        self.lines = lexer.sp
        self.index = 0
        self.asts = []
        self.keywords = create_keywords(self)

    def get_token(self, index):
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None

    @property
    def current(self):
        return self.get_token(self.index)

    def print_error(self):
        curr = self.current
        if curr is None:
            return

        target_line = curr[2]
        
        start_line = max(1, target_line - 3)
        end_line = min(len(self.lines), target_line + 3)

        print(f"\n--- Compile Error (Line {target_line}) ---")
        
        for l in range(start_line, end_line + 1):
            line_str = self.lines[l - 1].rstrip('\n')
            
            if l == target_line:
                print(f" {l:3d} | {line_str}")
                
                indent_spaces = len(line_str) - len(line_str.lstrip())
                caret_len = max(1, len(line_str.strip()))
                print(" " * 6 + " " * indent_spaces + "^" * caret_len)
            else:
                print(f" {l:3d} | {line_str}")

        sys.exit(1)

    def advance(self):
        token = self.current
        self.index += 1
        return token

    def peek_kind(self):
        curr = self.current
        if curr is None:
            return None
        return curr[0] if isinstance(curr, tuple) else curr
    
    def consume(self, kind):
        if self.peek_kind() == kind:
            return self.advance()
            
        raise self.print_error()

    # func blocks
    def parse_def(self):
        self.advance()
        if self.peek_kind() != "NAME":
            raise self.print_error()

        old_token = self.advance()

        type = None
        name = None

        args = []

        if self.peek_kind() != "LPAREN":
            print("expected lparen")

            if self.peek_kind() == "NAME":
                type = old_token
                name = self.advance()
        else:
            self.advance()
            name = old_token

        while self.current is not None and self.peek_kind() != "RPAREN":
            args.append(self.advance())

        self.advance() # skip rparen
        
        body = []
        count = 0
        while self.current is not None and self.peek_kind() != "DEDENT":
            if count == 0 and self.peek_kind() != "COLON":
                print("expected colon")
            
            if count == 1 and self.peek_kind() != "INDENT":
                print("expected indent")

            count += 1

            if count == 2 and self.peek_kind() == "INDENT" or count == 1 and self.peek_kind() == "COLON":
                self.advance()
                continue

            kind = self.peek_kind()
            parsed = self.parse_kind(kind)
            if parsed is not None:
                body.append(parsed)
            else:
                self.advance()

        self.advance() # skip dedent

        print("current d", self.current)
        print(type, "\n")
        print(name, "\n")
        print(args, "\n")
        print(body, "\n")

        return FunctionAST(name, args, body)

    # if blocks
    def read_elif(self):
        self.advance()

        cond = []
        while self.current is not None and self.peek_kind() != "COLON":
            cond.append(self.advance())

        self.advance() # skip colon
        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            body.append(self.advance())
            
        self.advance() # skip dedent

        print("current elf", self.current)

        return ElifAST(cond, body)
    
    def read_else(self):
        self.advance()
        body = []

        while self.current is not None and self.peek_kind() != "DEDENT":
            body.append(self.advance())

        self.advance() # skip dedent

        return ElseAST(body)

    def parse_if(self):
        self.advance()
        
        if_keywords = []

        while self.current is not None and self.peek_kind() != "COLON":
            if_keywords.append(self.advance())

        self.advance() # skip colon

        if_body = []

        while self.current is not None and self.peek_kind() != "DEDENT":
            if_body.append(self.advance())
            
        self.advance() # skip dedent

        elifs = []
        elses = []

        if self.peek_kind() == "ELIF":
            elifs.append(self.read_elif())

        if self.peek_kind() == "ELSE":
            elses.append(self.read_else())

        return IfAST(if_keywords, if_body, elifs, elses)

    def parse_kind(self, kind):
        if kind in ("DEDENT", "RPAREN", "COMMA", "ELIF", "ELSE"):
            raise self.print_error()

        func = self.keywords.get(kind, None)
        if func is not None:
            return func()

        if kind == "NAME":
            return self.parse_assignment_or_expr()

        return None
    
    def parse_all(self):
        while self.current is not None:
            kind = self.peek_kind()

            res = self.parse_kind(kind)
            if res is not None:
                self.asts.append(res)
            else:
                self.advance()

        print(self.asts)