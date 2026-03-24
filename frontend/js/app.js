const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000"
  : "https://RENDER_APP_NAME.onrender.com";

// Tópicos extraídos do PDF — preenchidos após upload
let topicosDinamicos = null;

// ── Formulário dinâmico (gerado a partir do PDF) ───────────────────────────────
function gerarFormularioDinamico(topicos) {
  topicosDinamicos = topicos;
  const container = document.getElementById("topicos-container");
  container.innerHTML = "";

  if (!topicos || topicos.length === 0) {
    container.innerHTML = `<p class="req-instrucao" style="color:#e94560;text-align:center;padding:16px">
      Não foi possível detectar secções no PDF. O ficheiro pode estar em formato de imagem (scan).
    </p>`;
    return;
  }

  topicos.forEach((topico) => {
    const section = document.createElement("div");
    section.className = "topico-section open";
    section.id = "sec_t" + topico.numero;

    const header = document.createElement("div");
    header.className = "topico-header";
    header.innerHTML = `
      <span class="topico-titulo">${topico.numero}. ${escHTML(topico.titulo)}</span>
      <span class="topico-count" id="count_t${topico.numero}"></span>
      <span class="topico-chevron">&#9660;</span>
    `;
    header.addEventListener("click", () => section.classList.toggle("open"));

    const body = document.createElement("div");
    body.className = "topico-body";

    (topico.campos || []).forEach((campo, fi) => {
      const inputId = `campo_t${topico.numero}_${fi}`;
      const row = document.createElement("div");
      row.className = "campo-row";
      row.innerHTML = `
        <label for="${inputId}">${escHTML(campo.label)}</label>
        <div class="campo-input-group">
          <input
            type="text"
            id="${inputId}"
            placeholder="ex: mínimo ${escHTML(campo.valor)}"
            autocomplete="off"
          />
          <span class="campo-pdf-ref">Ficha técnica: <strong>${escHTML(campo.valor)}</strong></span>
        </div>
      `;
      row.querySelector("input").addEventListener("input", () =>
        atualizarContagem(topico.numero)
      );
      body.appendChild(row);
    });

    section.appendChild(header);
    section.appendChild(body);
    container.appendChild(section);
  });
}

function atualizarContagem(topicoNum) {
  const inputs = document.querySelectorAll(`[id^="campo_t${topicoNum}_"]`);
  const n = Array.from(inputs).filter((el) => el.value.trim() !== "").length;
  const el = document.getElementById("count_t" + topicoNum);
  if (!el) return;
  if (n > 0) {
    el.textContent = n + " preenchido" + (n > 1 ? "s" : "");
    el.className = "topico-count tem-dados";
  } else {
    el.textContent = "";
    el.className = "topico-count";
  }
}

function coletarRequisitos() {
  if (!topicosDinamicos) return "";
  const linhas = [];
  topicosDinamicos.forEach((topico) => {
    (topico.campos || []).forEach((campo, fi) => {
      const el = document.getElementById(`campo_t${topico.numero}_${fi}`);
      const val = el?.value?.trim();
      if (val) linhas.push(`${campo.label}: ${val}`);
    });
  });
  return linhas.join("\n");
}

function limparTudo() {
  document.querySelectorAll("#topicos-container input[type='text']").forEach((el) => {
    el.value = "";
  });
  if (topicosDinamicos) {
    topicosDinamicos.forEach((t) => atualizarContagem(t.numero));
  }
}

function expandirTodos(expandir) {
  document.querySelectorAll(".topico-section").forEach((s) => {
    if (expandir) s.classList.add("open");
    else s.classList.remove("open");
  });
  const btn = document.getElementById("btn-expandir-todos");
  btn.textContent = expandir ? "Recolher todos" : "Expandir todos";
  btn._expandido = expandir;
}

// ── Navegação por tabs ────────────────────────────────────────────────────────
document.querySelectorAll("nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "tab-historico") carregarHistorico();
  });
});

// ── Upload PDF ────────────────────────────────────────────────────────────────
const uploadArea   = document.getElementById("upload-area");
const fileInput    = document.getElementById("file-input");
const filenameSpan = document.getElementById("filename");

uploadArea.addEventListener("click", () => fileInput.click());
uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("dragover");
});
uploadArea.addEventListener("dragleave", () => uploadArea.classList.remove("dragover"));
uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("dragover");
  if (e.dataTransfer.files[0]) definirFicheiro(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) definirFicheiro(fileInput.files[0]);
});

async function definirFicheiro(file) {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    mostrarErro("Apenas ficheiros PDF são aceites.");
    return;
  }
  fileInput._file = file;
  filenameSpan.textContent = file.name;
  filenameSpan.style.display = "block";
  esconderErro();

  // Analisar estrutura do PDF e construir formulário
  const container = document.getElementById("topicos-container");
  container.innerHTML = `<p class="req-instrucao" style="text-align:center;padding:20px;color:#888">
    A analisar estrutura do PDF...
  </p>`;

  try {
    const formData = new FormData();
    formData.append("ficheiro", file);
    const resp = await fetch(`${API_BASE}/api/extrair-topicos`, { method: "POST", body: formData });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Erro ao analisar PDF");
    }
    const dados = await resp.json();
    gerarFormularioDinamico(dados.topicos || []);
  } catch (err) {
    container.innerHTML = `<p class="req-instrucao" style="color:#e94560;text-align:center;padding:16px">
      Erro ao analisar PDF: ${escHTML(err.message)}
    </p>`;
  }
}

// ── Botões auxiliares ─────────────────────────────────────────────────────────
document.getElementById("btn-expandir-todos").addEventListener("click", function () {
  expandirTodos(!this._expandido);
});
document.getElementById("btn-limpar-tudo").addEventListener("click", () => {
  if (confirm("Limpar todos os campos preenchidos?")) limparTudo();
});

// ── Submissão ─────────────────────────────────────────────────────────────────
document.getElementById("form-validacao").addEventListener("submit", async (e) => {
  e.preventDefault();

  const file       = fileInput.files[0] || fileInput._file;
  const requisitos = coletarRequisitos();

  if (!file)       { mostrarErro("Por favor seleciona um ficheiro PDF."); return; }
  if (!requisitos) { mostrarErro("Por favor preenche pelo menos um campo de requisito."); return; }

  esconderErro();
  esconderResultado();
  mostrarLoading(true);
  document.getElementById("btn-validar").disabled = true;

  try {
    const formData = new FormData();
    formData.append("ficheiro", file);
    formData.append("requisitos", requisitos);

    const resp  = await fetch(`${API_BASE}/api/validar`, { method: "POST", body: formData });
    const dados = await resp.json();

    if (!resp.ok) throw new Error(dados.detail || "Erro desconhecido na API.");

    mostrarResultado(dados);
  } catch (err) {
    mostrarErro("Erro: " + err.message);
  } finally {
    mostrarLoading(false);
    document.getElementById("btn-validar").disabled = false;
  }
});

// ── Utilitários de UI ─────────────────────────────────────────────────────────
function mostrarLoading(v) {
  document.getElementById("loading").style.display = v ? "block" : "none";
}
function mostrarErro(msg) {
  const el = document.getElementById("erro-box");
  el.textContent = msg;
  el.style.display = "block";
}
function esconderErro()      { document.getElementById("erro-box").style.display = "none"; }
function esconderResultado() { document.getElementById("resultado-container").style.display = "none"; }

// ── Mostrar resultado ─────────────────────────────────────────────────────────
function mostrarResultado(dados) {
  const r = dados.resultado;
  const container = document.getElementById("resultado-container");

  document.getElementById("res-ficheiro").textContent = dados.nome_ficheiro;

  const clsMap = {
    "CONFORME": "status-CONFORME",
    "PARCIALMENTE CONFORME": "status-PARCIALMENTE",
    "NÃO CONFORME": "status-NAO_CONFORME",
  };
  const badge = document.getElementById("status-badge");
  badge.textContent = r.status_geral;
  badge.className   = "status-badge " + (clsMap[r.status_geral] || "status-PARCIALMENTE");

  document.getElementById("res-score").textContent          = r.score_geral;
  document.getElementById("stat-total").textContent         = r.total_requisitos;
  document.getElementById("stat-conformes").textContent     = r.conformes;
  document.getElementById("stat-parciais").textContent      = r.parciais;
  document.getElementById("stat-nao-conformes").textContent = r.nao_conformes;

  // Constrói mapa label → tópico a partir dos tópicos dinâmicos
  const topicoMap = {};
  if (topicosDinamicos) {
    topicosDinamicos.forEach((t) => {
      (t.campos || []).forEach((c) => {
        topicoMap[c.label.toLowerCase()] = `${t.numero}. ${t.titulo}`;
      });
    });
  }

  // Agrupa resultados por tópico
  const grupos = {};
  (r.detalhes || []).forEach((d) => {
    const labelPart = d.requisito.split(":")[0].trim().toLowerCase();
    let grupoTitulo = "Outros";
    for (const [label, titulo] of Object.entries(topicoMap)) {
      if (labelPart === label || labelPart.includes(label) || label.includes(labelPart)) {
        grupoTitulo = titulo;
        break;
      }
    }
    if (!grupos[grupoTitulo]) grupos[grupoTitulo] = [];
    grupos[grupoTitulo].push(d);
  });

  const lista = document.getElementById("lista-detalhes");
  lista.innerHTML = "";
  const iconMap = { CONFORME: "✅", PARCIAL: "⚠️", NAO_CONFORME: "❌" };

  Object.entries(grupos).forEach(([titulo, itens]) => {
    const grupoDiv = document.createElement("div");
    grupoDiv.className = "resultado-grupo";

    const grupoHeader = document.createElement("div");
    grupoHeader.className = "resultado-grupo-titulo";
    grupoHeader.textContent = titulo;
    grupoDiv.appendChild(grupoHeader);

    itens.forEach((d) => {
      const item = document.createElement("div");
      item.className = `req-item status-${d.status}`;

      const partes    = d.requisito.split(":");
      const labelText = partes[0]?.trim() || d.requisito;
      const valorText = partes.slice(1).join(":").trim();

      let bodyHtml = "";

      // O que foi pedido
      if (valorText) {
        bodyHtml += `<p class="secao-titulo">O que foi pedido</p>
          <ul class="ok"><li>${escHTML(valorText)}</li></ul>`;
      }

      // Confirmações (sempre visíveis no verde)
      if (d.confirmacoes?.length) {
        bodyHtml += `<p class="secao-titulo">Confirmações</p><ul class="ok">`;
        d.confirmacoes.forEach((c) => { bodyHtml += `<li>${c}</li>`; });
        bodyHtml += `</ul>`;
      } else if (d.status === "CONFORME") {
        bodyHtml += `<p class="secao-titulo">Confirmações</p>
          <ul class="ok"><li>Conteúdo verificado no documento</li></ul>`;
      }

      // Problemas
      if (d.problemas?.length) {
        bodyHtml += `<p class="secao-titulo">Problemas / Em falta</p><ul class="nok">`;
        d.problemas.forEach((p) => { bodyHtml += `<li>${p}</li>`; });
        bodyHtml += `</ul>`;
      }
      if (d.palavras_nao_encontradas?.length) {
        bodyHtml += `<p class="secao-titulo">Palavras não encontradas</p><ul class="info">`;
        d.palavras_nao_encontradas.forEach((p) => { bodyHtml += `<li>${p}</li>`; });
        bodyHtml += `</ul>`;
      }
      if (!bodyHtml) bodyHtml = `<p style="color:#aaa;font-size:0.83rem">Sem detalhes adicionais.</p>`;

      item.innerHTML = `
        <div class="req-header">
          <span class="req-icon">${iconMap[d.status] || "◦"}</span>
          <span class="req-label">${escHTML(labelText)}</span>
          ${valorText ? `<span class="req-valor-esp">${escHTML(valorText)}</span>` : ""}
          <span class="req-score-pill">${d.score}%</span>
          <span class="req-chevron">&#9660;</span>
        </div>
        <div class="req-body">${bodyHtml}</div>
      `;
      item.querySelector(".req-header").addEventListener("click", () =>
        item.classList.toggle("open")
      );
      grupoDiv.appendChild(item);
    });

    lista.appendChild(grupoDiv);
  });

  container.style.display = "block";
  container.scrollIntoView({ behavior: "smooth" });
}

function escHTML(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ── Histórico ─────────────────────────────────────────────────────────────────
async function carregarHistorico() {
  const tbody = document.getElementById("tabela-historico");
  tbody.innerHTML = '<tr><td colspan="6" class="sem-dados">A carregar...</td></tr>';

  try {
    const resp  = await fetch(`${API_BASE}/api/historico`);
    const dados = await resp.json();
    if (!resp.ok) throw new Error(dados.detail);

    if (!dados.dados?.length) {
      tbody.innerHTML = '<tr><td colspan="6" class="sem-dados">Sem validações registadas.</td></tr>';
      return;
    }

    tbody.innerHTML = "";
    dados.dados.forEach((item) => {
      const tr  = document.createElement("tr");
      const dt  = new Date(item.created_at).toLocaleString("pt-PT");
      const cls = { "CONFORME": "pill-CONFORME", "PARCIALMENTE CONFORME": "pill-PARCIALMENTE", "NÃO CONFORME": "pill-NAO_CONFORME" }[item.status_geral] || "pill-PARCIALMENTE";
      tr.innerHTML = `
        <td>${dt}</td>
        <td>${item.nome_ficheiro}</td>
        <td><span class="pill ${cls}">${item.status_geral}</span></td>
        <td><strong>${item.score_geral ?? "-"}%</strong></td>
        <td>${item.total_requisitos ?? "-"}</td>
        <td><button class="btn-detalhe" onclick="verDetalhe('${item.id}')">Ver</button></td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="6" class="sem-dados">Erro: ${err.message}</td></tr>`;
  }
}

// ── Modal detalhe ─────────────────────────────────────────────────────────────
async function verDetalhe(id) {
  const modal    = document.getElementById("modal-overlay");
  const conteudo = document.getElementById("modal-conteudo");
  conteudo.innerHTML = "<p>A carregar...</p>";
  modal.classList.add("open");

  try {
    const resp  = await fetch(`${API_BASE}/api/validacao/${id}`);
    const dados = await resp.json();
    if (!resp.ok) throw new Error(dados.detail);

    const d    = dados.dados;
    const dt   = new Date(d.created_at).toLocaleString("pt-PT");
    const cls  = { "CONFORME": "status-CONFORME", "PARCIALMENTE CONFORME": "status-PARCIALMENTE", "NÃO CONFORME": "status-NAO_CONFORME" }[d.status_geral] || "status-PARCIALMENTE";
    const iconMap = { CONFORME: "✅", PARCIAL: "⚠️", NAO_CONFORME: "❌" };

    const detalhes = typeof d.detalhes === "string" ? JSON.parse(d.detalhes) : (d.detalhes || []);
    let detalhesHtml = "";
    detalhes.forEach((req) => {
      const partes = req.requisito.split(":");
      const lbl = partes[0]?.trim();
      const val = partes.slice(1).join(":").trim();
      const cor = req.status === "CONFORME" ? "#28a745" : req.status === "PARCIAL" ? "#ffc107" : "#dc3545";
      detalhesHtml += `
        <div style="border-left:3px solid ${cor};padding:6px 10px;margin-bottom:6px;background:#fafafa;border-radius:0 4px 4px 0">
          <span style="font-size:0.85rem;font-weight:600">${iconMap[req.status] || ""} ${escHTML(lbl)}</span>
          ${val ? `<span style="font-size:0.82rem;color:#666;margin-left:8px">— ${escHTML(val)}</span>` : ""}
          <span style="float:right;font-size:0.78rem;color:#888">${req.score}%</span>
          ${req.confirmacoes?.length ? `<div style="font-size:0.8rem;color:#28a745;margin-top:3px">${req.confirmacoes.map((c) => "✓ " + c).join("<br>")}</div>` : (req.status === "CONFORME" ? `<div style="font-size:0.8rem;color:#28a745;margin-top:3px">✓ Conteúdo verificado no documento</div>` : "")}
          ${req.problemas?.length ? `<div style="font-size:0.8rem;color:#dc3545;margin-top:3px">${req.problemas.map((p) => "✗ " + p).join("<br>")}</div>` : ""}
        </div>`;
    });

    conteudo.innerHTML = `
      <p><strong>Ficheiro:</strong> ${d.nome_ficheiro}</p>
      <p style="margin-top:4px"><strong>Data:</strong> ${dt}</p>
      <hr style="margin:12px 0;border:none;border-top:1px solid #eee">
      <p>
        <strong>Resultado:</strong>
        <span class="status-badge ${cls}" style="margin-left:8px">${d.status_geral}</span>
        <span style="margin-left:12px;font-size:1.1rem;font-weight:700">${d.score_geral}%</span>
      </p>
      <p style="margin:6px 0 14px;font-size:0.82rem;color:#888">
        Total: ${d.total_requisitos} &nbsp;|&nbsp; Conformes: ${d.conformes} &nbsp;|&nbsp;
        Parciais: ${d.parciais} &nbsp;|&nbsp; Não conformes: ${d.nao_conformes}
      </p>
      <hr style="margin:12px 0;border:none;border-top:1px solid #eee">
      <p style="margin-bottom:10px"><strong>Detalhe por requisito:</strong></p>
      ${detalhesHtml}
    `;
  } catch (err) {
    conteudo.innerHTML = `<p style="color:red">Erro: ${err.message}</p>`;
  }
}

document.getElementById("modal-close").addEventListener("click", () => {
  document.getElementById("modal-overlay").classList.remove("open");
});
document.getElementById("modal-overlay").addEventListener("click", (e) => {
  if (e.target === document.getElementById("modal-overlay"))
    document.getElementById("modal-overlay").classList.remove("open");
});

// ── Estado inicial ─────────────────────────────────────────────────────────────
document.getElementById("topicos-container").innerHTML = `
  <p class="req-instrucao" style="text-align:center;padding:24px;color:#aaa">
    Carrega um ficheiro PDF para ver os campos de validação.
  </p>
`;
