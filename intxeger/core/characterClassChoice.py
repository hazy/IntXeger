from typing import Sequence

from intxeger.core import Node, Choice


class CharacterClassChoice(Node):
    def __init__(self, node: Choice):
        self.node = node
        self.length = self.node.length

    def get(self, idx: int):
        return self.node.get(idx)

    def __str__(self):
        return (
            "CharacterClassChoice(\n  "
            + "\n".join(str(c) for c in self.node.choices).replace("\n", "\n  ")
            + "\n)"
        )
