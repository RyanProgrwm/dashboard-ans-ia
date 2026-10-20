"""gera o modelo semântico (TMDL) do painel."""
import uuid
from pathlib import Path

ns = uuid.UUID("6f1c2b8e-7a44-4d0e-9a51-3c2f7e9b1a10")


def tag(*partes):
    return str(uuid.uuid5(ns, "/".join(partes)))


# (nome, tipo tmdl, tipo power query, oculta, formato, ordenar por)
tabelas = {
    "fReclamacoes": ("fato_reclamacoes.csv", [
        ("id_demanda", "string", "type text", True, None, None),
        ("data_abertura", "dateTime", "type date", True, "dd/mm/yyyy", None),
        ("id_operadora", "string", "type text", True, None, None),
        ("id_assunto", "int64", "Int64.Type", True, "0", None),
        ("uf", "string", "type text", True, None, None),
        ("id_faixa_etaria", "int64", "Int64.Type", True, "0", None),
        ("Idade", "int64", "Int64.Type", False, "0", None),
        ("Sexo", "string", "type text", False, None, None),
        ("Tipo de Plano", "string", "type text", False, None, None),
        ("Canal", "string", "type text", False, None, None),
        ("Natureza", "string", "type text", False, None, None),
        ("Resposta", "string", "type text", False, None, None),
        ("fl_respondida", "int64", "Int64.Type", True, "0", None),
        ("fl_resolvida", "int64", "Int64.Type", True, "0", None),
    ]),
    "dOperadora": ("dim_operadora.csv", [
        ("id_operadora", "string", "type text", True, None, None),
        ("Operadora", "string", "type text", False, None, None),
        ("Razão Social", "string", "type text", False, None, None),
        ("Modalidade", "string", "type text", False, None, None),
        ("UF Sede", "string", "type text", False, None, None),
        ("Situação", "string", "type text", False, None, None),
        ("Beneficiários", "int64", "Int64.Type", False, "#,0", None),
        ("Porte", "string", "type text", False, None, None),
        ("IDSS", "double", "type number", False, "0.000", None),
        ("Faixa IDSS", "string", "type text", False, None, None),
    ]),
    "dAssunto": ("dim_assunto.csv", [
        ("id_assunto", "int64", "Int64.Type", True, "0", None),
        ("Assunto", "string", "type text", False, None, None),
        ("Tema", "string", "type text", False, None, None),
        ("Grupo", "string", "type text", False, None, None),
        ("Assunto Completo", "string", "type text", True, None, None),
    ]),
    "dFaixaEtaria": ("dim_faixa_etaria.csv", [
        ("id_faixa_etaria", "int64", "Int64.Type", True, "0", None),
        ("Faixa Etária", "string", "type text", False, None, "id_faixa_etaria"),
    ]),
    "dUF": ("dim_uf.csv", [
        ("uf", "string", "type text", False, None, None),
        ("Estado", "string", "type text", False, None, None),
        ("Região", "string", "type text", False, None, None),
    ]),
}

relacionamentos = [
    ("fReclamacoes", "id_operadora", "dOperadora", "id_operadora"),
    ("fReclamacoes", "id_assunto", "dAssunto", "id_assunto"),
    ("fReclamacoes", "id_faixa_etaria", "dFaixaEtaria", "id_faixa_etaria"),
    ("fReclamacoes", "uf", "dUF", "uf"),
    ("fReclamacoes", "data_abertura", "dCalendario", "Data"),
]

calendario = """
var _ini = date(year(min(fReclamacoes[data_abertura])), 1, 1)
var _fim = date(year(max(fReclamacoes[data_abertura])), 12, 31)
return
    addcolumns(
        selectcolumns(calendar(_ini, _fim), "Data", [Date]),
        "Ano", year([Data]),
        "Mês Num", month([Data]),
        "Mês", format([Data], "mmm"),
        "Ano Mês Num", year([Data]) * 100 + month([Data]),
        "Mês Ano", format([Data], "mmm/yy"),
        "Trimestre", "T" & quarter([Data]),
        "Dia Semana Num", weekday([Data], 2),
        "Dia da Semana", format([Data], "ddd")
    )
"""

colunas_calendario = [
    ("Data", "dd/mm/yyyy", None, False),
    ("Ano", "0", None, False),
    ("Mês Num", "0", None, True),
    ("Mês", None, "Mês Num", False),
    ("Ano Mês Num", "0", None, True),
    ("Mês Ano", None, "Ano Mês Num", False),
    ("Trimestre", None, None, False),
    ("Dia Semana Num", "0", None, True),
    ("Dia da Semana", None, "Dia Semana Num", False),
]

# (nome, formato, pasta de exibição, expressão)
medidas = [
    ("Reclamações", "#,0", "Volume", "countrows(fReclamacoes)"),
    ("Respondidas", "#,0", "Volume", "sum(fReclamacoes[fl_respondida])"),
    ("Resolvidas", "#,0", "Volume", "sum(fReclamacoes[fl_resolvida])"),
    ("Meses", "0", "Apoio", "distinctcount(dCalendario[Ano Mês Num])"),
    ("Média Mensal", "#,0", "Volume", "divide([Reclamações], [Meses])"),
    ("Operadoras Reclamadas", "#,0", "Volume", "distinctcount(fReclamacoes[id_operadora])"),
    ("% Resolução", "0.0%;-0.0%;0.0%", "Qualidade", "divide([Resolvidas], [Respondidas])"),
    ("% Resposta", "0.0%;-0.0%;0.0%", "Qualidade", "divide([Respondidas], [Reclamações])"),
    ("% Assistencial", "0.0%;-0.0%;0.0%", "Volume",
     'divide(calculate([Reclamações], fReclamacoes[Natureza] = "Assistencial"), [Reclamações])'),
    ("Total Beneficiários", "#,0", "Taxa", "sum(dOperadora[Beneficiários])"),
    ("Taxa por 10 mil", "0.00", "Taxa", """
// reclamações por 10 mil beneficiários por mês (mesma lógica do IGR da ANS)
divide([Reclamações], [Total Beneficiários] * [Meses]) * 10000
"""),
    ("Taxa Mercado", "0.00", "Taxa", "calculate([Taxa por 10 mil], removefilters(dOperadora))"),
    ("Índice vs Mercado", "0.0", "Taxa", "divide([Taxa por 10 mil], [Taxa Mercado])"),
    ("Nota IDSS", "0.000", "Qualidade", """
if(hasonevalue(dOperadora[id_operadora]), max(dOperadora[IDSS]))
"""),
    ("Reclamações Mês Anterior", "#,0", "Tempo",
     "calculate([Reclamações], dateadd(dCalendario[Data], -1, month))"),
    ("Var % Mês", "+0.0%;-0.0%;0.0%", "Tempo", """
var _ant = [Reclamações Mês Anterior]
return if(not isblank(_ant), divide([Reclamações] - _ant, _ant))
"""),
    ("Assunto Principal", None, "Texto", """
var _top = topn(1, values(dAssunto[Assunto]), [Reclamações])
return maxx(_top, dAssunto[Assunto])
"""),
    ("% Assunto Principal", "0.0%;-0.0%;0.0%", "Texto", """
var _a = [Assunto Principal]
return divide(calculate([Reclamações], dAssunto[Assunto] = _a), [Reclamações])
"""),
    ("Total Grande Porte", "0", "Ranking", """
calculate(distinctcount(dOperadora[id_operadora]), removefilters(dOperadora), dOperadora[Porte] = "Grande")
"""),
    ("Ranking Taxa", "0", "Ranking", """
// posição da operadora entre as de grande porte (1 = maior taxa de reclamação)
var _id = selectedvalue(dOperadora[id_operadora])
var _taxa = [Taxa por 10 mil]
var _tab =
    calculatetable(
        addcolumns(values(dOperadora[id_operadora]), "@taxa", calculate([Taxa por 10 mil])),
        removefilters(dOperadora),
        dOperadora[Porte] = "Grande"
    )
return
    if(
        not isblank(_id) && selectedvalue(dOperadora[Porte]) = "Grande",
        countrows(filter(_tab, [@taxa] > _taxa)) + 1
    )
"""),
    ("Ranking Texto", None, "Ranking", """
var _r = [Ranking Taxa]
return
    if(
        isblank(_r),
        "fora do ranking de grande porte",
        _r & "ª maior taxa entre " & [Total Grande Porte] & " operadoras de grande porte"
    )
"""),
    ("Título Operadora", None, "Texto", """
selectedvalue(dOperadora[Operadora], "Selecione uma operadora")
"""),
    ("Subtítulo Operadora", None, "Texto", """
if(
    hasonevalue(dOperadora[id_operadora]),
    selectedvalue(dOperadora[Modalidade]) & "  ·  porte " & lower(selectedvalue(dOperadora[Porte]))
        & "  ·  sede em " & selectedvalue(dOperadora[UF Sede])
        & "  ·  " & format([Total Beneficiários], "#,0") & " beneficiários"
)
"""),
    ("Narrativa", None, "Texto", """
var _a = [Assunto Principal]
var _p = [% Assunto Principal]
var _t = [Taxa por 10 mil]
var _m = [Taxa Mercado]
return
    "O assunto mais reclamado é " & _a & " (" & format(_p, "0.0%") & " do total). "
        & "A taxa é de " & format(_t, "0.00") & " reclamações por 10 mil beneficiários por mês"
        & if(
            hasonevalue(dOperadora[id_operadora]),
            ", contra " & format(_m, "0.00") & " do mercado.",
            "."
        )
"""),
]


def coluna_tmdl(nome, tipo, oculta, formato, ordenar):
    linhas = [f"\tcolumn '{nome}'", f"\t\tdataType: {tipo}"]
    if formato:
        linhas.append(f"\t\tformatString: {formato}")
    if oculta:
        linhas.append("\t\tisHidden")
    linhas += [f"\t\tlineageTag: {tag('col', nome)}", "\t\tsummarizeBy: none", f"\t\tsourceColumn: {nome}"]
    if ordenar:
        linhas.append(f"\t\tsortByColumn: '{ordenar}'")
    linhas += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
    return "\n".join(linhas)


def tabela_csv(nome, arquivo, colunas):
    tipos = ", ".join('{"%s", %s}' % (c[0], c[2]) for c in colunas)
    m = f"""let
				    Fonte = Csv.Document(File.Contents(PastaDados & "{arquivo}"), [Delimiter = ";", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
				    Cabecalhos = Table.PromoteHeaders(Fonte, [PromoteAllScalars = true]),
				    Tipos = Table.TransformColumnTypes(Cabecalhos, {{{tipos}}}, "en-US")
				in
				    Tipos"""
    corpo = [f"table {nome}", f"\tlineageTag: {tag('tab', nome)}", ""]
    for c in colunas:
        corpo.append(coluna_tmdl(c[0], c[1], c[3], c[4], c[5]))
    corpo += [f"\tpartition {nome} = m", "\t\tmode: import", "\t\tsource =", f"\t\t\t\t{m}", "",
              "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(corpo)


def bloco(expr, nivel):
    pre = "\t" * nivel
    linhas = expr.strip("\n").split("\n")
    return "```\n" + "\n".join(pre + l for l in linhas) + "\n" + pre + "```"


def tabela_medidas():
    corpo = ["table _Medidas", f"\tlineageTag: {tag('tab', '_Medidas')}", ""]
    for nome, formato, pasta, expr in medidas:
        corpo.append(f"\tmeasure '{nome}' = {bloco(expr, 3)}")
        if formato:
            corpo.append(f"\t\tformatString: {formato}")
        corpo += [f"\t\tdisplayFolder: {pasta}", f"\t\tlineageTag: {tag('med', nome)}", ""]
    corpo += ["\tpartition _Medidas = m", "\t\tmode: import", "\t\tsource =",
              "\t\t\t\tlet",
              '\t\t\t\t    Fonte = #table(type table [Coluna = text], {}),',
              '\t\t\t\t    SemColunas = Table.RemoveColumns(Fonte, {"Coluna"})',
              "\t\t\t\tin",
              "\t\t\t\t    SemColunas", "",
              "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(corpo)


def tabela_calendario():
    corpo = ["table dCalendario", f"\tlineageTag: {tag('tab', 'dCalendario')}", "\tdataCategory: Time", ""]
    for nome, formato, ordenar, oculta in colunas_calendario:
        linhas = [f"\tcolumn '{nome}'"]
        if nome == "Data":
            linhas.append("\t\tisKey")
        if formato:
            linhas.append(f"\t\tformatString: {formato}")
        if oculta:
            linhas.append("\t\tisHidden")
        linhas += [f"\t\tlineageTag: {tag('cal', nome)}", "\t\tsummarizeBy: none", "\t\tisNameInferred",
                   f"\t\tsourceColumn: [{nome}]"]
        if ordenar:
            linhas.append(f"\t\tsortByColumn: '{ordenar}'")
        linhas += ["", "\t\tannotation SummarizationSetBy = Automatic", ""]
        corpo.append("\n".join(linhas))
    corpo += ["\tpartition dCalendario = calculated", "\t\tmode: import", f"\t\tsource = {bloco(calendario, 4)}", ""]
    return "\n".join(corpo)


def gerar(destino: Path, nome: str, pasta_dados: str):
    sm = destino / f"{nome}.SemanticModel"
    d = sm / "definition"
    (d / "tables").mkdir(parents=True, exist_ok=True)

    (sm / ".platform").write_text("""{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "SemanticModel",
    "displayName": "%s"
  },
  "config": {
    "version": "2.0",
    "logicalId": "%s"
  }
}""" % (nome, tag("sm", nome)), encoding="utf-8")
    (sm / "definition.pbism").write_text('{\n  "version": "4.2",\n  "settings": {}\n}', encoding="utf-8")
    (d / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1606\n\n", encoding="utf-8")

    ordem = ["fReclamacoes", "dOperadora", "dAssunto", "dFaixaEtaria", "dUF", "dCalendario", "_Medidas"]
    model = ["model Model", "\tculture: pt-BR", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tsourceQueryCulture: pt-BR", "\tdataAccessOptions", "\t\tlegacyRedirects",
             "\t\treturnErrorValuesAsNull", "",
             "annotation __PBI_TimeIntelligenceEnabled = 0", "",
             'annotation PBI_QueryOrder = ["PastaDados","fReclamacoes","dOperadora","dAssunto","dFaixaEtaria","dUF","_Medidas"]',
             ""]
    model += [f"ref table {t}" for t in ordem] + [""]
    (d / "model.tmdl").write_text("\n".join(model), encoding="utf-8")

    (d / "expressions.tmdl").write_text(
        f'expression PastaDados = "{pasta_dados}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]\n'
        f"\tlineageTag: {tag('exp', 'PastaDados')}\n\n"
        "\tannotation PBI_ResultType = Text\n\n", encoding="utf-8")

    for nome_tab, (arquivo, colunas) in tabelas.items():
        (d / "tables" / f"{nome_tab}.tmdl").write_text(tabela_csv(nome_tab, arquivo, colunas), encoding="utf-8")
    (d / "tables" / "dCalendario.tmdl").write_text(tabela_calendario(), encoding="utf-8")
    (d / "tables" / "_Medidas.tmdl").write_text(tabela_medidas(), encoding="utf-8")

    rel = []
    for de_t, de_c, para_t, para_c in relacionamentos:
        rel += [f"relationship {tag('rel', de_t, de_c)}", f"\tfromColumn: {de_t}.'{de_c}'",
                f"\ttoColumn: {para_t}.'{para_c}'", ""]
    (d / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")
