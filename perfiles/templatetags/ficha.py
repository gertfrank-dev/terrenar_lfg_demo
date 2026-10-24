from django import template

register = template.Library()


@register.filter
def attr(attrs, clave):
    """Lee un atributo con guion (ej. data-bajo) de un diccionario de atributos del widget."""
    return (attrs or {}).get(clave, "")
