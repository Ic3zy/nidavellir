from lexer import TOKEN_PATTERNS

def create_keywords(ast_parser):
    keywords = {}
    for pattern in TOKEN_PATTERNS:
        pattern_name = pattern[0]

        function_name = f"parse_{pattern_name.lower()}"

        function = getattr(ast_parser, function_name, None)

        keywords[pattern_name] = function
    
    return keywords
        