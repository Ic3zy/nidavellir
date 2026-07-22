def create_keywords(ast_parser):
    return {
        "DEF": ast_parser.parse_def,
        "IF": ast_parser.parse_if,
        # "WHILE": ast_parser.parse_while,
        # "RETURN": ast_parser.parse_return,
    }