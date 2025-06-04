from random import randint
from typing import Any
from enums.roles import Roles
from datetime import datetime, timezone
from jinja2 import Environment, BaseLoader

class TemplateProcessor:
    @staticmethod
    def render_all(texts: list[str], user, message) -> list[str]:
        context = TemplateProcessor._build_context(user, message)
        return [TemplateProcessor._render_jinja(text, context) for text in texts]

    @staticmethod
    def _render(text: str, user, message) -> str:
        context = TemplateProcessor._build_context(user, message)
        return TemplateProcessor._render_jinja(text, context)

    @staticmethod
    def _build_context(user, message) -> dict[str, Any]:
        return {
            "id": user.ID,
            "api": TemplateProcessor._enum_name(user.api),
            "lang": TemplateProcessor._enum_name(user.lang),
            "role": TemplateProcessor._enum_name(user.role),
            "roles": TemplateProcessor._roles_to_list(user.roles),
            "api_fields": user.api_data,
            "tmp_fields": user.tmp,
            "system": {
                "now": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M"),
                "utc": datetime.now(timezone.utc).isoformat(),
                "random": randint(0, 100),
                "version": "1.0.0"
            }
        }

    @staticmethod
    def _roles_to_list(value: Roles) -> list[str]:
        result: list[str] = []
        if not isinstance(value, Roles):
            try:
                value = Roles(value)
            except ValueError:
                return result
        for role in Roles:
            if role == Roles(0):
                continue
            if value & role == role:
                result.append(role.name)
        return result

    @staticmethod
    def _enum_name(value: Any) -> str:
        if isinstance(value, Roles) and value in Roles:
            return value.name
        elif hasattr(value, "name"):
            return value.name
        return str(value)

    @staticmethod
    def _render_jinja(template_str: str, context: dict[str, Any]) -> str:
        env = Environment(
            loader=BaseLoader(),
            autoescape=False,
        )
        template = env.from_string(template_str)
        return template.render(**context)