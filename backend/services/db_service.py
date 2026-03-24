import json
import os
from supabase import create_client, Client


def get_client() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_KEY têm de estar configurados no .env")
    return create_client(url, key)


def guardar_validacao(
    nome_ficheiro: str,
    conteudo_pdf: str,
    requisitos: str,
    resultado: dict,
) -> dict:
    """Guarda o registo completo de uma validação na base de dados."""
    client = get_client()

    registo = {
        "nome_ficheiro": nome_ficheiro,
        "conteudo_pdf": conteudo_pdf[:5000],
        "requisitos": requisitos,
        "status_geral": resultado.get("status_geral", "DESCONHECIDO"),
        "score_geral": resultado.get("score_geral", 0),
        "total_requisitos": resultado.get("total_requisitos", 0),
        "conformes": resultado.get("conformes", 0),
        "parciais": resultado.get("parciais", 0),
        "nao_conformes": resultado.get("nao_conformes", 0),
        "detalhes": json.dumps(resultado.get("detalhes", []), ensure_ascii=False),
    }

    resposta = client.table("validacoes").insert(registo).execute()
    return resposta.data[0] if resposta.data else registo


def listar_validacoes(limite: int = 20) -> list:
    """Lista as últimas validações guardadas."""
    client = get_client()
    resposta = (
        client.table("validacoes")
        .select("id, created_at, nome_ficheiro, status_geral, score_geral, total_requisitos, conformes, parciais, nao_conformes")
        .order("created_at", desc=True)
        .limit(limite)
        .execute()
    )
    return resposta.data or []


def obter_validacao(validacao_id: str) -> dict | None:
    """Obtém o detalhe completo de uma validação pelo ID."""
    client = get_client()
    resposta = (
        client.table("validacoes")
        .select("*")
        .eq("id", validacao_id)
        .single()
        .execute()
    )
    if resposta.data and isinstance(resposta.data.get("detalhes"), str):
        try:
            resposta.data["detalhes"] = json.loads(resposta.data["detalhes"])
        except (json.JSONDecodeError, TypeError):
            pass
    return resposta.data
