from typing import TypedDict
from enums.roles import Roles

class NodesRootIDs(TypedDict):
    roots: dict[Roles, int]
    nodes: dict[int, dict]