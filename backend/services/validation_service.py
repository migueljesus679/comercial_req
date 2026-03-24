"""
Serviço de validação baseado em algoritmo — sem IA externa.
Compara os requisitos do comercial com o conteúdo extraído do PDF.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional

# ─── Grupos de sinónimos ──────────────────────────────────────────────────────
SINONIMOS: Dict[str, List[str]] = {
    "cores": ["cores", "colorido", "cor", "cmyk", "a cores", "color", "policromia", "quadricromia"],
    "preto e branco": ["preto e branco", "p&b", "monocromatico", "mono", "black and white", "b&w", "pb", "monocromo"],
    "duplex": ["duplex", "frente e verso", "frente e costas", "duplex automatico", "impressao duplex", "impressao frente e verso"],
    "agrafagem": ["agrafagem", "agrafar", "agrafadora", "staple", "stapling", "agrafos", "grampo"],
    "furacao": ["furacao", "furo", "furar", "perfuracao", "perfurar", "punch", "furos", "furador"],
    "dobragem": ["dobragem", "dobrar", "dobra", "folding", "fold", "dobradora"],
    "rede": ["rede", "ethernet", "lan", "network", "gigabit", "rj45"],
    "wifi": ["wifi", "wireless", "wi-fi", "sem fios", "802.11"],
    "usb": ["usb", "usb 3.0", "usb 2.0"],
    "postscript": ["postscript", "ps3", "ps 3", "postscript 3"],
    "pdf": ["pdf", "pdf 1.7", "portable document format"],
    "encadernacao": ["encadernacao", "encadernar", "cola quente", "hot glue", "perfect binding", "lombada"],
    "corte": ["corte", "cortar", "aparador", "guilhotina", "trim", "trimmer", "corte de papel"],
    "garantia": ["garantia", "warranty", "suporte tecnico"],
    "automatico": ["automatico", "auto", "automaticamente", "automatizada"],
    "envelope": ["envelopes", "envelope"],
    "etiqueta": ["etiquetas", "etiqueta", "labels", "label"],
    "coche": ["couche", "coated", "papel couche", "papel couchado"],
    "energy star": ["energy star", "energystar"],
}

# ─── Unidades reconhecidas ────────────────────────────────────────────────────
PADROES_UNIDADE = [
    (r"(\d+[\.,]?\d*)\s*ppm\b", "ppm"),
    (r"(\d+[\.,]?\d*)\s*dpi\b", "dpi"),
    (r"(\d+[\.,]?\d*)\s*x\s*(\d+[\.,]?\d*)\s*dpi\b", "dpi_res"),
    (r"(\d+[\.,]?\d*)\s*g\s*[/\/]\s*m[²2]", "g/m2"),
    (r"(\d+[\.,]?\d*)\s*kw\b", "kw"),
    (r"(\d+[\.,]?\d*)\s*db[a]?\b", "db"),
    (r"(\d+[\.,]?\d*)\s*mm\b(?!\s*hg)", "mm"),
    (r"(\d+[\.,]?\d*)\s*segundos?\b", "s"),
    (r"(\d+[\.,]?\d*)\s*(?:anos?|ano)\b", "anos"),
    (r"(\d+[\.,]?\d*)\s*(?:folhas?|paginas?|copias?)\b(?!\s*/\s*m[eê]s)", "folhas"),
    (r"(\d+[\.,]?\d*)\s*000\s*(?:paginas?|folhas?)/mes\b", "kpag_mes"),
    (r"(\d+[\.,]?\d*)\.?000\s*(?:paginas?|folhas?)\s*/\s*mes\b", "kpag_mes"),
]

STOP_WORDS = {
    "de", "a", "o", "e", "com", "em", "para", "por", "que", "se",
    "na", "no", "as", "os", "um", "uma", "ate", "ou", "dos", "das",
    "do", "da", "ao", "mais", "sua", "seu", "ter", "deve", "dever",
    "conter", "incluir", "suportar", "aceitar", "ser", "estar",
    "precisa", "necessita", "requer", "exige", "minimo", "maximo",
    "minima", "maxima", "pelo", "menos", "acima", "abaixo", "superior",
    "inferior", "maior", "menor",
}


def normalizar(texto: str) -> str:
    """Minúsculas + remove acentos."""
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def expandir_sinonimos(texto: str) -> str:
    """Acrescenta termos canónicos ao texto para melhorar o matching."""
    norm = normalizar(texto)
    extras = []
    for canonical, variantes in SINONIMOS.items():
        for v in variantes:
            if normalizar(v) in norm:
                extras.append(normalizar(canonical))
                break
    return norm + " " + " ".join(extras)


def extrair_numeros(texto: str) -> List[Dict]:
    """Extrai pares (valor, unidade) do texto."""
    norm = normalizar(texto)
    resultados = []
    vistos: set = set()

    for padrao, unidade in PADROES_UNIDADE:
        for m in re.finditer(padrao, norm):
            pos = m.start()
            if pos in vistos:
                continue
            vistos.add(pos)
            try:
                if unidade == "dpi_res":
                    # p.ex. "3600 x 2400 dpi" → pegar o maior valor
                    val = max(float(m.group(1).replace(",", ".")),
                              float(m.group(2).replace(",", ".")))
                    unidade_final = "dpi"
                else:
                    val = float(m.group(1).replace(",", "."))
                    unidade_final = unidade
                resultados.append({"valor": val, "unidade": unidade_final, "raw": m.group(0).strip(), "pos": pos})
            except (ValueError, IndexError):
                pass

    return resultados


def detetar_modificador(texto: str, pos: int) -> str:
    """Detecta se é um requisito de mínimo, máximo ou valor exato."""
    janela = normalizar(texto[max(0, pos - 70): pos + 10])
    if any(p in janela for p in ["minimo", "pelo menos", "no minimo", "acima de", "superior a", "maior que", "minima", "pelo menos"]):
        return "min"
    if any(p in janela for p in ["maximo", "no maximo", "ate", "abaixo de", "inferior a", "menor que", "maxima"]):
        return "max"
    return "exato"


def verificar_requisito(linha: str, texto_pdf: str) -> Optional[Dict[str, Any]]:
    """Verifica um requisito individual contra o conteúdo do PDF."""
    # Limpar bullet points e linhas vazias
    linha = re.sub(r"^[\s\-•*►→]+", "", linha).strip()
    if not linha or len(linha) < 4:
        return None

    req_norm = normalizar(linha)
    pdf_norm = normalizar(texto_pdf)
    req_exp = expandir_sinonimos(linha)
    pdf_exp = expandir_sinonimos(texto_pdf)

    # ── Palavras-chave ────────────────────────────────────────────────────────
    tokens = re.split(r"[\s\-\/\(\)\[\]:,;]+", req_norm)
    palavras = [t for t in tokens if t and t not in STOP_WORDS and len(t) > 2 and not re.match(r"^\d+$", t)]

    if not palavras:
        return None

    encontradas, nao_encontradas = [], []
    for p in palavras:
        if p in pdf_exp or p in pdf_norm:
            encontradas.append(p)
        else:
            # Procurar via sinónimos
            achado = False
            for canonical, variantes in SINONIMOS.items():
                norms_v = [normalizar(v) for v in variantes]
                if p in norms_v or p == normalizar(canonical):
                    if any(normalizar(v) in pdf_norm for v in variantes) or normalizar(canonical) in pdf_norm:
                        encontradas.append(p)
                        achado = True
                        break
            if not achado:
                nao_encontradas.append(p)

    ratio_palavras = len(encontradas) / len(palavras)

    # ── Valores numéricos ─────────────────────────────────────────────────────
    nums_req = extrair_numeros(linha)
    nums_pdf = extrair_numeros(texto_pdf)
    confirmacoes: List[str] = []
    problemas: List[str] = []
    nums_ok = 0

    for nr in nums_req:
        mesma_und = [np for np in nums_pdf if np["unidade"] == nr["unidade"]]
        pos_no_texto = linha.lower().find(nr["raw"]) if nr["raw"] in linha.lower() else 0
        mod = detetar_modificador(linha, pos_no_texto)

        if mesma_und:
            valores_pdf = sorted(set(np["valor"] for np in mesma_und))
            melhor = max(valores_pdf)

            if mod == "min":
                if melhor >= nr["valor"]:
                    nums_ok += 1
                    confirmacoes.append(f"Mínimo {nr['valor']} {nr['unidade']} ✓ — PDF tem {melhor} {nr['unidade']}")
                else:
                    problemas.append(f"Requer mínimo {nr['valor']} {nr['unidade']} — PDF tem apenas {melhor} {nr['unidade']}")
            elif mod == "max":
                if melhor <= nr["valor"]:
                    nums_ok += 1
                    confirmacoes.append(f"Máximo {nr['valor']} {nr['unidade']} ✓ — PDF tem {melhor} {nr['unidade']}")
                else:
                    problemas.append(f"Requer máximo {nr['valor']} {nr['unidade']} — PDF tem {melhor} {nr['unidade']}")
            else:
                tolerancia = abs(melhor - nr["valor"]) / max(nr["valor"], 1)
                if tolerancia <= 0.15 or any(abs(v - nr["valor"]) / max(nr["valor"], 1) <= 0.15 for v in valores_pdf):
                    nums_ok += 1
                    confirmacoes.append(f"Valor {nr['valor']} {nr['unidade']} encontrado ✓")
                else:
                    problemas.append(
                        f"Valor {nr['valor']} {nr['unidade']} não encontrado — PDF tem: "
                        + ", ".join(f"{v} {nr['unidade']}" for v in valores_pdf)
                    )
        else:
            problemas.append(f"Sem dados de '{nr['unidade']}' no PDF para verificar {nr['valor']} {nr['unidade']}")

    # ── Score e Status ────────────────────────────────────────────────────────
    total_nums = len(nums_req)
    if total_nums > 0:
        ratio_num = nums_ok / total_nums
        score = round((ratio_palavras * 0.35 + ratio_num * 0.65) * 100)
    else:
        score = round(ratio_palavras * 100)

    if score >= 70 and not problemas and not nao_encontradas:
        status = "CONFORME"
    elif score >= 35 or (total_nums > 0 and nums_ok > 0):
        status = "PARCIAL"
    else:
        status = "NAO_CONFORME"

    return {
        "requisito": linha,
        "status": status,
        "score": score,
        "palavras_encontradas": encontradas,
        "palavras_nao_encontradas": nao_encontradas,
        "confirmacoes": confirmacoes,
        "problemas": problemas,
    }


def validar_documento(texto_pdf: str, texto_requisitos: str) -> Dict[str, Any]:
    """Valida o PDF contra todos os requisitos do comercial."""
    linhas = texto_requisitos.splitlines()
    detalhes = []

    for linha in linhas:
        resultado = verificar_requisito(linha, texto_pdf)
        if resultado:
            detalhes.append(resultado)

    if not detalhes:
        return {"erro": "Nenhum requisito válido encontrado. Escreve os requisitos, um por linha."}

    conformes   = [d for d in detalhes if d["status"] == "CONFORME"]
    parciais    = [d for d in detalhes if d["status"] == "PARCIAL"]
    nao_conf    = [d for d in detalhes if d["status"] == "NAO_CONFORME"]
    total       = len(detalhes)
    score_geral = round(sum(d["score"] for d in detalhes) / total)

    if score_geral >= 70 and not nao_conf:
        status_geral = "CONFORME"
    elif score_geral >= 35:
        status_geral = "PARCIALMENTE CONFORME"
    else:
        status_geral = "NÃO CONFORME"

    return {
        "status_geral": status_geral,
        "score_geral": score_geral,
        "total_requisitos": total,
        "conformes": len(conformes),
        "parciais": len(parciais),
        "nao_conformes": len(nao_conf),
        "detalhes": detalhes,
    }
