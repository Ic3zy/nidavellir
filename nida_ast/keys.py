COMPOUND_MAP = {
    "ASSIGN": "=",
    "PLUS_ASSIGN": "+",
    "MINUS_ASSIGN": "-",
    "STAR_ASSIGN": "*",
    "DIV_ASSIGN": "/",
    "MOD_ASSIGN": "%",
}

ASSIGN_TOKENS = COMPOUND_MAP.keys()


def create_keywords(ast_parser):
    return {
        "DEF": ast_parser.parse_def,
        "IF": ast_parser.parse_if,
        "FOR": ast_parser.parse_for,
        "WHILE": ast_parser.parse_while,
        "CLASS": ast_parser.parse_class,
    }
