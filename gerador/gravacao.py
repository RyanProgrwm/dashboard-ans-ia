"""grava o relatório pbir (tema, fundos, páginas e visuais) a partir das páginas montadas em gerar.py."""
import json
import shutil
from pathlib import Path

import fundos
import modelo
from visuais import gid, s, b, d, cor, col

tema = {
    "name": "ANS Noite",
    "dataColors": ["#22D3EE", "#A78BFA", "#F472B6", "#FBBF24", "#34D399", "#60A5FA", "#F87171", "#2DD4BF",
                   "#FB923C", "#C084FC", "#4ADE80", "#38BDF8"],
    "background": "#0A1020", "foreground": "#E2E8F0", "tableAccent": "#22D3EE",
    "good": "#34D399", "neutral": "#FBBF24", "bad": "#F87171",
    "maximum": "#22D3EE", "center": "#0E7490", "minimum": "#0F172A",
    "textClasses": {
        "callout": {"fontSize": 26, "fontFace": "Segoe UI Semibold", "color": "#F8FAFC"},
        "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#E2E8F0"},
        "header": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": "#E2E8F0"},
        "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": "#CBD5E1"},
    },
    "visualStyles": {
        "*": {"*": {
            "background": [{"show": False}],
            "border": [{"show": False}],
            "dropShadow": [{"show": False}],
            "title": [{"show": False}],
            "visualHeader": [{"show": True, "background": {"solid": {"color": "#141D33"}},
                              "foreground": {"solid": {"color": "#94A3B8"}}, "transparency": 0}],
            "visualTooltip": [{"background": {"solid": {"color": "#141D33"}},
                               "titleFontColor": {"solid": {"color": "#94A3B8"}},
                               "valueFontColor": {"solid": {"color": "#F8FAFC"}}}],
            "categoryAxis": [{"labelColor": {"solid": {"color": "#94A3B8"}}, "gridlineShow": False}],
            "valueAxis": [{"labelColor": {"solid": {"color": "#52627A"}},
                           "gridlineColor": {"solid": {"color": "#1B2540"}}}],
            "legend": [{"labelColor": {"solid": {"color": "#CBD5E1"}}}],
        }},
        "page": {"*": {
            "background": [{"transparency": 0}],
            "outspace": [{"color": {"solid": {"color": "#05080F"}}}],
        }},
        "slicer": {"*": {
            "header": [{"fontColor": {"solid": {"color": "#7C8BA3"}}, "textSize": 9, "show": True}],
            "items": [{"fontColor": {"solid": {"color": "#E2E8F0"}}, "background": {"solid": {"color": "#141D33"}},
                       "textSize": 10, "outlineColor": {"solid": {"color": "#22D3EE"}}}],
        }},
        "tableEx": {"*": {
            "grid": [{"gridVertical": False, "gridHorizontal": True,
                      "gridHorizontalColor": {"solid": {"color": "#1B2540"}},
                      "outlineColor": {"solid": {"color": "#1B2540"}}, "rowPadding": 7, "textSize": 10}],
            "columnHeaders": [{"fontColor": {"solid": {"color": "#94A3B8"}}, "backColor": {"solid": {"color": "#0B1222"}},
                               "fontFamily": "Segoe UI Semibold", "fontSize": 10, "wordWrap": True}],
            "values": [{"fontColorPrimary": {"solid": {"color": "#E2E8F0"}},
                        "backColorPrimary": {"solid": {"color": "#111A2E"}},
                        "fontColorSecondary": {"solid": {"color": "#E2E8F0"}},
                        "backColorSecondary": {"solid": {"color": "#0E1628"}}}],
        }},
        "pivotTable": {"*": {
            "grid": [{"gridVertical": True, "gridVerticalColor": {"solid": {"color": "#0A1020"}},
                      "gridHorizontal": True, "gridHorizontalColor": {"solid": {"color": "#0A1020"}}, "rowPadding": 9}],
            "columnHeaders": [{"fontColor": {"solid": {"color": "#94A3B8"}}, "backColor": {"solid": {"color": "#0B1222"}},
                               "fontFamily": "Segoe UI Semibold", "alignment": "Center"}],
            "rowHeaders": [{"fontColor": {"solid": {"color": "#CBD5E1"}}, "backColor": {"solid": {"color": "#0E1628"}}}],
            "values": [{"fontColorPrimary": {"solid": {"color": "#F8FAFC"}},
                        "backColorPrimary": {"solid": {"color": "#111A2E"}},
                        "backColorSecondary": {"solid": {"color": "#111A2E"}}}],
            "subTotals": [{"rowSubtotals": False, "columnSubtotals": False}],
        }},
    },
}

schema_pagina = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
versao_import = {"visual": "2.14.0", "report": "3.4.0", "page": "2.3.1"}


def gravar_json(caminho, dado):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dado, ensure_ascii=False, indent=2), encoding="utf-8")


def gravar(raiz: Path, nome, pasta_dados, paginas, menu, nomes_pag, tema_base: Path):
    for pasta in (raiz / f"{nome}.Report", raiz / f"{nome}.SemanticModel"):
        if pasta.exists():
            shutil.rmtree(pasta)
    modelo.gerar(raiz, nome, pasta_dados)

    rp = raiz / f"{nome}.Report"
    defs = rp / "definition"
    res = rp / "StaticResources" / "RegisteredResources"
    base = rp / "StaticResources" / "SharedResources" / "BaseThemes"
    base.mkdir(parents=True)
    res.mkdir(parents=True)
    shutil.copy(tema_base, base / tema_base.name)
    gravar_json(res / "ANS_Noite.json", tema)

    gravar_json(rp / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": nome},
        "config": {"version": "2.0", "logicalId": modelo.tag("rp", nome)}})
    gravar_json(rp / "definition.pbir",
                {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{nome}.SemanticModel"}}})
    gravar_json(defs / "version.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"})

    # fundos desenhados em html e convertidos para png
    temp = raiz / "gerador" / ".render"
    itens = [{"name": "ANS_Noite.json", "path": "ANS_Noite.json", "type": "CustomTheme"}]
    for chave, _, _, desenho in paginas:
        largura, altura = (400, 260) if chave == "dica" else (1920, 1080)
        arquivo = f"fundo_{chave}.png"
        dims = fundos.renderizar(fundos.html_pagina(desenho, menu, largura, altura), res / arquivo,
                                 largura, altura, temp)
        print(f"  fundo {chave}: {dims[0]}x{dims[1]}")
        itens.append({"name": arquivo, "path": arquivo, "type": "Image"})

    gravar_json(defs / "report.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json",
        "themeCollection": {
            "baseTheme": {"name": tema_base.stem, "reportVersionAtImport": versao_import, "type": "SharedResources"},
            "customTheme": {"name": "ANS_Noite.json", "reportVersionAtImport": versao_import,
                            "type": "RegisteredResources"},
        },
        "objects": {"outspacePane": [{"properties": {"expanded": b(False)}}]},
        "resourcePackages": [
            {"name": "SharedResources", "type": "SharedResources",
             "items": [{"name": tema_base.stem, "path": f"BaseThemes/{tema_base.name}", "type": "BaseTheme"}]},
            {"name": "RegisteredResources", "type": "RegisteredResources", "items": itens},
        ],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                     "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True},
    })

    for chave, rotulo, pg, _ in paginas:
        nome_pg = nomes_pag[chave]
        largura, altura = (400, 260) if chave == "dica" else (1920, 1080)
        url = {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1,
                                                "ItemName": f"fundo_{chave}.png"}}}
        pagina = {"$schema": schema_pagina, "name": nome_pg, "displayName": rotulo, "displayOption": "FitToPage",
                  "height": altura, "width": largura,
                  "objects": {
                      "background": [{"properties": {
                          "image": {"image": {"name": s(f"fundo_{chave}.png"), "url": url, "scaling": s("Fit")}},
                          "transparency": d(0)}}],
                      "outspace": [{"properties": {"color": cor("#05080F")}}]}}
        if chave == "dica":
            pagina.update({"visibility": "HiddenInViewMode", "type": "Tooltip"})
        if chave == "detalhe":
            filtro = gid("detalhe", "drill")
            campo = col("dOperadora", "Operadora")
            pagina["visibility"] = "HiddenInViewMode"
            pagina["filterConfig"] = {"filters": [{"name": filtro, "field": campo, "type": "Categorical",
                                                   "howCreated": "Drillthrough"}]}
            pagina["pageBinding"] = {"name": gid("detalhe", "binding"), "type": "Drillthrough",
                                     "parameters": [{"name": gid("detalhe", "param"), "boundFilter": filtro,
                                                     "fieldExpr": campo}],
                                     "referenceScope": "CrossReport"}
        gravar_json(defs / "pages" / nome_pg / "page.json", pagina)
        for v in pg.visuais:
            gravar_json(defs / "pages" / nome_pg / "visuals" / v["name"] / "visual.json", v)

    gravar_json(defs / "pages" / "pages.json", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
        "pageOrder": [nomes_pag[c] for c, _, _, _ in paginas], "activePageName": nomes_pag["visao"]})

    gravar_json(raiz / f"{nome}.pbip", {"version": "1.0", "artifacts": [{"report": {"path": f"{nome}.Report"}}],
                                         "settings": {"enableAutoRecovery": True}})
    shutil.rmtree(temp, ignore_errors=True)
    total = sum(len(pg.visuais) for _, _, pg, _ in paginas)
    print(f"projeto gerado: {nome}.pbip · {len(paginas)} páginas · {total} visuais")
