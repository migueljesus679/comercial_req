"""
Script para gerar o PDF de exemplo estático.
Executa uma vez: python gerar_exemplo.py
O ficheiro gerado vai para frontend/assets/documento_exemplo.pdf
"""
import os
from fpdf import FPDF

OUTPUT = os.path.join(
    os.path.dirname(__file__),
    "..", "frontend", "assets", "documento_exemplo.pdf"
)


class PDF(FPDF):
    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "Documento de exemplo - Validacao de Documentos Comerciais", align="C")


def gerar():
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(15, 15, 15)

    # Titulo
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 8, "Ficha Tecnica de Equipamento de Impressao", ln=True)
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(0.5)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(3)

    # Caixa de cabecalho
    pdf.set_fill_color(240, 244, 255)
    pdf.set_draw_color(0, 51, 102)
    pdf.set_line_width(0.3)
    y_box = pdf.get_y()
    pdf.rect(15, y_box, 180, 18, style="FD")
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(18, y_box + 2)
    pdf.cell(85, 5, "Marca: Konica Minolta")
    pdf.set_xy(103, y_box + 2)
    pdf.cell(85, 5, "Modelo: AccurioPress C4080")
    pdf.set_xy(18, y_box + 9)
    pdf.cell(85, 5, "Tipo: Impressora Digital de Producao a Cores")
    pdf.set_xy(103, y_box + 9)
    pdf.cell(85, 5, "Data: 24/03/2026   Ref.: KM-APC4080-2026")
    pdf.ln(22)

    COR_TITULO    = (0, 51, 102)
    COR_TH_BG     = (0, 51, 102)
    COR_TH_FG     = (255, 255, 255)
    COR_LINHA_PAR = (244, 248, 255)

    def secao(numero, titulo, linhas):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*COR_TITULO)
        pdf.set_fill_color(230, 237, 255)
        pdf.set_draw_color(*COR_TITULO)
        pdf.set_line_width(0.6)
        pdf.rect(15, pdf.get_y(), 3, 6, style="F")
        pdf.set_x(20)
        pdf.cell(0, 6, f"{numero}. {titulo}", ln=True)
        pdf.ln(1)

        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_fill_color(*COR_TH_BG)
        pdf.set_text_color(*COR_TH_FG)
        pdf.set_draw_color(200, 200, 200)
        pdf.set_line_width(0.2)
        pdf.cell(88, 6, "  Parametro", border=1, fill=True)
        pdf.cell(92, 6, "  Valor", border=1, fill=True, ln=True)

        pdf.set_text_color(0, 0, 0)
        for i, (label, valor) in enumerate(linhas):
            fill = i % 2 == 1
            pdf.set_fill_color(*COR_LINHA_PAR)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(88, 5.5, f"  {label}", border=1, fill=fill)
            pdf.set_font("Helvetica", "", 8.5)
            pdf.cell(92, 5.5, f"  {valor}", border=1, fill=fill, ln=True)
        pdf.ln(4)

    secao(1, "Velocidade de Impressao", [
        ("Impressao a cores (A4)",            "80 ppm (paginas por minuto)"),
        ("Impressao a preto e branco (A4)",   "80 ppm"),
        ("Impressao duplex automatico (A4)",  "60 ppm"),
        ("Formato SRA3",                      "40 ppm"),
    ])
    secao(2, "Qualidade de Impressao", [
        ("Resolucao maxima",    "3600 x 2400 dpi"),
        ("Tecnologia",          "Electrofotografia a laser"),
        ("Reproducao de cor",   "CMYK + Toner especial opcional"),
        ("Profundidade de cor", "8 bits por canal"),
    ])
    secao(3, "Capacidade de Papel", [
        ("Capacidade total de entrada", "8.300 folhas"),
        ("Gramagem suportada",          "52 g/m2 ate 400 g/m2"),
        ("Formatos suportados",         "A6 a SRA3 (320 x 450 mm)"),
        ("Papel couche",                "Sim"),
        ("Envelopes e etiquetas",       "Sim"),
    ])
    secao(4, "Caracteristicas Gerais, Acabamentos e Desempenho", [
        ("Impressao frente e verso (duplex)", "Sim, automatico"),
        ("Conectividade",                     "Ethernet 1 Gbps, USB 3.0"),
        ("Protocolo de impressao",            "PCL6, PostScript 3, PDF 1.7"),
        ("Sistemas operativos compativeis",   "Windows, macOS, Linux"),
        ("Agrafagem automatica",              "Sim (ate 100 folhas)"),
        ("Furacao",                           "Sim (2 e 4 furos)"),
        ("Dobragem",                          "Sim (em Z, cavalete, simples)"),
        ("Volume mensal recomendado",         "Ate 850.000 paginas/mes"),
        ("Volume maximo suportado",           "1.500.000 paginas/mes"),
        ("Tempo de aquecimento",              "Menos de 25 segundos"),
        ("Tempo para primeira pagina",        "Menos de 5 segundos"),
        ("Consumo em funcionamento",          "2,5 kW"),
        ("Consumo em modo de espera",         "0,5 kW"),
        ("Nivel de ruido (em funcionamento)", "65 dB(A)"),
        ("Certificacoes ambientais",          "Energy Star, EPEAT Gold"),
    ])

    pdf.output(OUTPUT)
    print(f"PDF gerado: {os.path.abspath(OUTPUT)}")


if __name__ == "__main__":
    gerar()
