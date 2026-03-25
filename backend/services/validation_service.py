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
    (r"(\d+[\.,]?\d*)\s*[x×]\s*(\d+[\.,]?\d*)\s*dpi\b", "dpi_res"),
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


def comparar_campo(label: str, valor_usuario: str, valor_pdf: str) -> Optional[Dict[str, Any]]:
    """Compara o valor inserido pelo utilizador com o valor extraído do PDF para um campo específico."""
    req = normalizar(valor_usuario.strip())
    pdf = normalizar(valor_pdf.strip())

    if not req:
        return None

    base = {"requisito": f"{label}: {valor_usuario}"}

    # Determina se o valor tem texto (letras) ou é puramente numérico
    tem_letras = bool(re.search(r'[a-zA-Z]', req))

    # 1. Correspondência de texto: só se o valor tem letras, ≥3 chars, e está contido no PDF
    if tem_letras and len(req) >= 3 and req in pdf:
        return {**base,
            "status": "CONFORME", "score": 100,
            "palavras_encontradas": [], "palavras_nao_encontradas": [],
            "confirmacoes": [f"✓ '{valor_usuario}' corresponde ao PDF ('{valor_pdf}')"],
            "problemas": []}

    problemas: List[str] = []
    confirmacoes: List[str] = []

    # 2. Valores numéricos com unidade reconhecida (ex: "60 ppm", "400 g/m²", "3600×2400 dpi")
    nums_req = extrair_numeros(valor_usuario)
    nums_pdf_campo = extrair_numeros(valor_pdf)

    for nr in nums_req:
        mesma_und = [np for np in nums_pdf_campo if np["unidade"] == nr["unidade"]]
        if mesma_und:
            melhor = max(np["valor"] for np in mesma_und)
            if abs(melhor - nr["valor"]) / max(nr["valor"], 1) > 0.05:
                problemas.append(f"PDF tem {melhor} {nr['unidade']}, não {nr['valor']} {nr['unidade']}")
            else:
                confirmacoes.append(f"✓ {nr['valor']} {nr['unidade']}")
        else:
            problemas.append(f"'{nr['raw']}' não encontrado — PDF indica: '{valor_pdf}'")

    if problemas:
        return {**base,
            "status": "NAO_CONFORME", "score": 0,
            "palavras_encontradas": confirmacoes, "palavras_nao_encontradas": [],
            "confirmacoes": confirmacoes, "problemas": problemas}

    # 3. Valor puramente numérico sem unidade reconhecida (ex: "12", "1200x1900")
    #    Compara via extrair_numeros do campo PDF — nunca por substrings de dígitos
    e_puramente_numerico = not tem_letras and bool(re.search(r'\d', req))
    if e_puramente_numerico and not nums_req:
        if not nums_pdf_campo:
            # Campo do PDF não tem valores numéricos com unidade → número não faz sentido aqui
            return {**base,
                "status": "NAO_CONFORME", "score": 0,
                "palavras_encontradas": [], "palavras_nao_encontradas": [],
                "confirmacoes": [],
                "problemas": [f"'{valor_usuario}' não corresponde — campo contém: '{valor_pdf}'"]}
        numeros_float = []
        for n in re.findall(r"\d+[\.,]?\d*", req):
            try:
                numeros_float.append(float(n.replace(",", ".")))
            except ValueError:
                pass
        valores_pdf = [np["valor"] for np in nums_pdf_campo]
        for n_user in numeros_float:
            if not any(abs(v - n_user) / max(n_user, 0.001) <= 0.05 for v in valores_pdf):
                return {**base,
                    "status": "NAO_CONFORME", "score": 0,
                    "palavras_encontradas": [], "palavras_nao_encontradas": [],
                    "confirmacoes": [],
                    "problemas": [f"Valor '{valor_usuario}' não corresponde — PDF indica: '{valor_pdf}'"]}
        return {**base,
            "status": "CONFORME", "score": 100,
            "palavras_encontradas": [], "palavras_nao_encontradas": [],
            "confirmacoes": [f"✓ Valor {valor_usuario} verificado"],
            "problemas": []}

    # 4. Palavras-chave — comparadas apenas contra o valor do campo (não o PDF todo)
    tokens = re.split(r"[\s\-\/\(\)\[\]:,;×x+]+", req)
    palavras = [t for t in tokens if t and t not in STOP_WORDS and len(t) > 2 and not re.match(r"^\d+$", t)]

    if not palavras:
        if confirmacoes:
            return {**base,
                "status": "CONFORME", "score": 100,
                "palavras_encontradas": [], "palavras_nao_encontradas": [],
                "confirmacoes": confirmacoes, "problemas": []}
        return {**base,
            "status": "NAO_CONFORME", "score": 0,
            "palavras_encontradas": [], "palavras_nao_encontradas": [],
            "confirmacoes": [],
            "problemas": [f"'{valor_usuario}' não corresponde ao PDF ('{valor_pdf}')"]}

    encontradas = [p for p in palavras if p in pdf]
    nao_encontradas = [p for p in palavras if p not in pdf]

    if nao_encontradas:
        return {**base,
            "status": "NAO_CONFORME",
            "score": round(len(encontradas) / len(palavras) * 100),
            "palavras_encontradas": encontradas,
            "palavras_nao_encontradas": nao_encontradas,
            "confirmacoes": confirmacoes,
            "problemas": [f"'{valor_usuario}' não corresponde — campo do PDF contém: '{valor_pdf}'"]}

    return {**base,
        "status": "CONFORME", "score": 100,
        "palavras_encontradas": encontradas, "palavras_nao_encontradas": [],
        "confirmacoes": confirmacoes + [f"✓ Valor verificado"],
        "problemas": []}


def validar_campos_estruturados(topicos: list, requisitos_texto: str) -> Dict[str, Any]:
    """Valida campo a campo: compara o valor do utilizador com o valor do PDF para cada campo."""
    # Mapa: label normalizado → valor extraído do PDF
    mapa_pdf: Dict[str, str] = {}
    for topico in topicos:
        for campo in topico.get("campos", []):
            chave = normalizar(campo["label"])
            mapa_pdf[chave] = campo["valor"]

    detalhes = []
    for linha in requisitos_texto.splitlines():
        if ":" not in linha:
            continue
        partes = linha.split(":", 1)
        label = partes[0].strip()
        valor_usuario = partes[1].strip()
        if not valor_usuario:
            continue

        label_norm = normalizar(label)
        valor_pdf = mapa_pdf.get(label_norm)

        if not valor_pdf:
            detalhes.append({
                "requisito": linha,
                "status": "PARCIAL", "score": 50,
                "palavras_encontradas": [], "palavras_nao_encontradas": [],
                "confirmacoes": [],
                "problemas": [f"Campo '{label}' não encontrado na estrutura do PDF"],
            })
            continue

        resultado = comparar_campo(label, valor_usuario, valor_pdf)
        if resultado:
            detalhes.append(resultado)

    if not detalhes:
        return {"erro": "Nenhum requisito válido encontrado. Preenche pelo menos um campo."}

    conformes = [d for d in detalhes if d["status"] == "CONFORME"]
    parciais  = [d for d in detalhes if d["status"] == "PARCIAL"]
    nao_conf  = [d for d in detalhes if d["status"] == "NAO_CONFORME"]
    total     = len(detalhes)
    score_geral = round(sum(d["score"] for d in detalhes) / total)

    if not nao_conf and not parciais:
        status_geral = "CONFORME"
    elif score_geral >= 50:
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
