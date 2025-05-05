import os
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Define la ruta a la carpeta donde están las plantillas
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura el entorno de Jinja2
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['html', 'xml'])
)

def render_template(template_name: str, context: dict) -> str:
    template_file = f"{template_name}.html"
    try:
        template = env.get_template(template_file)
        return template.render(**context)
    except Exception as e:
        logger.error(f"Error al renderizar la plantilla '{template_file}': {e}")
        raise
