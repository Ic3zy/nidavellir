from .base import *
from .keys import create_keywords, ASSIGN_TOKENS, COMPOUND_MAP
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
            print("Syntax Error: Unexpected end of file")
            sys.exit(1)

        target_line = curr[2]

        start_line = max(1, target_line - 3)
        end_line = min(len(self.lines), target_line + 3)

        print(f"\n--- Compile Error (Line {target_line}) ---")

        for l in range(start_line, end_line + 1):
            line_str = self.lines[l - 1].rstrip("\n")

            if l == target_line:
                print(f" {l:3d} | {line_str}")

                indent_spaces = len(line_str) - len(line_str.lstrip())
                caret_len = max(1, len(line_str.strip()))
                print(" " * 6 + " " * indent_spaces + "^" * caret_len)
            else:
                print(f" {l:3d} | {line_str}")

        print(self.current[1])

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

    def parse_primary(self):
        kind = self.peek_kind()

        if kind == "NUMBER":
            return NumberAST(self.advance()[1])

        if kind == "STRING":
            return StringAST(self.advance()[1])

        if kind == "NAME":
            return self.parse_name()

        if kind == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.consume("RPAREN")
            return expr

        if kind == "TRUE":
            self.advance()
            return BooleanAST(True)

        if kind == "FALSE":
            self.advance()
            return BooleanAST(False)

        self.print_error(f"Unexpected token in expression")

    def parse_factor(self):
        left = self.parse_primary()

        while self.peek_kind() in ("STAR", "SLASH"):
            op_token = self.advance()
            right = self.parse_primary()
            left = BinaryOpAST(left=left, op=op_token[1], right=right)

        return left

    def parse_term(self):
        left = self.parse_factor()

        while self.peek_kind() in ("PLUS", "MINUS"):
            op_token = self.advance()
            right = self.parse_factor()
            left = BinaryOpAST(left=left, op=op_token[1], right=right)

        return left

    def parse_or(self):
        left = self.parse_and()

        while self.peek_kind() in ("OR", "KW_OR"):
            op_token = self.advance()
            right = self.parse_and()
            left = BinaryOpAST(left=left, op=op_token[1], right=right)

        return left

    def parse_and(self):
        left = self.parse_equality()

        while self.peek_kind() in ("AND"):
            op_token = self.advance()
            right = self.parse_equality()
            left = BinaryOpAST(left=left, op=op_token[1], right=right)

        return left

    def parse_equality(self):
        left = self.parse_term()

        while self.peek_kind() in ("EQEQ", "NEQ", "GT", "LT", "GTE", "LTE"):
            op_token = self.advance()
            right = self.parse_term()
            left = BinaryOpAST(left=left, op=op_token[1], right=right)

        return left

    def parse_expression(self):
        return self.parse_or()

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

    def check_function_call(self):
        start_index = self.index

        if self.peek_kind() != "NAME":
            return False

        self.advance()

        while self.peek_kind() == "DOT":
            self.advance()
            if self.peek_kind() == "NAME":
                self.advance()

        if self.peek_kind() != "LPAREN":
            self.index = start_index
            return False

        find_lparen = False
        is_func = False

        while self.current is not None:
            kind = self.peek_kind()

            if kind == "LPAREN":
                find_lparen = True

            if kind == "RPAREN":
                if find_lparen:
                    is_func = True
                break

            if kind == "NEWLINE" and not find_lparen:
                break

            self.advance()

        self.index = start_index
        return is_func

    def check_assignment(self):
        offset = 0
        paren_depth = 0
        bracket_depth = 0
        brace_depth = 0

        prev_kind = None

        while True:
            tok = self.get_token(self.index + offset)
            if tok is None:
                break

            kind = tok[0] if isinstance(tok, tuple) else tok

            if kind == "LPAREN":
                paren_depth += 1
            elif kind == "RPAREN":
                paren_depth -= 1
            elif kind == "LBRACKET":
                bracket_depth += 1
            elif kind == "RBRACKET":
                bracket_depth -= 1
            elif kind == "LBRACE":
                brace_depth += 1
            elif kind == "RBRACE":
                brace_depth -= 1

            if kind in ("NEWLINE", "DEDENT", "SEMI"):
                break

            if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                if kind in ASSIGN_TOKENS:
                    return True

                if prev_kind == "NAME" and kind == "NAME":
                    return True

            prev_kind = kind
            offset += 1

        return False

    def skip_newlines(self):
        while self.current is not None and self.peek_kind() == "NEWLINE":
            self.advance()

    def get_compound_assignment(self):
        start_index = self.index

        while self.peek_kind() is not None and self.peek_kind() not in ASSIGN_TOKENS:
            if self.peek_kind() == "NEWLINE":
                self.index = start_index
                return False

            self.advance()

        if self.peek_kind() in ASSIGN_TOKENS:
            r = COMPOUND_MAP[self.peek_kind()]
            self.index = start_index
            return r

        self.index = start_index
        return False

    def get_assign_type(self):
        start_index = self.index
        if self.peek_kind() == "NAME":
            type = self.advance()
            if self.peek_kind() == "NAME":
                self.index = start_index
                return type

        self.index = start_index
        return False

    def parse_assignment(self):
        type = self.get_assign_type()
        if type:
            self.advance()

        comp = self.get_compound_assignment()

        target_name, chain = self.parse_chain_target()

        data_type = type[1] if isinstance(type, tuple) else None

        if data_type and chain:
            target_path = f"{target_name}.{'.'.join(chain)}"
            self.print_error(
                f"Syntax Error: Cannot use type annotation '{data_type}' on member access '{target_path}'.\n"
                f"  --> Fields already have a type defined in their class."
            )

        if self.peek_kind() == "COLON":
            self.print_error("Syntax Error: Unexpected ':'")

        value_ast = None

        if self.peek_kind() in ASSIGN_TOKENS:
            self.consume(self.peek_kind())
            value_ast = self.parse_expression()
            if comp:
                value_ast = BinaryOpAST(
                    left=VariableAST(name=target_name), op=comp, right=value_ast
                )

        return AssignAST(
            target=target_name, chain=chain, type_annotation=data_type, value=value_ast
        )

    def parse_function_call(self):
        target_name, chain = self.parse_chain_target()

        self.consume("LPAREN")

        args = []
        while self.current is not None and self.peek_kind() != "RPAREN":
            arg_ast = self.parse_kind(self.peek_kind())
            if arg_ast is not None:
                args.append(arg_ast)

            if self.peek_kind() == "COMMA":
                self.advance()

        self.consume("RPAREN")

        return CallAST(target=target_name, chain=chain, args=args)

    def parse_name(self, is_func_arg=False):
        token = self.current
        if token is None:
            raise self.print_error("Syntax Error: Expected name")

        if self.check_assignment():
            return self.parse_assignment()
        elif self.check_function_call():
            return self.parse_function_call()
        elif token[1] == "self":
            self.advance()
            return SelfAST()
        elif is_func_arg:
            return self.parse_assignment()
        else:
            self.advance()
            return VariableAST(name=token[1])

    def parse_else(self):
        self.consume("ELSE")
        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")
        return BlockAST(body)

    def parse_elif(self):
        self.consume("ELIF")
        cond = self.parse_expression()

        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")

        return ElifAST(cond, body)

    def parse_if(self):
        self.consume("IF")

        cond = self.parse_expression()

        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")

        self.skip_newlines()

        elifs = []
        while self.current is not None and self.peek_kind() == "ELIF":
            elifs.append(self.parse_elif())
            self.skip_newlines()

        else_body = None
        if self.current is not None and self.peek_kind() == "ELSE":
            else_body = self.parse_else()

        return IfAST(cond, body, elifs, else_body)

    def parse_def(self):
        self.consume("DEF")

        start = self.consume("NAME")

        name = None
        type = None

        if self.peek_kind() == "NAME":
            type = start
            name = self.advance()
        elif self.peek_kind() == "LPAREN":
            name = start
        else:
            self.print_error("Syntax Error: Expected function name")

        self.consume("LPAREN")

        args = []
        while self.current is not None and self.peek_kind() == "NAME":
            args.append(self.parse_name(is_func_arg=True))
            if self.peek_kind() == "COMMA":
                self.advance()

        self.consume("RPAREN")
        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")

        return FunctionAST(name=name[1], args=args, body=body, type=type)

    def parse_return(self):
        self.consume("RETURN")
        value = self.parse_expression()
        return ReturnAST(value)

    def parse_class(self):
        self.consume("CLASS")
        name = self.consume("NAME")
        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")
        return ClassAST(name=name[1], body=body)

    def parse_while(self):
        self.consume("WHILE")
        cond = self.parse_expression()
        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")

        return WhileAST(cond, body)

    def parse_for(self):
        self.consume("FOR")

        target = self.consume("NAME")
        self.consume("IN")
        source = self.parse_expression()

        self.consume("COLON")
        self.consume("NEWLINE")
        self.consume("INDENT")

        body = []
        while self.current is not None and self.peek_kind() != "DEDENT":
            kind = self.parse_kind(self.peek_kind())
            if kind is not None:
                body.append(kind)
            else:
                self.advance()

        self.consume("DEDENT")

        return ForAST(target, source, body)

    def parse_kind(self, kind):
        print("PARSE KIND", kind)
        if kind is None:
            return None

        if kind in ("DEDENT", "RPAREN", "COMMA", "ELIF", "ELSE"):
            self.print_error(f"Syntax Error: Unexpected '{kind}'")

        func = self.keywords.get(kind)
        if func is not None:
            return func()

        if kind == "NEWLINE":
            return None

        if kind == "RETURN":
            return self.parse_return()

        if kind == "NAME":
            return self.parse_name()

        if kind == "NUMBER":
            return self.parse_number()

        if kind == "STRING":
            token = self.advance()
            return StringAST(value=token[1])

        if kind == "PASS":
            self.advance()
            return PassAST()

        if kind == "LPAREN":
            self.advance()
            expr = self.parse_kind(self.peek_kind())
            self.consume("RPAREN")
            return expr

        if kind in ("PLUS", "MINUS", "STAR", "SLASH", "EQEQ", "NEQ", "GT", "LT"):
            token = self.advance()
            return OperatorAST(op=token[1])

        return None

    def parse_all(self):
        while self.current is not None:
            kind = self.peek_kind()
            res = self.parse_kind(kind)
            if res is not None:
                self.asts.append(res)
            else:
                self.advance()

        print("TREE", self.asts)
