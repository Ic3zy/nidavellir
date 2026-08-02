TOKEN_PATTERNS = [
    ("EQEQ",      r'=='),
    ("NEQ",       r'!='),
    ("LTE",       r'<='),
    ("GTE",       r'>='),
    
    ("AND",       r'\band\b'),
    ("OR",        r'\bor\b'),
    ("IF",        r'\bif\b'),
    ("ELIF",      r'\belif\b'),
    ("ELSE",      r'\belse\b'),
    ("WHILE",     r'\bwhile\b'),
    ("FOR",       r'\bfor\b'),
    ("PASS",      r'\bpass\b'),
    ("RETURN",    r'\breturn\b'),
    ("TRUE",      r'\bTrue\b'),
    ("FALSE",     r'\bFalse\b'),

    ("ASSIGN",    r'='),
    ("PLUS",      r'\+'),
    ("MINUS",     r'\-'),
    ("STAR",      r'\*'),
    ("AMP",       r'&'),
    ("DIV",       r'/'),
    ("MOD",       r'%'),
    ("LT",        r'<'),
    ("GT",        r'>'),
    ("LPAREN",    r'\('),
    ("RPAREN",    r'\)'),
    ("LBRACKET",  r'\['),
    ("RBRACKET",  r'\]'),
    ("COLON",     r':'),
    ("COMMA",     r','),
    ("DOT",       r'\.'),
    
    ("STRING",    r'"[^"]*"|\'[^\']*\''),
    ("NUMBER",    r'\d+(\.\d+)?'),
    
    ("NAME",      r'[a-zA-Z_][a-zA-Z0-9_]*'), 
]

MASTER_REGEX = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_PATTERNS)

