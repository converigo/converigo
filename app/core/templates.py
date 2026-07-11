from fastapi.templating import Jinja2Templates

from app.core.template_context import build_template_context


templates = Jinja2Templates(directory="app/templates")


def template_context(request) -> dict:
    context = build_template_context()
    context["request"] = request
    return context


def get_template_globals() -> dict:
    return build_template_context()


templates.env.globals.update({"get_template_globals": get_template_globals})
