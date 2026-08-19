def format_item(item):
    if hasattr(item, "__class__") and item.__class__.__name__.endswith("AST"):
        node_name = item.__class__.__name__
        target = getattr(item, "target", getattr(item, "name", ""))
        target_str = f" ({target})" if target else ""
        return f"<{node_name}{target_str}>"
    return item


def render_node(label, value, prefix="", is_last=True):
    branch = "└── " if is_last else "├── "
    child_prefix = prefix + ("    " if is_last else "│   ")

    formatted = format_item(value)
    if isinstance(formatted, str):
        if label is not None:
            return [prefix + branch + f"{label}: {formatted}"]
        return [prefix + branch + formatted]

    if isinstance(value, list):
        header = prefix + branch + label + (":" if value else ": []")
        lines = [header]
        for index, item in enumerate(value):
            item_last = index == len(value) - 1
            lines.extend(render_node(None, item, child_prefix, item_last))
        return lines

    if hasattr(value, "__dict__"):
        header = f"{label} : {type(value).__name__}" if label else type(value).__name__
        lines = [prefix + branch + header]
        lines.extend(render_attrs(value, child_prefix))
        return lines

    if label is not None:
        return [prefix + branch + f"{label}: {value!r}"]

    item_lines = repr(value).splitlines() or [repr(value)]
    lines = [prefix + branch + item_lines[0]]
    lines.extend(child_prefix + line for line in item_lines[1:])
    return lines


def render_attrs(obj, prefix=""):
    attrs = [(key, val) for key, val in vars(obj).items() if key != "name"]
    lines = []
    for index, (key, val) in enumerate(attrs):
        lines.extend(render_node(key, val, prefix, index == len(attrs) - 1))
    return lines
