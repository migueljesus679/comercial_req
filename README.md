# Validação de Documentos Comerciais

Ferramenta de apoio à equipa comercial para verificar se uma ficha técnica de equipamento cumpre os requisitos de um cliente — de forma rápida, automática e sem margem para erro humano.

---

## O que faz?

Quando um cliente define requisitos para um equipamento de impressão (velocidade, qualidade, acabamentos, etc.), o comercial normalmente tem de comparar manualmente esses requisitos com a ficha técnica do fabricante. Este processo é demorado e sujeito a lapsos.

Esta ferramenta automatiza essa comparação:

1. **Carregas a ficha técnica** do equipamento em PDF
2. **Indicas os requisitos** do cliente — o sistema lê a ficha e preenche os campos automaticamente como ponto de partida
3. **Clicas em Validar** — a ferramenta analisa o documento e diz-te o que está conforme, o que está em falta e o que não cumpre
4. **Vês o resultado** de forma clara, requisito a requisito, com uma pontuação geral de conformidade
5. **Consultas o histórico** de todas as validações anteriores

---

## O que analisa?

A ferramenta consegue verificar, entre outros:

- Velocidade de impressão (ppm)
- Resolução e qualidade de impressão (dpi)
- Capacidade e gramagem de papel (g/m²)
- Funcionalidades como duplex, agrafagem, furação, dobragem
- Conectividade (rede, Wi-Fi, USB)
- Protocolos de impressão (PostScript, PDF…)
- Consumo energético e certificações ambientais
- E qualquer outro dado presente na ficha técnica

---

## Como usar

Acede à ferramenta em: **[link do GitHub Pages]**

Não é necessário instalar nada. Funciona diretamente no browser.

Se precisares de um exemplo de como deve estar formatada a ficha técnica, podes descarregar o modelo disponível no topo da página — tanto em PDF (para referência) como em Word (editável).

---

## Resultado da validação

Cada requisito é classificado como:

- **Conforme** — o equipamento cumpre o requisito
- **Parcial** — cumpre parcialmente ou há informação insuficiente
- **Não conforme** — o equipamento não cumpre o requisito

No final é apresentada uma pontuação geral de conformidade.
