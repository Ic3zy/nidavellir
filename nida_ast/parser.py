from .base import *
from .keys import create_keywords


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
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

    def advance(self):
        token = self.current
        self.index += 1
        return token

    def peek_kind(self):
        curr = self.current
        if curr is None:
            return None
        return curr[0] if isinstance(curr, tuple) else curr

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

        return ElifAST(cond, body)
    
    def read_else(self):
        self.advance()
        body = []

        while self.current is not None and self.peek_kind() != "DEDENT":
            body.append(self.advance())

        self.advance() # skip dedent

        return body

    def parse_if(self):
        print("CALLED")
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
            print("ELIF")
            elifs.append(self.read_elif())

        if self.peek_kind() == "ELSE":
            elses.append(self.read_else())

        print("IF CONDITION:", if_keywords)
        print("IF BODY:", if_body)
        print("ELIFS:", elifs)
        print("ELSE BODY:", elses)

    def parse_all(self):
        while self.current is not None:
            kind = self.peek_kind()
            func = self.keywords.get(kind, None)
            
            if func is not None:
                func()
            else:
                self.advance()