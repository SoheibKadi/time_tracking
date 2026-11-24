import io
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

_template_dir = Path(__file__).parent.parent / "templates"
_jinja_env = Environment(loader=FileSystemLoader(str(_template_dir)))


def render_invoice_pdf(context: dict) -> bytes:
    """Render the invoice Jinja2 template to PDF bytes."""
    template = _jinja_env.get_template("invoice.html")
    html_str = template.render(**context)
    buf = io.BytesIO()
    HTML(string=html_str).write_pdf(buf)
    return buf.getvalue()
