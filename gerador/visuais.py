"""helpers para montar o json dos visuais no formato PBIR."""
import hashlib

schema_visual = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.14.0/schema.json"
medidas = "_Medidas"


def gid(*partes):
    return hashlib.md5("/".join(partes).encode("utf-8")).hexdigest()[:20]


# ------------------------------------------------------------------ literais
def lit(valor):
    return {"expr": {"Literal": {"Value": valor}}}


def s(texto):
    return lit("'" + str(texto).replace("'", "''") + "'")


def b(valor):
    return lit("true" if valor else "false")


def d(numero):
    return lit(f"{numero}D")


def cor(hexa):
    return {"solid": {"color": s(hexa)}}


# ------------------------------------------------------------------ campos
def col(entidade, prop):
    return {"Column": {"Expression": {"SourceRef": {"Entity": entidade}}, "Property": prop}}


def med(prop):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": medidas}}, "Property": prop}}


def ref(campo):
    c = campo.get("Column") or campo.get("Measure")
    return f"{c['Expression']['SourceRef']['Entity']}.{c['Property']}"


def proj(campo, nome=None):
    p = {"field": campo, "queryRef": ref(campo), "nativeQueryRef": nome or ref(campo).split(".", 1)[1]}
    if nome:
        p["displayName"] = nome
    if "Column" in campo:
        p["active"] = True
    return p


def ordem(campo, direcao="Descending"):
    return {"sort": [{"field": campo, "direction": direcao}]}


# ------------------------------------------------------------------ formatação condicional
def gradiente(medida, cores, nulo="asZero"):
    """cores: (min, max) ou (min, meio, max)."""
    regra = {"linearGradient2" if len(cores) == 2 else "linearGradient3": {}}
    chave = next(iter(regra))
    nomes = ("min", "max") if len(cores) == 2 else ("min", "mid", "max")
    for n, c in zip(nomes, cores):
        regra[chave][n] = {"color": {"Literal": {"Value": f"'{c}'"}}}
    regra[chave]["nullColoringStrategy"] = {"strategy": {"Literal": {"Value": f"'{nulo}'"}}}
    return {"solid": {"color": {"expr": {"FillRule": {"Input": med(medida), "FillRule": regra}}}}}


def seletor_todos(metadata=None):
    sel = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}
    if metadata:
        sel["metadata"] = metadata
    return sel


def seletor_categoria(campo, valor):
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": campo,
                                                 "Right": {"Literal": {"Value": f"'{valor}'"}}}}}]}


# ------------------------------------------------------------------ filtros de visual
def filtro_categoria(entidade, prop, valores, nome, excluir=False):
    cond = {"In": {
        "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": prop}}],
        "Values": [[{"Literal": {"Value": f"'{v}'"}}] for v in valores]}}
    if excluir:
        cond = {"Not": {"Expression": cond}}
    return {
        "name": nome,
        "field": col(entidade, prop),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "f", "Entity": entidade, "Type": 0}],
            "Where": [{"Condition": cond}],
        },
    }


def filtro_top(entidade, prop, medida, n, nome):
    return {
        "name": nome,
        "field": col(entidade, prop),
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {"Name": "subquery", "Expression": {"Subquery": {"Query": {
                    "Version": 2,
                    "From": [{"Name": "d", "Entity": entidade, "Type": 0},
                             {"Name": "m", "Entity": medidas, "Type": 0}],
                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop},
                                "Name": "field"}],
                    "OrderBy": [{"Direction": 2, "Expression": {
                        "Measure": {"Expression": {"SourceRef": {"Source": "m"}}, "Property": medida}}}],
                    "Top": n}}}, "Type": 2},
                {"Name": "d", "Entity": entidade, "Type": 0},
            ],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "d"}}, "Property": prop}}],
                "Table": {"SourceRef": {"Source": "subquery"}}}}}],
        },
    }


# ------------------------------------------------------------------ visual genérico
class Pagina:
    def __init__(self, nome):
        self.nome = nome
        self.visuais = []
        self.z = 1000

    def add(self, chave, tipo, x, y, w, h, query=None, objetos=None, container=None, filtros=None,
            ordenacao=None, extra=None):
        nome = gid(self.nome, chave)
        self.z += 100
        visual = {"visualType": tipo}
        if query:
            q = {"queryState": {k: {"projections": v} for k, v in query.items()}}
            if ordenacao:
                q["sortDefinition"] = ordenacao
            visual["query"] = q
        if objetos:
            visual["objects"] = objetos
        cont = {"title": [{"properties": {"show": b(False)}}]}
        if container:
            cont.update(container)
        visual["visualContainerObjects"] = cont
        visual["drillFilterOtherVisuals"] = True
        if extra:
            visual.update(extra)
        v = {
            "$schema": schema_visual,
            "name": nome,
            "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
            "visual": visual,
        }
        if filtros:
            v["filterConfig"] = {"filters": filtros}
        self.visuais.append(v)
        return nome


# ------------------------------------------------------------------ atalhos de visual
def obj(**props):
    return [{"properties": props}]


def cartao(pg, chave, x, y, w, h, medida, tamanho=28, cor_valor="#F8FAFC", fonte="Segoe UI Semibold"):
    return pg.add(chave, "card", x, y, w, h,
                  query={"Values": [proj(med(medida))]},
                  objetos={"labels": obj(color=cor(cor_valor), fontSize=d(tamanho), fontFamily=s(fonte)),
                           "categoryLabels": obj(show=b(False)),
                           "wordWrap": obj(show=b(True))},
                  container={"visualHeader": obj(show=b(False))})


def segmentacao(pg, chave, x, y, w, h, campo, titulo):
    return pg.add(chave, "slicer", x, y, w, h,
                  query={"Values": [proj(campo)]},
                  objetos={"data": obj(mode=s("Dropdown")),
                           "header": obj(text=s(titulo), show=b(True))},
                  container={"visualHeader": obj(show=b(False))})


def botao(pg, chave, x, y, w, h, tipo, destino=None):
    link = {"show": b(True), "type": s(tipo)}
    if destino:
        link["navigationSection"] = s(destino)
    return pg.add(chave, "actionButton", x, y, w, h,
                  objetos={
                      "icon": [{"properties": {"show": b(False)}, "selector": {"id": "default"}}],
                      "text": [{"properties": {"show": b(False)}, "selector": {"id": "default"}}],
                      "outline": [{"properties": {"show": b(False)}, "selector": {"id": "default"}}],
                      "fill": [
                          {"properties": {"show": b(False)}, "selector": {"id": "default"}},
                          {"properties": {"show": b(True), "fillColor": cor("#22D3EE"), "transparency": d(88)},
                           "selector": {"id": "hover"}},
                      ],
                  },
                  container={"visualLink": obj(**link), "visualHeader": obj(show=b(False))})
