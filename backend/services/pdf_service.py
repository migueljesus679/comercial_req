import io
import re
import pdfplumber

# Palavras que identificam linhas de cabeçalho das tabelas (não são campos)
_CABECALHOS_TABELA = {"condição", "parâmetro", "velocidade", "valor"}


def detectar_estrutura_pdf(conteudo_bytes: bytes) -> list:
    """
    Detecta a estrutura do PDF: lista de tópicos com campos e valores.

    Fase 1 — extract_text(): detecção fiável dos cabeçalhos numerados.
    Fase 2 — extract_words(): extracção de campos usando o maior gap horizontal
              entre palavras consecutivas como separador natural de colunas.

    Retorna: [{"numero": 1, "titulo": "...", "campos": [{"label": "...", "valor": "..."}]}]
    """
    topicos = []
    numeros_vistos = set()
    MIN_GAP_COLUNAS = 10  # pontos PDF mínimos para separador de colunas

    with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
        for pagina in pdf.pages:
            largura = pagina.width

            # ── Fase 1: detecta secções via extract_text() (método mais fiável)
            texto = pagina.extract_text() or ""
            for linha_txt in texto.split("\n"):
                linha_txt = linha_txt.strip()
                m = re.match(r"^(\d{1,2})\.\s+(.{4,80})$", linha_txt)
                if m:
                    num = int(m.group(1))
                    if num not in numeros_vistos and num <= 20:
                        numeros_vistos.add(num)
                        topicos.append({
                            "numero": num,
                            "titulo": m.group(2).strip(),
                            "campos": [],
                        })

            if not topicos:
                continue  # página sem secções — ignora

            # Mapa rápido número → tópico
            secoes_map = {t["numero"]: t for t in topicos}

            # ── Fase 2: extrai campos via extract_words() com detecção de colunas
            palavras = pagina.extract_words(
                keep_blank_chars=False,
                x_tolerance=3,
                y_tolerance=3,
            )

            # Agrupa palavras em linhas pelo eixo Y (tolerância de 5 pontos)
            linhas: list[dict] = []
            for w in sorted(palavras, key=lambda x: (x["top"], x["x0"])):
                encontrou = False
                for linha in linhas:
                    if abs(linha["y"] - w["top"]) < 5:
                        linha["palavras"].append(w)
                        encontrou = True
                        break
                if not encontrou:
                    linhas.append({"y": w["top"], "palavras": [w]})

            linhas.sort(key=lambda l: l["y"])
            for linha in linhas:
                linha["palavras"].sort(key=lambda w: w["x0"])

            secao_atual = None

            for linha in linhas:
                pw = linha["palavras"]
                texto_linha = " ".join(w["text"] for w in pw).strip()

                # ── Verifica se é cabeçalho de secção conhecido
                # (usa startswith para robustez — evita problemas de espaçamento do PDF)
                for num in secoes_map:
                    if texto_linha.startswith(f"{num}.") or texto_linha.startswith(f"{num} ."):
                        secao_atual = num
                        break
                else:
                    # Não é cabeçalho → tenta extrair campo com duas colunas

                    # Maior gap entre palavras consecutivas = separador de colunas
                    max_gap = 0
                    split_x = None
                    for i in range(len(pw) - 1):
                        x1_atual = pw[i].get("x1", pw[i]["x0"])
                        gap = pw[i + 1]["x0"] - x1_atual
                        if gap > max_gap:
                            max_gap = gap
                            split_x = (x1_atual + pw[i + 1]["x0"]) / 2

                    # Sem gap suficiente → linha sem colunas (rodapé, texto contínuo)
                    if split_x is None or max_gap < MIN_GAP_COLUNAS:
                        continue

                    # Primeiro word não perto da margem esq. → texto centrado / rodapé
                    if pw[0]["x0"] > largura * 0.15:
                        continue

                    col_esq = [w["text"] for w in pw if w["x0"] < split_x]
                    col_dir = [w["text"] for w in pw if w["x0"] >= split_x]
                    texto_esq = " ".join(col_esq).strip()
                    texto_dir = " ".join(col_dir).strip()

                    # Salta linhas de cabeçalho das tabelas (ex: "Condição | Velocidade")
                    if (texto_esq.lower() in _CABECALHOS_TABELA or
                            texto_dir.lower() in _CABECALHOS_TABELA):
                        continue

                    # Salta URLs / caminhos de ficheiro (rodapés do browser ao imprimir)
                    if "file://" in texto_esq or texto_esq.lower().startswith("http"):
                        continue

                    # Regista campo
                    if secao_atual and texto_esq and len(texto_esq) > 2 and texto_dir:
                        secoes_map[secao_atual]["campos"].append({
                            "label": texto_esq,
                            "valor": texto_dir,
                        })

    topicos.sort(key=lambda x: x["numero"])
    return topicos


def extrair_texto_pdf(conteudo_bytes: bytes) -> str:
    """Extrai texto de um PDF (incluindo tabelas), recebido em bytes."""
    partes = []

    with pdfplumber.open(io.BytesIO(conteudo_bytes)) as pdf:
        for pagina in pdf.pages:
            # Texto livre
            texto = pagina.extract_text()
            if texto:
                partes.append(texto)

            # Conteúdo de tabelas (importante para fichas técnicas)
            tabelas = pagina.extract_tables()
            for tabela in tabelas:
                for linha in tabela:
                    if linha:
                        celulas = [str(c).strip() for c in linha if c and str(c).strip()]
                        if celulas:
                            partes.append(" | ".join(celulas))

    resultado = "\n".join(partes).strip()

    if not resultado:
        raise ValueError(
            "Não foi possível extrair texto do PDF. "
            "O ficheiro pode ser uma imagem digitalizada (scan)."
        )

    return resultado
