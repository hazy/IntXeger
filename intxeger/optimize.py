from random import randint

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


def optimize(node: Node, level=10):
    """Traverse the tree return an optimized copy.

    This traverses the tree and applies transforms which are designed to
    improve the sampling speed. Examples of transforms include removing
    unnecessary operations, flattening small nodes, and more.

    Args:
        node: The root node.
        level: The optimization level (higher = more optimization loops).

    Returns:
        The root node of the optimized tree.
    """
    original_node = node

    # Apply the optimizations
    for _ in range(level):
        new_node = _optimize(node)
        if str(node) == str(new_node):
            break
        node = new_node

    # Test the optimized node
    assert node.length == original_node.length
    for _ in range(10):
        i = randint(0, node.length - 1)
        assert node.get(i) == original_node.get(i)

    return node


def _optimize(node: Node):
    if isinstance(node, Group):
        node = Group(_optimize(node.node), node.ref_id)

    if isinstance(node, CharacterClassChoice):
        node = _optimize(node.node)

    elif isinstance(node, Choice):
        node = Choice([_optimize(c) for c in node.choices])
        if len(node.choices) == 1:
            node = node.choices[0]
        elif all(isinstance(c, Choice) for c in node.choices):
            node = Choice([c for n in node.choices for c in n.choices])  # type: ignore

    elif isinstance(node, Concatenate):
        node = Concatenate([_optimize(c) for c in node.nodes])
        if len(node.nodes) == 1:
            node = node.nodes[0]
        elif all(isinstance(c, Constant) for c in node.nodes):
            node = Constant("".join(c.value for c in node.nodes))  # type: ignore

    elif isinstance(node, Repeat):
        node = node.node

    if node.length < 10000:
        is_flat = isinstance(node, Constant) or (
            isinstance(node, Choice)
            and all(isinstance(c, Constant) for c in node.choices)
        )
        skip = isinstance(node, Group) or isinstance(node, GroupRef)
        if not is_flat and not skip:
            node = Choice([Constant(node.get(i)) for i in range(node.length)])
    return node
