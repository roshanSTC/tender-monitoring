from jinja2 import Environment
from jinja2 import FileSystemLoader


class TemplateService:

    env = Environment(
        loader=FileSystemLoader(
            "templates"
        )
    )

    @staticmethod
    def render(
        template_name,
        **kwargs,
    ):

        template = (
            TemplateService.env.get_template(
                template_name
            )
        )

        return template.render(
            **kwargs
        )