"""Regras para decidir se uma mensagem é uma oferta de ar-condicionado
quente e frio com 9.000 BTUs ou mais."""
import re
import unicodedata

BTU_MINIMO = 9000


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


RE_AR = re.compile(r"\bar[\s\-]*cond|\bsplit\b|\bmulti[\s\-]?split\b|\bhi[\s\-]?wall\b")
RE_QUENTE_FRIO = re.compile(
    r"quente\s*(?:e|/|&|-|\+)?\s*frio"
    r"|frio\s*(?:e|/|&|-|\+)\s*quente"
    r"|\bq\s*/\s*f\b"
    r"|ciclo\s+(?:reverso|quente)"
    r"|aquecimento\s+e\s+refrigeracao|refrigeracao\s+e\s+aquecimento"
)
# Ex.: 9000 BTU, 9.000 BTUs, 12 000 btu/h, 9k btus, 9 mil btus, 18.000Btu
RE_BTU = re.compile(
    r"(\d{1,3}(?:[.\s]\d{3})+|\d{4,6}|\d{1,3}(?:[.,]\d+)?\s*(?:k|mil))\s*-?\s*btu"
)
RE_PRECO = re.compile(r"r\$\s*(\d{1,3}(?:\.\d{3})*|\d+)(?:,(\d{2}))?")


def extrair_btus(texto_norm: str) -> list[int]:
    valores = []
    for m in RE_BTU.finditer(texto_norm):
        bruto = m.group(1).replace(" ", "")
        if bruto.endswith(("k", "mil")):
            num = bruto.rstrip("kmil").replace(",", ".")
            valores.append(int(float(num) * 1000))
        else:
            valores.append(int(bruto.replace(".", "")))
    return valores


def extrair_preco(texto_norm: str) -> float | None:
    precos = []
    for m in RE_PRECO.finditer(texto_norm):
        inteiro = int(m.group(1).replace(".", ""))
        centavos = int(m.group(2) or 0)
        precos.append(inteiro + centavos / 100)
    # Em ofertas "de R$ 3.000 por R$ 2.000", o menor costuma ser o preço final
    return min(precos) if precos else None


def avaliar(texto: str, btu_minimo: int = BTU_MINIMO, preco_maximo: float | None = None):
    """Retorna dict com detalhes se a mensagem bate com o filtro, senão None."""
    t = normalizar(texto)
    if not RE_AR.search(t) or not RE_QUENTE_FRIO.search(t):
        return None
    btus = [b for b in extrair_btus(t) if 5000 <= b <= 60000]
    if not btus or max(btus) < btu_minimo:
        return None
    preco = extrair_preco(t)
    if preco_maximo is not None and preco is not None and preco > preco_maximo:
        return None
    return {"btus": max(btus), "preco": preco}
