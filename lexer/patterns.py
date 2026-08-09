# fmt: off

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
    ("CLASS",     r'\bclass\b'),
    ("FOR",       r'\bfor\b'),
    ("PASS",      r'\bpass\b'),
    ("RETURN",    r'\breturn\b'),
    ("TRUE",      r'\bTrue\b'),
    ("FALSE",     r'\bFalse\b'),

    ("PLUS_ASSIGN",  r'\+='), 
    ("MINUS_ASSIGN", r'\-='),
    ("STAR_ASSIGN",  r'\*='),
    ("DIV_ASSIGN",   r'/='),
    ("MOD_ASSIGN",   r'%='),
    ("ASSIGN",    r'='),

    ("AT",        r'\@'),
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
    
    ("STRING",    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''),
    ("NUMBER",    r'\d+(\.\d+)?'),
    
    ("NAME",      r'[a-zA-Z_][a-zA-Z0-9_]*'), 
]

MASTER_REGEX = "|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_PATTERNS)
