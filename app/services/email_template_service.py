import re
import asyncio
from pathlib import Path


class EmailTemplateService:
    _PLACEHOLDER_PATTERN = re.compile(r"{{\s*(\w+)\s*}}")
    TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "email_templates"

    def __init__(self):
        self._cache: dict[str, str] = {}

    def get_template_path(self, template_name: str, extension: str = "html") -> str:
        path = self.TEMPLATE_DIR / f"{template_name}.{extension}"
        if not path.exists():
            raise FileNotFoundError(f"Email template not found: {path}")
        return str(path)

    async def render_template(
        self,
        template_name: str,
        data: dict,
        strict: bool = False,
        extension: str = "html",
        use_cache: bool = True,
    ) -> str:
        filepath = self.get_template_path(template_name, extension)
        return await self.render_email_from_file(filepath, data, strict=strict, use_cache=use_cache)

    def render_email_template(self, template: str, data: dict, strict: bool = False) -> str:
        """
        Replace placeholders like {{key}} in an HTML email template with values from `data`.
        """
        def replacer(match):
            key = match.group(1)
            if key in data:
                return str(data[key])
            if strict:
                raise KeyError(f"Missing value for placeholder: '{key}'")
            return match.group(0)

        return self._PLACEHOLDER_PATTERN.sub(replacer, template)

    async def render_email_from_file(
        self, filepath: str, data: dict, strict: bool = False, use_cache: bool = True
    ) -> str:
        if use_cache and filepath in self._cache:
            template = self._cache[filepath]
        else:
            template = await asyncio.to_thread(self._read_file, filepath)
            if use_cache:
                self._cache[filepath] = template
        return self.render_email_template(template, data, strict=strict)

    @staticmethod
    def _read_file(filepath: str) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()