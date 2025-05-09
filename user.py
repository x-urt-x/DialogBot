from api_ids import ApiId
from dataclasses import dataclass, field
from typing import Any
from roles import Roles

@dataclass
class User:
    role: Roles = Roles.USER
    availableRoles = Roles.USER
    tmp_fields: dict[ApiId, Any] = field(default_factory=dict)