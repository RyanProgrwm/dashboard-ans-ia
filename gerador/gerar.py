"""
gera o projeto power bi (pbip) completo: modelo, relatório, tema e fundos.

uso: python gerador/gerar.py
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modelo  # noqa: E402
import fundos  # noqa: E402
from visuais import (Pagina, gid, s, b, d, cor, col, med, proj, ordem, obj, gradiente, seletor_todos,  # noqa: E402
                     seletor_categoria, filtro_categoria, filtro_top, cartao, segmentacao, botao)

raiz = Path(__file__).resolve().parent.parent
nome = "painel-ans"
pasta_dados = str(raiz / "dados" / "modelo") + "\\"
tema_base_origem = raiz.parent / "powerbi-ans" / "reclamacoes-ans.Report" / "StaticResources" / "SharedResources" / "BaseThemes" / "Fluent2-CY26SU10.json"

# ------------------------------------------------------------------ grade
x0, x1, gap = 256, 1896, 16
cw = x1 - x0

menu = [("visao", "Visão geral", "home"), ("operadoras", "Operadoras", "predio"),
        ("assuntos", "Assuntos", "camadas"), ("perfil", "Perfil", "pessoa"), ("geografia", "Geografia", "mapa")]
nomes_pag = {c: gid("pagina", c) for c in ["visao", "operadoras", "assuntos", "perfil", "geografia", "detalhe", "dica"]}

verde, ambar, vermelho = "#34D399", "#FBBF24", "#F87171"
semaforo = (vermelho, ambar, verde)          # menor é pior (ex.: % resolução)
semaforo_inv = (verde, ambar, vermelho)      # maior é pior (ex.: taxa de reclamação)


def colunas(y, h, larguras):
    """divide a largura útil em painéis lado a lado; larguras são pesos."""
    total = sum(larguras)
    livre = cw - gap * (len(larguras) - 1)
    x, caixas = x0, []
    for i, p in enumerate(larguras):
        w = round(livre * p / total) if i < len(larguras) - 1 else x1 - x
        caixas.append((x, y, w, h))
        x += w + gap
    return caixas


def area(caixa, topo=64):
    x, y, w, h = caixa
    return x + 12, y + topo, w - 24, h - topo - 10


# ------------------------------------------------------------------ objetos comuns
def eixos(categoria=True, valor=False, fonte=10):
    return {"categoryAxis": obj(show=b(categoria), labelColor=cor("#94A3B8"), fontSize=d(fonte),
                                showAxisTitle=b(False), gridlineShow=b(False)),
            "valueAxis": obj(show=b(valor), labelColor=cor("#52627A"), fontSize=d(9), showAxisTitle=b(False),
                             gridlineShow=b(valor), gridlineColor=cor("#1B2540"))}


def rotulos(show=True, cor_txt="#E2E8F0", tamanho=10, unidades=None):
    p = dict(show=b(show), color=cor(cor_txt), fontSize=d(tamanho))
    if unidades is not None:
        p["labelDisplayUnits"] = d(unidades)
    return {"labels": obj(**p)}


def preenchimento(cor_fixa=None, regra=None):
    if regra:
        return {"dataPoint": [{"properties": {"fill": regra}, "selector": seletor_todos()}]}
    return {"dataPoint": obj(fill=cor(cor_fixa))}


def legenda(show=True, posicao="Top"):
    return {"legend": obj(show=b(show), position=s(posicao), labelColor=cor("#CBD5E1"), fontSize=d(10))}


def dica(pagina_dica=True):
    return {"visualTooltip": obj(section=s(nomes_pag["dica"]))} if pagina_dica else {}


def juntar(*dicts):
    r = {}
    for x in dicts:
        r.update(x)
    return r


def navegacao(pg, ativa):
    for i, (chave, _, _) in enumerate(menu):
        if chave != ativa:
            botao(pg, f"nav-{chave}", 16, 144 + i * 52, 200, 44, "PageNavigation", nomes_pag[chave])


def slicers_cabecalho(pg):
    campos = [(col("dOperadora", "Modalidade"), "Modalidade"), (col("dOperadora", "Porte"), "Porte"),
              (col("fReclamacoes", "Tipo de Plano"), "Tipo de plano"), (col("dCalendario", "Mês Ano"), "Mês")]
    w, g = 176, 12
    x = x1 - len(campos) * w - (len(campos) - 1) * g
    for i, (campo, titulo) in enumerate(campos):
        segmentacao(pg, f"slicer-{titulo}", x + i * (w + g), 26, w, 62, campo, titulo)


def faixa_kpis(pg, defs, y=120, h=124):
    caixas = colunas(y, h, [1] * len(defs))
    kpis = []
    for caixa, (rotulo, medida, cor_k, icone, nota, *tam) in zip(caixas, defs):
        x, yy, w, hh = caixa
        kpis.append({"box": caixa, "rotulo": rotulo, "cor": cor_k, "icone": icone, "nota": nota})
        cartao(pg, f"kpi-{medida}", x + 8, yy + 38, w - 16, 54, medida, tamanho=tam[0] if tam else 26)
    return kpis


paginas = []

# =========================================================== 1. visão geral
pg = Pagina("visao")
navegacao(pg, "visao")
slicers_cabecalho(pg)
kpis = faixa_kpis(pg, [
    ("Reclamações", "Reclamações", "cyan", "mensagem", "registradas em 2025"),
    ("Taxa por 10 mil", "Taxa por 10 mil", "violeta", "pulso", "beneficiários por mês"),
    ("% Resolução", "% Resolução", "verde", "check", "entre quem respondeu"),
    ("Resolvidas", "Resolvidas", "azul", "trofeu", "segundo o beneficiário"),
    ("Operadoras", "Operadoras Reclamadas", "ambar", "predio", "com ao menos 1 reclamação"),
    ("Assistenciais", "% Assistencial", "rosa", "coracao", "ligadas a atendimento"),
])
l2 = colunas(260, 380, [2, 1])
p_linha = {"box": l2[0], "nome": "Reclamações por mês", "desc": "Volume mensal · passe o mouse para ver a variação e a taxa",
           "icone": "tendencia", "cor": "cyan"}
xi, yi, wi, hi = l2[1]
p_insight = {"box": (xi, yi, wi, 132), "nome": "Leitura rápida", "desc": "Gerada pelos filtros aplicados",
             "icone": "lampada", "cor": "ambar"}
p_resp = {"box": (xi, yi + 148, wi, hi - 148), "nome": "Resposta do beneficiário", "desc": "Como o caso terminou",
          "icone": "pizza", "cor": "verde"}
l3 = colunas(656, 400, [1, 1])
p_assunto = {"box": l3[0], "nome": "Temas e assuntos", "desc": "Hierarquia tema › assunto · clique para filtrar",
             "icone": "camadas", "cor": "violeta"}
p_top = {"box": l3[1], "nome": "Top 10 operadoras por volume", "desc": "Cor = % de resolução (vermelho pior, verde melhor)",
         "icone": "predio", "cor": "rosa"}

x, y, w, h = area(p_linha["box"])
pg.add("linha", "lineChart", x, y, w, h,
       query={"Category": [proj(col("dCalendario", "Mês Ano"))], "Y": [proj(med("Reclamações"))],
              "Tooltips": [proj(med("Var % Mês")), proj(med("Taxa por 10 mil")), proj(med("% Resolução"))]},
       ordenacao=ordem(col("dCalendario", "Mês Ano"), "Ascending"),
       objetos=juntar(eixos(True, True), legenda(False),
                      {"lineStyles": obj(strokeWidth=d(3), showMarker=b(True), markerSize=d(5), lineChartType=s("smooth"),
                                         areaShow=b(True), shadeTransparency=d(85))},
                      preenchimento("#22D3EE"), rotulos(True, "#CBD5E1", 9, 1000)))
x, y, w, h = area(p_insight["box"], 58)
cartao(pg, "narrativa", x + 4, y, w - 8, h, "Narrativa", tamanho=12, cor_valor="#CBD5E1", fonte="Segoe UI")
x, y, w, h = area(p_resp["box"])
cores_resposta = {"Resolvido": verde, "Cobertura no prazo": "#2DD4BF", "Não resolvido": vermelho,
                  "Cobertura fora do prazo": "#FB923C", "Sem resposta": "#334155"}
pg.add("resposta", "donutChart", x, y, w, h,
       query={"Category": [proj(col("fReclamacoes", "Resposta"))], "Y": [proj(med("Reclamações"))]},
       objetos={"legend": obj(show=b(True), position=s("Right"), labelColor=cor("#CBD5E1"), fontSize=d(10)),
                "labels": obj(show=b(True), labelStyle=s("Percent of total"), color=cor("#E2E8F0"), fontSize=d(9)),
                "dataPoint": [{"properties": {"fill": cor(c)},
                               "selector": seletor_categoria(col("fReclamacoes", "Resposta"), k)}
                              for k, c in cores_resposta.items()]})
x, y, w, h = area(p_assunto["box"])
pg.add("assuntos", "clusteredBarChart", x, y, w, h,
       query={"Category": [proj(col("dAssunto", "Tema")), proj(col("dAssunto", "Assunto"))],
              "Y": [proj(med("Reclamações"))], "Tooltips": [proj(med("% Resolução"))]},
       ordenacao=ordem(med("Reclamações")),
       objetos=juntar(eixos(True, False, 9), preenchimento("#A78BFA"), rotulos(True, "#CBD5E1", 9, 1000)))
x, y, w, h = area(p_top["box"])
pg.add("top10", "clusteredBarChart", x, y, w, h,
       query={"Category": [proj(col("dOperadora", "Operadora"))], "Y": [proj(med("Reclamações"))],
              "Tooltips": [proj(med("% Resolução")), proj(med("Taxa por 10 mil"))]},
       ordenacao=ordem(med("Reclamações")),
       objetos=juntar(eixos(True, False, 9), rotulos(True, "#CBD5E1", 9, 1000),
                      preenchimento(regra=gradiente("% Resolução", semaforo))),
       container=dica(), filtros=[filtro_top("dOperadora", "Operadora", "Reclamações", 10, gid("visao", "top10f"))])
paginas.append(("visao", "Visão geral", pg, {
    "chave": "visao", "titulo": "Visão geral",
    "subtitulo": "325 mil reclamações de beneficiários de planos de saúde registradas na ANS em 2025",
    "paineis": [p_linha, p_insight, p_resp, p_assunto, p_top], "kpis": kpis}))

# =========================================================== 2. operadoras
pg = Pagina("operadoras")
navegacao(pg, "operadoras")
slicers_cabecalho(pg)
esq_w = 880
p_disp = {"box": (x0, 120, esq_w, 520), "nome": "Qualidade (IDSS) × taxa de reclamação",
          "desc": "Operadoras de grande porte · tamanho da bolha = beneficiários", "icone": "dispersao", "cor": "violeta"}
bw = (esq_w - gap) // 2
p_mod = {"box": (x0, 656, bw, 400), "nome": "Taxa por modalidade", "desc": "Reclamações por 10 mil beneficiários/mês",
         "icone": "barras", "cor": "cyan"}
p_porte = {"box": (x0 + bw + gap, 656, esq_w - bw - gap, 400), "nome": "Taxa por porte",
           "desc": "Pequeno < 20 mil · médio até 100 mil · grande > 100 mil", "icone": "barras", "cor": "ambar"}
p_tab = {"box": (x0 + esq_w + gap, 120, cw - esq_w - gap, 936), "nome": "Ranking das operadoras de grande porte",
         "desc": "Ordenado pela taxa · clique com o botão direito para ver o detalhe", "icone": "trofeu", "cor": "rosa"}
filtro_grande = filtro_categoria("dOperadora", "Porte", ["Grande"], gid("operadoras", "fgrande"))

x, y, w, h = area(p_disp["box"])
pg.add("dispersao", "scatterChart", x, y, w, h,
       query={"Category": [proj(col("dOperadora", "Operadora"))], "Series": [proj(col("dOperadora", "Modalidade"))],
              "X": [proj(med("Nota IDSS"))], "Y": [proj(med("Taxa por 10 mil"))], "Size": [proj(med("Total Beneficiários"))]},
       objetos=juntar(legenda(True, "Top"),
                      {"categoryAxis": obj(show=b(True), labelColor=cor("#94A3B8"), showAxisTitle=b(True),
                                           titleColor=cor("#64748B"), gridlineShow=b(True), gridlineColor=cor("#1B2540")),
                       "valueAxis": obj(show=b(True), labelColor=cor("#94A3B8"), showAxisTitle=b(True),
                                        titleColor=cor("#64748B"), gridlineShow=b(True), gridlineColor=cor("#1B2540"))}),
       container=dica(), filtros=[filtro_grande])
x, y, w, h = area(p_mod["box"])
pg.add("modalidade", "clusteredBarChart", x, y, w, h,
       query={"Category": [proj(col("dOperadora", "Modalidade"))], "Y": [proj(med("Taxa por 10 mil"))],
              "Tooltips": [proj(med("Reclamações")), proj(med("Total Beneficiários"))]},
       ordenacao=ordem(med("Taxa por 10 mil")),
       objetos=juntar(eixos(True, False, 9), rotulos(True, "#E2E8F0", 9),
                      preenchimento(regra=gradiente("Taxa por 10 mil", ("#164E63", "#22D3EE")))))
x, y, w, h = area(p_porte["box"])
pg.add("porte", "clusteredColumnChart", x, y, w, h,
       query={"Category": [proj(col("dOperadora", "Porte"))], "Y": [proj(med("Taxa por 10 mil"))],
              "Tooltips": [proj(med("Reclamações")), proj(med("Total Beneficiários"))]},
       ordenacao=ordem(med("Taxa por 10 mil")),
       objetos=juntar(eixos(True, False, 10), rotulos(True, "#E2E8F0", 10), preenchimento("#FBBF24")),
       filtros=[filtro_categoria("dOperadora", "Porte", ["Pequeno", "Médio", "Grande"], gid("operadoras", "fporte"))])
x, y, w, h = area(p_tab["box"])
colunas_tab = ["Reclamações", "Taxa por 10 mil", "Índice vs Mercado", "% Resolução", "Nota IDSS"]
pg.add("ranking", "tableEx", x, y, w, h,
       query={"Values": [proj(col("dOperadora", "Operadora")), proj(col("dOperadora", "Modalidade")),
                         proj(med("Total Beneficiários"), "Beneficiários")] + [proj(med(m)) for m in colunas_tab]},
       ordenacao=ordem(med("Taxa por 10 mil")),
       objetos={"values": [
           {"properties": {"backColor": gradiente("Taxa por 10 mil", ("#0F2A2E", "#7C2D12", "#B91C1C"))},
            "selector": seletor_todos("_Medidas.Taxa por 10 mil")},
           {"properties": {"backColor": gradiente("% Resolução", ("#7F1D1D", "#78350F", "#065F46"))},
            "selector": seletor_todos("_Medidas.% Resolução")},
           {"properties": {"fontColor": gradiente("Nota IDSS", (vermelho, ambar, verde), "asBlank")},
            "selector": seletor_todos("_Medidas.Nota IDSS")},
       ], "total": obj(totals=b(False))},
       container=dica(), filtros=[filtro_categoria("dOperadora", "Porte", ["Grande"], gid("operadoras", "fgrande2"))])
paginas.append(("operadoras", "Operadoras", pg, {
    "chave": "operadoras", "titulo": "Operadoras",
    "subtitulo": "Quem reclama mais quando o tamanho da carteira entra na conta",
    "paineis": [p_disp, p_mod, p_porte, p_tab]}))

# =========================================================== 3. assuntos
pg = Pagina("assuntos")
navegacao(pg, "assuntos")
slicers_cabecalho(pg)
p_mat = {"box": (x0, 120, 1100, 936), "nome": "Mapa de calor: assunto × mês",
         "desc": "Quanto mais intensa a cor, mais reclamações no mês", "icone": "grade", "cor": "cyan"}
dx = x0 + 1100 + gap
dw = x1 - dx
p_res = {"box": (dx, 120, dw, 560), "nome": "% de resolução por assunto", "desc": "Do pior para o melhor",
         "icone": "check", "cor": "verde"}
p_nat = {"box": (dx, 696, dw, 360), "nome": "Natureza da demanda", "desc": "Assistencial × não assistencial",
         "icone": "pizza", "cor": "rosa"}
x, y, w, h = area(p_mat["box"])
pg.add("matriz", "pivotTable", x, y, w, h,
       query={"Rows": [proj(col("dAssunto", "Assunto"))], "Columns": [proj(col("dCalendario", "Mês"))],
              "Values": [proj(med("Reclamações"))]},
       ordenacao=ordem(med("Reclamações")),
       objetos={"values": [{"properties": {"backColor": gradiente("Reclamações", ("#0F172A", "#0E7490", "#22D3EE")),
                                           "fontColorPrimary": cor("#F8FAFC")},
                            "selector": seletor_todos("_Medidas.Reclamações")}]})
x, y, w, h = area(p_res["box"])
pg.add("resolucao", "clusteredBarChart", x, y, w, h,
       query={"Category": [proj(col("dAssunto", "Assunto"))], "Y": [proj(med("% Resolução"))],
              "Tooltips": [proj(med("Reclamações"))]},
       ordenacao=ordem(med("% Resolução"), "Ascending"),
       objetos=juntar(eixos(True, False, 9), rotulos(True, "#E2E8F0", 9),
                      preenchimento(regra=gradiente("% Resolução", semaforo))))
x, y, w, h = area(p_nat["box"])
pg.add("natureza", "donutChart", x, y, w, h,
       query={"Category": [proj(col("fReclamacoes", "Natureza"))], "Y": [proj(med("Reclamações"))]},
       objetos={"legend": obj(show=b(True), position=s("Bottom"), labelColor=cor("#CBD5E1"), fontSize=d(10)),
                "labels": obj(show=b(True), labelStyle=s("Percent of total"), color=cor("#E2E8F0"), fontSize=d(10)),
                "dataPoint": [{"properties": {"fill": cor(c)},
                               "selector": seletor_categoria(col("fReclamacoes", "Natureza"), k)}
                              for k, c in {"Assistencial": "#F472B6", "Não Assistencial": "#A78BFA"}.items()]})
paginas.append(("assuntos", "Assuntos", pg, {
    "chave": "assuntos", "titulo": "Assuntos",
    "subtitulo": "Do que os beneficiários reclamam, mês a mês, e o que costuma ser resolvido",
    "paineis": [p_mat, p_res, p_nat]}))

# =========================================================== 4. perfil
pg = Pagina("perfil")
navegacao(pg, "perfil")
slicers_cabecalho(pg)
l1 = colunas(120, 460, [2, 1])
p_idade = {"box": l1[0], "nome": "Faixa etária (faixas da ANS)", "desc": "Colunas = reclamações · linha = % de resolução",
           "icone": "pessoas", "cor": "cyan"}
p_sexo = {"box": l1[1], "nome": "Sexo do beneficiário", "desc": "Participação no total", "icone": "pessoa", "cor": "rosa"}
l2 = colunas(596, 460, [1, 1, 1])
p_plano = {"box": l2[0], "nome": "Tipo de plano", "desc": "Reclamações por tipo de contratação", "icone": "camadas", "cor": "violeta"}
p_canal = {"box": l2[1], "nome": "Canal de contato", "desc": "Por onde a reclamação chegou à ANS", "icone": "mensagem", "cor": "ambar"}
p_dia = {"box": l2[2], "nome": "Dia da semana", "desc": "Quando as reclamações são abertas", "icone": "calendario", "cor": "verde"}
x, y, w, h = area(p_idade["box"])
pg.add("idade", "lineClusteredColumnComboChart", x, y, w, h,
       query={"Category": [proj(col("dFaixaEtaria", "Faixa Etária"))], "Y": [proj(med("Reclamações"))],
              "Y2": [proj(med("% Resolução"))]},
       ordenacao=ordem(col("dFaixaEtaria", "Faixa Etária"), "Ascending"),
       objetos=juntar(eixos(True, False, 10), legenda(True, "Top"), rotulos(True, "#CBD5E1", 9, 1000),
                      {"dataPoint": [{"properties": {"fill": cor("#22D3EE")}, "selector": {"metadata": "_Medidas.Reclamações"}},
                                     {"properties": {"fill": cor("#FBBF24")}, "selector": {"metadata": "_Medidas.% Resolução"}}],
                       "lineStyles": obj(strokeWidth=d(3), showMarker=b(True), lineChartType=s("smooth"))}))
x, y, w, h = area(p_sexo["box"])
pg.add("sexo", "donutChart", x, y, w, h,
       query={"Category": [proj(col("fReclamacoes", "Sexo"))], "Y": [proj(med("Reclamações"))]},
       objetos={"legend": obj(show=b(True), position=s("Bottom"), labelColor=cor("#CBD5E1"), fontSize=d(10)),
                "labels": obj(show=b(True), labelStyle=s("Percent of total"), color=cor("#E2E8F0"), fontSize=d(10)),
                "dataPoint": [{"properties": {"fill": cor(c)},
                               "selector": seletor_categoria(col("fReclamacoes", "Sexo"), k)}
                              for k, c in {"Feminino": "#F472B6", "Masculino": "#60A5FA", "Não informado": "#334155"}.items()]})
for chave, painel_, campo, cor_b in (("plano", p_plano, col("fReclamacoes", "Tipo de Plano"), "#A78BFA"),
                                     ("canal", p_canal, col("fReclamacoes", "Canal"), "#FBBF24")):
    x, y, w, h = area(painel_["box"])
    pg.add(chave, "clusteredBarChart", x, y, w, h,
           query={"Category": [proj(campo)], "Y": [proj(med("Reclamações"))], "Tooltips": [proj(med("% Resolução"))]},
           ordenacao=ordem(med("Reclamações")),
           objetos=juntar(eixos(True, False, 10), rotulos(True, "#E2E8F0", 10, 1000), preenchimento(cor_b)))
x, y, w, h = area(p_dia["box"])
pg.add("dia", "clusteredColumnChart", x, y, w, h,
       query={"Category": [proj(col("dCalendario", "Dia da Semana"))], "Y": [proj(med("Reclamações"))]},
       ordenacao=ordem(col("dCalendario", "Dia da Semana"), "Ascending"),
       objetos=juntar(eixos(True, False, 10), rotulos(True, "#E2E8F0", 9, 1000), preenchimento("#34D399")))
paginas.append(("perfil", "Perfil", pg, {
    "chave": "perfil", "titulo": "Perfil do beneficiário",
    "subtitulo": "Quem reclama, por qual canal e com que tipo de plano",
    "paineis": [p_idade, p_sexo, p_plano, p_canal, p_dia]}))

# =========================================================== 5. geografia
pg = Pagina("geografia")
navegacao(pg, "geografia")
slicers_cabecalho(pg)
p_uf = {"box": (x0, 120, cw, 470), "nome": "Reclamações por estado do beneficiário",
        "desc": "Cor = % de resolução", "icone": "mapa", "cor": "cyan"}
l2 = colunas(606, 450, [1, 1])
p_tree = {"box": l2[0], "nome": "Região › estado", "desc": "Área proporcional ao volume", "icone": "grade", "cor": "violeta"}
p_reg = {"box": l2[1], "nome": "% de resolução por região", "desc": "Entre quem respondeu", "icone": "check", "cor": "verde"}
x, y, w, h = area(p_uf["box"])
pg.add("uf", "clusteredColumnChart", x, y, w, h,
       query={"Category": [proj(col("dUF", "uf"))], "Y": [proj(med("Reclamações"))],
              "Tooltips": [proj(med("% Resolução"))]},
       ordenacao=ordem(med("Reclamações")),
       objetos=juntar(eixos(True, False, 10), rotulos(True, "#E2E8F0", 9, 1000),
                      preenchimento(regra=gradiente("% Resolução", semaforo))),
       filtros=[filtro_categoria("dUF", "uf", ["ND"], gid("geo", "fnd"), excluir=True)])
x, y, w, h = area(p_tree["box"])
pg.add("treemap", "treemap", x, y, w, h,
       query={"Group": [proj(col("dUF", "Região")), proj(col("dUF", "Estado"))], "Values": [proj(med("Reclamações"))]},
       objetos=juntar(legenda(True, "Top"), rotulos(True, "#0A1020", 10)))
x, y, w, h = area(p_reg["box"])
pg.add("regiao", "clusteredBarChart", x, y, w, h,
       query={"Category": [proj(col("dUF", "Região"))], "Y": [proj(med("% Resolução"))],
              "Tooltips": [proj(med("Reclamações"))]},
       ordenacao=ordem(med("% Resolução")),
       objetos=juntar(eixos(True, False, 11), rotulos(True, "#E2E8F0", 10),
                      preenchimento(regra=gradiente("% Resolução", semaforo))))
paginas.append(("geografia", "Geografia", pg, {
    "chave": "geografia", "titulo": "Geografia",
    "subtitulo": "Onde moram os beneficiários que reclamam (UF informada na reclamação)",
    "paineis": [p_uf, p_tree, p_reg]}))

# =========================================================== 6. detalhe da operadora (drill-through)
pg = Pagina("detalhe")
navegacao(pg, None)
botao(pg, "voltar", x0, 30, 48, 48, "Back")
cartao(pg, "titulo", x0 + 64, 18, cw - 64, 54, "Título Operadora", tamanho=24)
cartao(pg, "subtitulo", x0 + 64, 70, cw - 64, 30, "Subtítulo Operadora", tamanho=11, cor_valor="#94A3B8", fonte="Segoe UI")
kpis_d = faixa_kpis(pg, [
    ("Reclamações", "Reclamações", "cyan", "mensagem", "em 2025"),
    ("Taxa por 10 mil", "Taxa por 10 mil", "violeta", "pulso", "beneficiários por mês"),
    ("Vezes o mercado", "Índice vs Mercado", "rosa", "tendencia", "1,0 = igual à média"),
    ("% Resolução", "% Resolução", "verde", "check", "entre quem respondeu"),
    ("Nota IDSS", "Nota IDSS", "ambar", "escudo", "qualidade ANS (0 a 1)"),
    ("Assunto nº 1", "Assunto Principal", "azul", "camadas", "mais reclamado", 13),
])
faixa = (x0, 260, cw, 84)
cartao(pg, "narrativa", x0 + 64, 270, 1080, 64, "Narrativa", tamanho=13, cor_valor="#E2E8F0", fonte="Segoe UI")
cartao(pg, "ranking", x0 + 1160, 270, cw - 1180, 64, "Ranking Texto", tamanho=13, cor_valor="#22D3EE")
l3 = colunas(360, 696, [1, 1])
p_evol = {"box": l3[0], "nome": "Taxa mensal: operadora × mercado", "desc": "Reclamações por 10 mil beneficiários",
          "icone": "tendencia", "cor": "violeta"}
p_ass = {"box": l3[1], "nome": "Assuntos da operadora", "desc": "Cor = % de resolução", "icone": "camadas", "cor": "cyan"}
x, y, w, h = area(p_evol["box"])
pg.add("evolucao", "lineChart", x, y, w, h,
       query={"Category": [proj(col("dCalendario", "Mês Ano"))],
              "Y": [proj(med("Taxa por 10 mil"), "Operadora"), proj(med("Taxa Mercado"), "Mercado")]},
       ordenacao=ordem(col("dCalendario", "Mês Ano"), "Ascending"),
       objetos=juntar(eixos(True, True), legenda(True, "Top"), rotulos(False),
                      {"lineStyles": obj(strokeWidth=d(3), showMarker=b(True), lineChartType=s("smooth")),
                       "dataPoint": [{"properties": {"fill": cor("#A78BFA")}, "selector": {"metadata": "_Medidas.Taxa por 10 mil"}},
                                     {"properties": {"fill": cor("#64748B")}, "selector": {"metadata": "_Medidas.Taxa Mercado"}}]}))
x, y, w, h = area(p_ass["box"])
pg.add("assuntos", "clusteredBarChart", x, y, w, h,
       query={"Category": [proj(col("dAssunto", "Assunto"))], "Y": [proj(med("Reclamações"))],
              "Tooltips": [proj(med("% Resolução"))]},
       ordenacao=ordem(med("Reclamações")),
       objetos=juntar(eixos(True, False, 9), rotulos(True, "#E2E8F0", 9),
                      preenchimento(regra=gradiente("% Resolução", semaforo))))
voltar_html = (f'<div class="abs" style="left:{x0}px;top:30px;width:48px;height:48px;border-radius:12px;'
               f'border:1px solid #1B2540;background:rgba(20,29,51,.9);display:grid;place-items:center">'
               f'{fundos.svg("voltar", "#22D3EE", 22)}</div>')
paginas.append(("detalhe", "Detalhe da operadora", pg, {
    "chave": "detalhe", "faixas": [faixa], "paineis": [p_evol, p_ass], "kpis": kpis_d,
    "html_extra": [voltar_html,
                   f'<div class="abs" style="left:{x0 + 24}px;top:{260 + 30}px">{fundos.svg("lampada", "#FBBF24", 24)}</div>',
                   '<div class="abs linha" style="left:256px;top:104px;width:1640px"></div>']}))

# =========================================================== 7. dica de ferramenta
pg = Pagina("dica")
cartao(pg, "nome", 12, 8, 376, 40, "Título Operadora", tamanho=13)
for i, (medida, rot) in enumerate((("Taxa por 10 mil", "TAXA/10 MIL"), ("% Resolução", "RESOLUÇÃO"), ("Nota IDSS", "IDSS"))):
    cartao(pg, f"k{i}", 12 + i * 126, 72, 120, 40, medida, tamanho=18)
pg.add("spark", "lineChart", 8, 150, 384, 104,
       query={"Category": [proj(col("dCalendario", "Mês Ano"))], "Y": [proj(med("Reclamações"))]},
       ordenacao=ordem(col("dCalendario", "Mês Ano"), "Ascending"),
       objetos=juntar(eixos(False, False), legenda(False),
                      {"lineStyles": obj(strokeWidth=d(2), showMarker=b(False), lineChartType=s("smooth"),
                                         areaShow=b(True), shadeTransparency=d(80))},
                      preenchimento("#22D3EE")))
dica_html = ['<div class="abs" style="left:0;top:0;width:400px;height:260px;border-radius:0;'
             'background:linear-gradient(180deg,#141D33,#0D1426);border:1px solid #22D3EE55"></div>',
             '<div class="abs" style="left:0;top:0;width:400px;height:3px;background:linear-gradient(90deg,#22D3EE,#A78BFA)"></div>']
for i, rot in enumerate(("TAXA / 10 MIL", "RESOLUÇÃO", "IDSS")):
    dica_html.append(f'<div class="abs" style="left:{12 + i * 126}px;top:56px;width:120px;text-align:center;'
                     f'font-size:9.5px;letter-spacing:1.2px;color:#64748B;font-weight:600">{rot}</div>')
dica_html.append('<div class="abs" style="left:16px;top:128px;font-size:9.5px;letter-spacing:1.2px;color:#64748B;'
                 'font-weight:600">RECLAMAÇÕES POR MÊS</div>')
paginas.append(("dica", "Dica", pg, {"chave": "dica", "menu": False, "html_extra": dica_html}))

# =========================================================== gravação
import gravacao  # noqa: E402

gravacao.gravar(raiz, nome, pasta_dados, paginas, menu, nomes_pag, tema_base_origem)
