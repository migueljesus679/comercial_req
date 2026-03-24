# Validação de Documentos Comerciais

Programa de demonstração para validar documentos técnicos de impressoras para gráficas.
**Sem IA externa — funciona com algoritmo próprio, sem custos.**

## Estrutura do Projeto

```
├── backend/
│   ├── main.py                      # API FastAPI (endpoints)
│   ├── requirements.txt             # Dependências Python
│   ├── .env.example                 # Template das variáveis de ambiente
│   └── services/
│       ├── pdf_service.py           # Extração de texto do PDF
│       ├── validation_service.py    # Algoritmo de comparação (sem IA)
│       └── db_service.py            # Operações na base de dados (Supabase)
└── frontend/
    ├── index.html                   # Interface principal
    ├── css/style.css                # Estilos
    └── js/app.js                    # Lógica do frontend
```

---

## Configuração — Passo a Passo

### 1. Base de Dados — Supabase (gratuito)

1. Cria uma conta em https://supabase.com (gratuito)
2. Cria um novo projeto
3. No painel do projeto, vai a **SQL Editor** e executa:

```sql
CREATE TABLE validacoes (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  nome_ficheiro TEXT NOT NULL,
  conteudo_pdf TEXT,
  requisitos TEXT NOT NULL,
  status_geral TEXT NOT NULL,
  score_geral INTEGER DEFAULT 0,
  total_requisitos INTEGER DEFAULT 0,
  conformes INTEGER DEFAULT 0,
  parciais INTEGER DEFAULT 0,
  nao_conformes INTEGER DEFAULT 0,
  detalhes TEXT
);
```

4. Vai a **Project Settings → API** e copia:
   - `Project URL` (ex: `https://xxxxxxxxxxx.supabase.co`)
   - `anon public` key

### 2. Configurar o Backend

Na pasta `backend/`, cria um ficheiro `.env` (copia de `.env.example`):

```env
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> **Nota:** A base de dados é opcional para a demo. Se não configurares o `.env`,
> o programa valida na mesma — só não guarda o histórico.

### 3. Instalar Dependências Python

Abre o terminal na pasta `backend/` e executa:

```bash
python -m pip install -r requirements.txt
```

### 4. Iniciar o Backend

```bash
cd backend
python main.py
```

O servidor arranca em `http://localhost:8000`

### 5. Abrir o Frontend

Abre o ficheiro `frontend/index.html` diretamente no browser.

---

## Como Usar

1. **Seleciona o PDF** — arrasta ou clica para escolher a ficha técnica da impressora
2. **Escreve os requisitos** — um por linha, p.ex.:
   ```
   - Velocidade mínima de 60 ppm
   - Impressão a cores e a preto e branco
   - Resolução mínima de 1200 dpi
   - Suporte para papel até 350 g/m²
   - Impressão duplex automático
   ```
3. **Clica em "Validar Documento"** — o algoritmo analisa o PDF e compara com os requisitos
4. **Vê o resultado** — resultado por requisito com score de conformidade
5. **Histórico** — consulta validações anteriores no separador "Histórico"

---

## Como funciona o algoritmo

Para cada requisito escrito pelo comercial, o algoritmo:

1. **Extrai palavras-chave** do requisito (ignora preposições e verbos genéricos)
2. **Detecta valores numéricos** com unidades (ppm, dpi, g/m², kW, anos…)
3. **Detecta modificadores** — "mínimo de X", "máximo de X", ou valor exato
4. **Pesquisa no PDF** — palavras diretas + tabela de sinónimos (cores/CMYK, duplex/frente-e-verso, etc.)
5. **Compara numericamente** — com tolerância de 15% para valores exatos
6. **Classifica cada requisito:** CONFORME / PARCIAL / NÃO CONFORME

---

## API Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | `/api/validar` | Valida um PDF contra os requisitos |
| GET | `/api/historico` | Lista as últimas 20 validações |
| GET | `/api/validacao/{id}` | Detalhe de uma validação |
