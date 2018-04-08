#!/usr/bin/env python3
"""Generate the syntax tree data structures from their spec.

Run `generate_syntax_trees.sh` rather than this script directly.
"""
import sys
import textwrap
from typing import List, Mapping, Optional

from sttools import Child, get_exports, get_node_types, NodeType, TOKEN_TYPE


PREAMBLE = """\
\"\"\"NOTE: This file auto-generated from ast.txt.

Run `bin/generate_syntax_trees.sh` to re-generate. Do not edit!
\"\"\"
from typing import List, Optional, Sequence, Union

import pytch.greencst as greencst
from .lexer import Token


class Node:
    def __init__(
        self,
        parent: Optional["Node"],
    ) -> None:
        self._parent = parent

    @property
    def parent(self) -> Optional["Node"]:
        return self._parent

    @property
    def children(self) -> Sequence[Union["Node", Optional["Token"]]]:
        raise NotImplementedError("should be implemented by children")


"""


def main() -> None:
    lines = sys.stdin.read().splitlines()
    sections = get_node_types(lines)
    class_defs = [
        get_class_def(name, sections, children)
        for name, children
        in sections.items()
    ]
    exports = get_exports(sections.keys())
    sys.stdout.write(PREAMBLE)
    sys.stdout.write("\n\n".join(class_defs) + "\n\n")
    sys.stdout.write(get_green_to_red_node_map(sections) + "\n\n")
    sys.stdout.write(exports)


def get_green_to_red_node_map(
    node_types: Mapping[NodeType, List[Child]],
) -> str:
    map = "GREEN_TO_RED_NODE_MAP = {\n"
    for node_type in node_types:
        node_class = node_type.name
        map += f"    {node_class}: greencst.{node_class},\n"
    map += "}\n"
    return map


def get_class_def(
    node_type: NodeType,
    node_types: Mapping[NodeType, List[Child]],
    children: List[Child],
) -> str:
    node_types = {
        NodeType(name=k.name, supertype=None): v
        for k, v in node_types.items()
    }

    def get_leaf_children(base_type: NodeType) -> Optional[List[Child]]:
        children = node_types.get(base_type, [])
        if len(children) > 0:
            return children
        return None

    # class name
    class_header = f"class {node_type.name}"
    if node_type.supertype:
        class_header += f"({node_type.supertype})"
    class_header += ":\n"

    if not children:
        class_body = textwrap.indent("pass\n", prefix="    ")
        return class_header + class_body

    # __init__
    init_header = "def __init__(\n"
    init_header += f"    self,\n"
    init_header += f"    parent: Optional[Node],\n"
    init_header += f"    origin: greencst.{node_type.name},\n"
    init_header += f") -> None:\n"
    init_header = textwrap.indent(init_header, prefix="    ")
    class_header += init_header

    # __init__ body
    init_body = "super().__init__(parent)\n"
    init_body += "self.origin = origin\n"
    init_body = textwrap.indent(init_body, prefix="    " * 2)
    class_header += init_body

    # class body
    class_body = ""
    for child in children:
        property_body = "\n"
        property_body += "@property\n"
        property_body += f"def {child.name}(self) -> {child.type.name}:\n"

        leaf_children = get_leaf_children(child.base_type)
        if child.base_type == TOKEN_TYPE:
            # Tokens don't need to construct a new red node.
            property_body += f"    return self.origin.{child.name}\n"
        elif leaf_children is not None:
            # A specific class to construct, like `FunctionCallExpr`.
            property_body += f"    return {child.base_type}(\n"
            property_body += f"        parent=self,\n"
            property_body += f"        origin=self.origin.{child.name},\n"
            property_body += f"    )\n"
        else:
            property_body += f"    if self.origin.{child.name} is None:\n"
            property_body += f"        return None\n"
            property_body += f"    return GREEN_TO_RED_NODE_MAP[" + \
                f"self.origin.{child.name}.__class__](\n"
            property_body += f"        parent=self,\n"
            property_body += f"        origin=self.origin.{child.name},\n"
            property_body += f"    )\n"

        class_body += textwrap.indent(property_body, prefix="    ")

    children_prop_body = "\n"
    children_prop_body += f"@property\n"
    children_prop_body += \
        f"def children(self) -> List[Optional[Union[Token, Node]]]:\n"
    children_prop_body += f"    return [\n"
    for child in children:
        if child.is_sequence_type:
            children_prop_body += f"        *self.{child.name},\n"
        elif child.is_optional_sequence_type:
            children_prop_body += (
                f"        *(self.{child.name} " +
                f"if self.{child.name} is not None else []),\n"
            )
        else:
            children_prop_body += f"        self.{child.name},\n"
    children_prop_body += "    ]\n"
    class_body += textwrap.indent(children_prop_body, prefix="    ")

    return class_header + class_body


if __name__ == "__main__":
    main()
