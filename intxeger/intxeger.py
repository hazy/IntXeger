# flake8: noqa
# mypy: ignore-errors
import sre_parse
import string

from intxeger.core import (
    Choice,
    Concatenate,
    Constant,
    Group,
    GroupRef,
    Node,
    Repeat,
    CharacterClassChoice,
)
from intxeger.optimize import optimize


ILLEGAL_WHITE_SPACE_CHARACTERS = ["\n", "\r", "\t", "\v", "\f"]

ALL_CHARACTERS = [
    c for c in string.printable if c not in ILLEGAL_WHITE_SPACE_CHARACTERS
]

CATEGORY_MAP = {
    sre_parse.CATEGORY_SPACE: " ",
    sre_parse.CATEGORY_NOT_SPACE: "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~",
    sre_parse.CATEGORY_DIGIT: "0123456789",
    sre_parse.CATEGORY_NOT_DIGIT: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ ",
    sre_parse.CATEGORY_WORD: "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_",
    sre_parse.CATEGORY_NOT_WORD: "!\"#$%&'()*+,-./:;<=>?@[\\]^`{|}~ ",
}


def _to_node(op, args, max_repeat):
    if op == sre_parse.IN:
        nodes = []
        for op, args in args:
            nodes.append(_to_node(op, args, max_repeat))
        if nodes[0] == "NEGATE":
            values = [c[i] for c in nodes[1:] for i in range(c.length)]
            nodes = [Constant(c) for c in ALL_CHARACTERS if c not in values]
        node = Choice(nodes)
        return CharacterClassChoice(node=node)
    elif op == sre_parse.RANGE:
        min_value, max_value = args
        return Choice(
            [Constant(chr(value)) for value in range(min_value, max_value + 1)]
        )
    elif op == sre_parse.LITERAL:
        return Constant(chr(args))
    elif op == sre_parse.NEGATE:
        return "NEGATE"
    elif op == sre_parse.CATEGORY:
        return Choice([Constant(c) for c in CATEGORY_MAP[args]])
    elif op == sre_parse.ANY:
        return Choice([Constant(c) for c in ALL_CHARACTERS])
    elif op == sre_parse.ASSERT:
        nodes = []
        for op, args in args[1]:
            nodes.append(_to_node(op, args, max_repeat))
        return Concatenate(nodes)
    elif op == sre_parse.BRANCH:
        nodes = []
        for group in args[1]:
            subnodes = []
            for op, args in group:
                subnodes.append(_to_node(op, args, max_repeat))
            nodes.append(Concatenate(subnodes))
        return Choice(nodes)
    elif op == sre_parse.SUBPATTERN:
        nodes = []
        ref_id = args[0]
        for op, args in args[3]:
            nodes.append(_to_node(op, args, max_repeat))
        return Group(Concatenate(nodes), ref_id)
    elif op == sre_parse.GROUPREF:
        return GroupRef(ref_id=args)
    elif op == sre_parse.MAX_REPEAT or op == sre_parse.MIN_REPEAT:
        min_, max_, args = args
        op, args = args[0]
        if max_ == sre_parse.MAXREPEAT:
            max_ = max_repeat
        return Repeat(_to_node(op, args, max_repeat), min_, max_)
    elif op == sre_parse.NOT_LITERAL:
        node = Choice([Constant(c) for c in ALL_CHARACTERS if c != chr(args)])
        return CharacterClassChoice(node=node)
    else:
        raise ValueError(f"{op} {args}")


def build(regex: str, use_optimization: bool = True, max_repeat: int = 10) -> Node:
    """Parse the regex and return the root node.

    This parses the regex into an internal tree structure and returns the root
    node; the root node can then be used to generate samples.

    Args:
        regex: The regular expression string.
        use_optimization: Whether to apply the optimization routine.
        max_repeat: The maximum number of repeats when using the zero-or-more
            (``*``) or one-or-more (``+``) operators in the regex.

    Returns:
        The root node of the tree.
    """
    nodes = []
    tokens = sre_parse.parse(regex)
    for op, args in tokens:
        nodes.append(_to_node(op, args, max_repeat))
    node = Concatenate(nodes)
    if use_optimization:
        return optimize(node)
    return node
