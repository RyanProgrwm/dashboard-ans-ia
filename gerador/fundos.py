"""desenha os fundos das páginas em html e converte para png com o chrome headless."""
import struct
import subprocess
from pathlib import Path

chrome = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

paleta = {
    "cyan": "#22D3EE", "violeta": "#A78BFA", "rosa": "#F472B6", "ambar": "#FBBF24",
    "verde": "#34D399", "azul": "#60A5FA", "vermelho": "#F87171",
}

icones = {
    "home": '<path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z"/>',
    "predio": '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 7h1M14 7h1M9 11h1M14 11h1M9 15h1M14 15h1"/>',
    "camadas": '<path d="M12 3 2 8l10 5 10-5-10-5z"/><path d="M2 13l10 5 10-5"/>',
    "pessoa": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 4-6 8-6s8 2 8 6"/>',
    "mapa": '<path d="M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    "mensagem": '<path d="M21 12a8 8 0 0 1-11.5 7.2L4 21l1.8-5.2A8 8 0 1 1 21 12z"/>',
    "pulso": '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "escudo": '<path d="M12 3 4 6v6c0 5 3.5 8 8 9 4.5-1 8-4 8-9V6l-8-3z"/>',
    "pessoas": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c0-3.5 3-5.5 6.5-5.5s6.5 2 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.8c2 .7 3.5 2.4 3.5 5.2"/>',
    "coracao": '<path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/>',
    "tendencia": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "grade": '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
    "calendario": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    "pizza": '<path d="M12 3a9 9 0 1 0 9 9h-9z"/><path d="M15 3.5A9 9 0 0 1 20.5 9H15z"/>',
    "barras": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "dispersao": '<circle cx="7" cy="15" r="2"/><circle cx="12" cy="8" r="2"/><circle cx="17" cy="13" r="2"/><path d="M3 21h18M3 3v18"/>',
    "voltar": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "lampada": '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    "trofeu": '<path d="M8 21h8M12 17v4M7 4h10v5a5 5 0 0 1-10 0V4z"/><path d="M17 5h3v2a3 3 0 0 1-3 3M7 5H4v2a3 3 0 0 0 3 3"/>',
    "relogio": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
}


def svg(nome, cor, tamanho=18, traco=2):
    return (f'<svg width="{tamanho}" height="{tamanho}" viewBox="0 0 24 24" fill="none" stroke="{cor}" '
            f'stroke-width="{traco}" stroke-linecap="round" stroke-linejoin="round">{icones[nome]}</svg>')


css = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { width: %(w)dpx; height: %(h)dpx; overflow: hidden; font-family: 'Segoe UI', sans-serif; color: #E2E8F0;
  background:
    radial-gradient(1100px 520px at 18%% -12%%, rgba(34,211,238,.11), transparent 70%%),
    radial-gradient(900px 480px at 100%% -5%%, rgba(167,139,250,.12), transparent 70%%),
    radial-gradient(800px 600px at 60%% 120%%, rgba(244,114,182,.06), transparent 70%%),
    #0A1020; position: relative; }
.abs { position: absolute; }
.lateral { left: 0; top: 0; width: 232px; height: 100%%; background: rgba(6,10,22,.82);
  border-right: 1px solid #141D33; }
.logo { left: 24px; top: 28px; display: flex; align-items: center; gap: 12px; }
.logo .marca { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center;
  background: linear-gradient(135deg, #22D3EE, #A78BFA); color: #06101F; font-weight: 800; font-size: 14px;
  letter-spacing: .5px; box-shadow: 0 8px 24px rgba(34,211,238,.25); }
.logo .t1 { font-size: 15px; font-weight: 700; color: #F8FAFC; line-height: 1.15; }
.logo .t2 { font-size: 11.5px; color: #64748B; margin-top: 2px; }
.secao { left: 28px; font-size: 10.5px; letter-spacing: 1.6px; color: #475569; font-weight: 600; }
.item { left: 16px; width: 200px; height: 44px; border-radius: 10px; display: flex; align-items: center;
  gap: 12px; padding-left: 16px; font-size: 14px; color: #94A3B8; }
.item.ativo { background: linear-gradient(90deg, rgba(34,211,238,.16), rgba(34,211,238,.03));
  color: #F8FAFC; font-weight: 600; }
.item.ativo::before { content: ''; position: absolute; left: -16px; top: 10px; width: 4px; height: 24px;
  border-radius: 0 4px 4px 0; background: #22D3EE; box-shadow: 0 0 12px #22D3EE; }
.rodape { left: 28px; bottom: 28px; font-size: 11px; color: #475569; line-height: 1.6; }
.titulo { font-size: 30px; font-weight: 700; color: #F8FAFC; letter-spacing: -.3px; }
.subtitulo { font-size: 14px; color: #7C8BA3; }
.linha { height: 1px; background: linear-gradient(90deg, rgba(34,211,238,.55), rgba(167,139,250,.35) 40%%, transparent); }
.painel { border-radius: 16px; border: 1px solid #1B2540;
  background: linear-gradient(180deg, rgba(20,29,51,.92), rgba(13,20,38,.92));
  box-shadow: 0 12px 32px rgba(0,0,0,.35), inset 0 1px 0 rgba(255,255,255,.03); }
.painel .cab { position: absolute; left: 20px; top: 16px; display: flex; align-items: center; gap: 10px; }
.painel .ico { width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center; }
.painel .nome { font-size: 15px; font-weight: 600; color: #E2E8F0; }
.painel .desc { font-size: 11.5px; color: #64748B; margin-top: 1px; }
.kpi { border-radius: 16px; border: 1px solid #1B2540; overflow: hidden;
  background: linear-gradient(180deg, rgba(20,29,51,.95), rgba(13,20,38,.95)); }
.kpi .barra { position: absolute; left: 0; top: 0; right: 0; height: 3px; }
.kpi .brilho { position: absolute; left: 50%%; top: -60px; width: 220px; height: 120px; transform: translateX(-50%%);
  border-radius: 50%%; filter: blur(30px); opacity: .22; }
.kpi .rot { position: absolute; left: 0; right: 0; top: 18px; display: flex; justify-content: center;
  align-items: center; gap: 8px; font-size: 11px; letter-spacing: 1.3px; color: #94A3B8; font-weight: 600; }
.kpi .nota { position: absolute; left: 0; right: 0; bottom: 12px; text-align: center; font-size: 11px; color: #52627A; }
.faixa { border-radius: 14px; border: 1px solid rgba(34,211,238,.25);
  background: linear-gradient(90deg, rgba(34,211,238,.10), rgba(167,139,250,.06)); }
"""


def lateral(paginas_menu, ativa):
    html = ['<div class="abs lateral"></div>',
            '<div class="abs logo"><div class="marca">ANS</div><div><div class="t1">Saúde Suplementar</div>'
            '<div class="t2">Reclamações · 2025</div></div></div>',
            '<div class="abs secao" style="top:122px">PAINÉIS</div>']
    for i, (chave, rotulo, icone) in enumerate(paginas_menu):
        y = 144 + i * 52
        classe = "item ativo" if chave == ativa else "item"
        c = "#22D3EE" if chave == ativa else "#64748B"
        html.append(f'<div class="abs {classe}" style="top:{y}px">{svg(icone, c)}{rotulo}</div>')
    html.append('<div class="abs rodape">Fonte: ANS · Dados Abertos<br>NIP 2025 · beneficiários e IDSS</div>')
    return "\n".join(html)


def painel(p):
    x, y, w, h = p["box"]
    c = paleta[p.get("cor", "cyan")]
    cab = ""
    if p.get("nome"):
        cab = (f'<div class="cab"><div class="ico" style="background:{c}1F">{svg(p["icone"], c, 17)}</div>'
               f'<div><div class="nome">{p["nome"]}</div><div class="desc">{p.get("desc", "")}</div></div></div>')
    return f'<div class="abs painel" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">{cab}</div>'


def kpi(k):
    x, y, w, h = k["box"]
    c = paleta[k["cor"]]
    nota = f'<div class="nota">{k["nota"]}</div>' if k.get("nota") else ""
    return (f'<div class="abs kpi" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px">'
            f'<div class="barra" style="background:linear-gradient(90deg,transparent,{c},transparent)"></div>'
            f'<div class="brilho" style="background:{c}"></div>'
            f'<div class="rot">{svg(k["icone"], c, 15)}{k["rotulo"].upper()}</div>{nota}</div>')


def html_pagina(pg, menu, largura=1920, altura=1080):
    partes = [f"<!doctype html><html><head><meta charset='utf-8'><style>{css % {'w': largura, 'h': altura}}</style>"
              "</head><body>"]
    if pg.get("menu", True):
        partes.append(lateral(menu, pg["chave"]))
    if pg.get("titulo"):
        partes.append(f'<div class="abs titulo" style="left:{pg.get("titulo_x", 256)}px;top:24px">{pg["titulo"]}</div>')
        partes.append(f'<div class="abs subtitulo" style="left:{pg.get("titulo_x", 256)}px;top:68px">{pg["subtitulo"]}</div>')
        partes.append('<div class="abs linha" style="left:256px;top:104px;width:1640px"></div>')
    for f in pg.get("faixas", []):
        x, y, w, h = f
        partes.append(f'<div class="abs faixa" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px"></div>')
    for p in pg.get("paineis", []):
        partes.append(painel(p))
    for k in pg.get("kpis", []):
        partes.append(kpi(k))
    partes.extend(pg.get("html_extra", []))
    partes.append("</body></html>")
    return "\n".join(partes)


def tamanho_png(caminho):
    with open(caminho, "rb") as f:
        cab = f.read(24)
    return struct.unpack(">II", cab[16:24])


def renderizar(html, destino: Path, largura, altura, temp: Path):
    temp.mkdir(parents=True, exist_ok=True)
    arq = temp / (destino.stem + ".html")
    arq.write_text(html, encoding="utf-8")
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                    f"--window-size={largura},{altura}", f"--screenshot={destino}", arq.as_uri()],
                   check=True, capture_output=True, timeout=120)
    return tamanho_png(destino)
