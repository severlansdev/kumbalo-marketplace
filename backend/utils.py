import html

def sanitize_input(text: str) -> str:
    """
    Sanitiza el texto de entrada escapando caracteres HTML para prevenir XSS.
    Ejemplo: '<script>alert("hola")</script>' -> '&lt;script&gt;alert(&quot;hola&quot;)&lt;/script&gt;'
    """
    if not text:
        return text
    return html.escape(str(text))
