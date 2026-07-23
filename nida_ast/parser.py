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
        print(self.tokens)

    def get_token(self, index):
        if 0 <= index < len(self.tokens):
            return self.tokens[index]
        return None

    @property
    def current(self):
        return self.get_token(self.index)

    def print_error(self, msg):
        curr = self.current
        if curr is None:
            raise Exception("Syntax Error: Unexpected end of file")

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

        print(msg)

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

        raise self.print_error("Syntax Error")

    def parse_number(self, data_type=None):
        token_value = self.advance()
        
        return NumberAST(value=token_value[1], data_type=data_type)

    def parse_expression(self):
        kind = self.peek_kind()

        if kind == "NUMBER":
            return self.parse_number()
        
        elif kind == "STRING":
            token = self.advance()
            return StringAST(value=token[1])
            
        elif kind == "NAME":
            return self.parse_identifier_or_call()
            
        else:
            raise self.print_error(f"Syntax Error: Unexpected expression token '{kind}'")

    def check_function_call(self):
        start_index = self.index
        while self.peek_kind() != "LPAREN":
            if self.peek_kind() == "DOT":
                self.advance()

            elif self.peek_kind() == "NAME":
                self.advance()

            else:
                self.index = start_index
                return False

        self.index = start_index
        print("func call")
        return True

    def check_assignment(self):
        offset = 0
        while True:
            tok = self.get_token(self.index + offset)
            if tok is None:
                break
            
            kind = tok[0] if isinstance(tok, tuple) else tok
            
            if kind in ("ASSIGN", "COLON"):
                return True
            if kind in ("NEWLINE", "DEDENT", "SEMI"): 
                break
            
            offset += 1
            
        return False
    
    def parse_chain_target(self):
        start_token = self.consume("NAME")
        chain = []

        while self.peek_kind() == "DOT":
            self.advance()

            if self.peek_kind() == "NAME":
                field_token = self.advance()
                chain.append(field_token[1])
            else:
                raise self.print_error("Syntax Error: Expected field name after '.'")

        return start_token[1], chain
    
    def parse_assignment(self):
        name, chain = self.parse_chain_target()

        self.consume("ASSIGN")

        value = self.parse_expression()

        return AssignAST(name, chain, value)


    def parse_function_call(self):
        start_name = self.advance()

        chain = []
        while self.peek_kind() != "LPAREN":
            if self.peek_kind() == "DOT":
                self.advance()
                continue
            elif self.peek_kind() == "NAME":
                kind = self.parse_kind(self.advance())

                if kind is not None:
                    chain.append(kind)
                    continue
                continue
            else:
                raise self.print_error("Syntax Error: Expected dot or name")
            
        self.consume("LPAREN")
        args = []
        while self.current is not None and self.peek_kind() != "RPAREN":
            kind = self.parse_kind(self.peek_kind())
            args.append(kind)

        self.consume("RPAREN")

        return ChainAccessAST(start_name, chain, args)

    def parse_while(self):
        self.consume("NAME")
        conditions = []
        while self.peek_kind() != "COLON":
            conditions.append(self.current)
            self.advance()

        self.consume("COLON")
        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            body.append(self.advance())
            
        self.advance() # skip dedent

        return WhileAST(conditions, body)

    def parse_name(self):
        statement_kyw = {
            # "with": self.parse_with,
            # "for": self.parse_for,
            "while": self.parse_while,
        }

        token = self.current
        if token is None:
            raise self.print_error("Syntax Error: Expected name")

        name = token[1]
        if name in statement_kyw:
            return statement_kyw[name]()

        if self.check_function_call():
            return self.parse_function_call()

        if self.check_assignment():
            return self.parse_assignment()
        else:
            return
            raise self.print_error()


    # func blocks
    def parse_def(self):
        self.advance()
        if self.peek_kind() != "NAME":
            raise self.print_error("Syntax Error: Expected name")

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
            name = old_token

        print("current d", self.current)

        self.consume("LPAREN")

        while self.current is not None and self.peek_kind() != "RPAREN":
            kind = self.parse_kind(self.advance())
            args.append(kind)

        self.advance() # skip rparen
        self.advance() # skip colon

        self.consume("INDENT")
        
        body = []
        count = 0
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.peek_kind()
            parsed = self.parse_kind(kind)
            if parsed is not None:
                body.append(parsed)
            else:
                self.advance()

        self.advance() # skip dedent

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
            print("e: ", kind)
            raise self.print_error("Syntax Error: Expected '{}'".format(kind))

        func = self.keywords.get(kind, None)
        if func is not None:
            return func()

        if kind == "NAME":
            return self.parse_name()

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
        print(self.asts[0].conditions)
        print(self.asts[0].body)