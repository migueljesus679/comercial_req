from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from services.pdf_service import extrair_texto_pdf, detectar_estrutura_pdf
from services.validation_service import validar_documento
from services.db_service import guardar_validacao, listar_validacoes, obter_validacao

load_dotenv()

app = FastAPI(title="Validação de Documentos Comerciais", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def raiz():
    return {"status": "online", "mensagem": "API de Validação de Documentos Comerciais v2"}


@app.post("/api/extrair-topicos")
async def extrair_topicos_endpoint(ficheiro: UploadFile = File(...)):
    """Recebe um PDF e devolve a estrutura de tópicos com campos e valores."""
    if not ficheiro.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas ficheiros PDF são aceites.")
    conteudo_bytes = await ficheiro.read()
    if len(conteudo_bytes) == 0:
        raise HTTPException(status_code=400, detail="O ficheiro PDF está vazio.")
    try:
        topicos = detectar_estrutura_pdf(conteudo_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")
    return {"sucesso": True, "topicos": topicos}


@app.post("/api/validar")
async def validar_documento_endpoint(
    ficheiro: UploadFile = File(...),
    requisitos: str = Form(...),
):
    """Recebe um PDF e os requisitos, analisa e devolve o resultado."""
    if not ficheiro.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas ficheiros PDF são aceites.")

    if not requisitos.strip():
        raise HTTPException(status_code=400, detail="Os requisitos não podem estar vazios.")

    conteudo_bytes = await ficheiro.read()
    if len(conteudo_bytes) == 0:
        raise HTTPException(status_code=400, detail="O ficheiro PDF está vazio.")

    # Extrair texto do PDF
    try:
        texto_pdf = extrair_texto_pdf(conteudo_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar PDF: {str(e)}")

    # Validar com algoritmo (sem IA)
    resultado = validar_documento(texto_pdf, requisitos)

    if "erro" in resultado:
        raise HTTPException(status_code=422, detail=resultado["erro"])

    # Guardar na base de dados (não bloqueia em caso de erro)
    registo_id = None
    try:
        registo = guardar_validacao(
            nome_ficheiro=ficheiro.filename,
            conteudo_pdf=texto_pdf,
            requisitos=requisitos,
            resultado=resultado,
        )
        registo_id = registo.get("id")
    except Exception as e:
        print(f"Aviso: Não foi possível guardar na BD: {e}")

    return {
        "sucesso": True,
        "nome_ficheiro": ficheiro.filename,
        "resultado": resultado,
        "id": registo_id,
    }


@app.get("/api/historico")
def historico(limite: int = 20):
    """Devolve o historial das últimas validações."""
    try:
        registos = listar_validacoes(limite)
        return {"sucesso": True, "dados": registos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/validacao/{validacao_id}")
def detalhe_validacao(validacao_id: str):
    """Devolve o detalhe completo de uma validação."""
    try:
        registo = obter_validacao(validacao_id)
        if not registo:
            raise HTTPException(status_code=404, detail="Validação não encontrada.")
        return {"sucesso": True, "dados": registo}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
