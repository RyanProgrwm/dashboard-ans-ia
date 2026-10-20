"""
prepara os dados abertos da ANS no formato estrela usado pelo painel.

entrada (dados/brutos):
  pda-013-demandas_dos_consumidores_nip-2025.csv  reclamações (NIP) de 2025
  Relatorio_cadop.csv                             operadoras ativas
  Relatorio_cadop_canceladas.csv                  operadoras canceladas
  beneficiarios_operadora.csv                     beneficiários por operadora e carteira
  idss_2016_2025.csv                              histórico do IDSS

saída (dados/modelo):
  fato_reclamacoes.csv, dim_operadora.csv, dim_assunto.csv,
  dim_faixa_etaria.csv, dim_uf.csv e qualidade.json (log do que foi tratado)

uso: python etl/preparar_dados.py
"""
import csv
import json
import collections
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
brutos = raiz / "dados" / "brutos"
modelo = raiz / "dados" / "modelo"
modelo.mkdir(parents=True, exist_ok=True)

ano_idss = "IDSS_2025_2024"
sem_operadora = "0"

# faixas etárias regulatórias da ANS (RN 63/2003)
faixas = [(0, 18, "0 a 18"), (19, 23, "19 a 23"), (24, 28, "24 a 28"), (29, 33, "29 a 33"),
          (34, 38, "34 a 38"), (39, 43, "39 a 43"), (44, 48, "44 a 48"), (49, 53, "49 a 53"),
          (54, 58, "54 a 58"), (59, 110, "59 ou mais")]

ufs = {
    "AC": ("Acre", "Norte"), "AL": ("Alagoas", "Nordeste"), "AM": ("Amazonas", "Norte"),
    "AP": ("Amapá", "Norte"), "BA": ("Bahia", "Nordeste"), "CE": ("Ceará", "Nordeste"),
    "DF": ("Distrito Federal", "Centro-Oeste"), "ES": ("Espírito Santo", "Sudeste"),
    "GO": ("Goiás", "Centro-Oeste"), "MA": ("Maranhão", "Nordeste"), "MG": ("Minas Gerais", "Sudeste"),
    "MS": ("Mato Grosso do Sul", "Centro-Oeste"), "MT": ("Mato Grosso", "Centro-Oeste"),
    "PA": ("Pará", "Norte"), "PB": ("Paraíba", "Nordeste"), "PE": ("Pernambuco", "Nordeste"),
    "PI": ("Piauí", "Nordeste"), "PR": ("Paraná", "Sul"), "RJ": ("Rio de Janeiro", "Sudeste"),
    "RN": ("Rio Grande do Norte", "Nordeste"), "RO": ("Rondônia", "Norte"), "RR": ("Roraima", "Norte"),
    "RS": ("Rio Grande do Sul", "Sul"), "SC": ("Santa Catarina", "Sul"), "SE": ("Sergipe", "Nordeste"),
    "SP": ("São Paulo", "Sudeste"), "TO": ("Tocantins", "Norte"),
}

respostas = {
    "Sim, resolvido": ("Resolvido", 1, 1),
    "Cobertura dentro do prazo": ("Cobertura no prazo", 1, 1),
    "Não resolvido": ("Não resolvido", 1, 0),
    "Cobertura fora do prazo": ("Cobertura fora do prazo", 1, 0),
    "": ("Sem resposta", 0, 0),
}

log = collections.OrderedDict()


def ler(nome):
    with open(brutos / nome, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def gravar(nome, colunas, linhas):
    with open(modelo / nome, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        w.writerow(colunas)
        w.writerows(linhas)
    print(f"  {nome}: {len(linhas):,} linhas".replace(",", "."))


def limpa(texto):
    # espaços nas pontas e o caractere corrompido que aparece na origem (¿ no lugar de á)
    return (texto or "").strip().replace("¿", "á")


def faixa_de(idade):
    if idade is None:
        return 11
    for i, (ini, fim, _) in enumerate(faixas, start=1):
        if ini <= idade <= fim:
            return i
    return 11


# ---------------------------------------------------------------- reclamações
print("lendo reclamações...")
nip = ler("pda-013-demandas_dos_consumidores_nip-2025.csv")
log["reclamacoes_lidas"] = len(nip)

assuntos = {}
contagem_bruta_assuntos = len({r["ASSUNTO"] for r in nip})
idade_invalida = sem_idade = sem_uf = sem_op = 0
fato = []
for r in nip:
    assunto = limpa(r["ASSUNTO"])
    if assunto not in assuntos:
        assuntos[assunto] = len(assuntos) + 1

    idade_txt = r["IDADE_BENEFICIARIO"].strip()
    idade = int(idade_txt) if idade_txt else None
    if idade is None:
        sem_idade += 1
    elif idade > 110:
        idade_invalida += 1
        idade = None

    uf = r["UF_BENEFICIARIO"].strip()
    if uf not in ufs:
        sem_uf += 1
        uf = "ND"

    op = r["REGISTRO_OPERADORA"].strip()
    if not op:
        sem_op += 1
        op = sem_operadora

    resposta, respondida, resolvida = respostas.get(r["RESPOSTA_BENEFICIARIO"].strip(), ("Sem resposta", 0, 0))
    sexo = {"F": "Feminino", "M": "Masculino"}.get(r["SEXO_BENEFICIARIO"].strip(), "Não informado")
    tipo_plano = r["TIPO_PLANO_CONTRATADO"].strip() or "Não informado"
    natureza = r["NATUREZA_NIP"].strip() or "Não informada"
    forma = r["FORMA_CONTATO_ANS"].strip()
    forma = forma if forma in ("Site", "Telefone") else "Outros canais"

    fato.append([r["NR_DEMANDA"].strip(), r["DT_ABERTURA_DEMANDA"].strip(), op, assuntos[assunto], uf,
                 faixa_de(idade), "" if idade is None else idade, sexo, tipo_plano, forma, natureza,
                 resposta, respondida, resolvida])

log["assuntos_brutos_distintos"] = contagem_bruta_assuntos
log["assuntos_apos_limpeza"] = len(assuntos)
log["idade_vazia"] = sem_idade
log["idade_invalida_maior_110"] = idade_invalida
log["uf_nao_informada"] = sem_uf
log["sem_operadora"] = sem_op

# ---------------------------------------------------------------- operadoras
print("lendo operadoras, beneficiários e IDSS...")
ativas = ler("Relatorio_cadop.csv")
canceladas = ler("Relatorio_cadop_canceladas.csv")

# o arquivo é uma série mensal (coluna MES); o denominador certo para 2025 é a média dos 12 meses do ano
benef_mes = collections.defaultdict(collections.Counter)
for r in ler("beneficiarios_operadora.csv"):
    if r["MES"].startswith("2025"):
        benef_mes[r["CD_OPERADORA"].strip()][r["MES"]] += int(r["NR_BENEF"] or 0)
beneficiarios = {op: round(sum(m.values()) / len(m)) for op, m in benef_mes.items()}
log["operadoras_com_beneficiarios_2025"] = len(beneficiarios)

idss = {}
for r in ler("idss_2016_2025.csv"):
    v = (r.get(ano_idss) or "").strip().replace(",", ".")
    try:
        idss[r["REGISTRO_OPERADORA"].strip()] = float(v)
    except ValueError:
        pass  # vazio ou "ND": operadora sem nota no ano


def porte(b):
    # classificação de porte da ANS por número de beneficiários
    if b == 0:
        return "Sem beneficiários"
    if b < 20000:
        return "Pequeno"
    if b <= 100000:
        return "Médio"
    return "Grande"


def faixa_idss(v):
    if v is None:
        return "Sem nota"
    for limite, nome in ((0.2, "0,0 a 0,19"), (0.4, "0,2 a 0,39"), (0.6, "0,4 a 0,59"), (0.8, "0,6 a 0,79")):
        if v < limite:
            return nome
    return "0,8 a 1,0"


operadoras = {}
for situacao, linhas in (("Ativa", ativas), ("Cancelada", canceladas)):
    for r in linhas:
        reg = r["REGISTRO_OPERADORA"].strip()
        if reg in operadoras:
            continue
        nome = (r["NOME_FANTASIA"] or "").strip() or r["RAZAO_SOCIAL"].strip()
        b = beneficiarios.get(reg, 0)
        nota = idss.get(reg)
        operadoras[reg] = [reg, nome, r["RAZAO_SOCIAL"].strip(), r["MODALIDADE"].strip(), r["UF"].strip(),
                           situacao, b, porte(b), "" if nota is None else f"{nota:.4f}", faixa_idss(nota)]

# o nome é usado no drill-through, então precisa ser único: nomes repetidos ganham o registro ANS
repetidos = collections.Counter(o[1] for o in operadoras.values())
for o in operadoras.values():
    if repetidos[o[1]] > 1:
        o[1] = f"{o[1]} ({o[0]})"
log["nomes_de_operadora_desambiguados"] = sum(n for n in repetidos.values() if n > 1)

operadoras[sem_operadora] = [sem_operadora, "(não informada)", "(não informada)", "Não informada", "ND",
                             "Não informada", 0, "Sem beneficiários", "", "Sem nota"]

orfas = {linha[2] for linha in fato if linha[2] not in operadoras}
log["operadoras_orfas_na_fato"] = len(orfas)
log["operadoras_canceladas_com_reclamacao"] = len(
    {linha[2] for linha in fato if operadoras.get(linha[2], [None] * 6)[5] == "Cancelada"})

# ---------------------------------------------------------------- gravação
print("gravando modelo...")
gravar("fato_reclamacoes.csv",
       ["id_demanda", "data_abertura", "id_operadora", "id_assunto", "uf", "id_faixa_etaria", "Idade",
        "Sexo", "Tipo de Plano", "Canal", "Natureza", "Resposta", "fl_respondida", "fl_resolvida"], fato)

gravar("dim_operadora.csv",
       ["id_operadora", "Operadora", "Razão Social", "Modalidade", "UF Sede", "Situação", "Beneficiários",
        "Porte", "IDSS", "Faixa IDSS"], list(operadoras.values()))

linhas_assunto = []
for assunto, i in assuntos.items():
    partes = assunto.split(" >> ")
    linhas_assunto.append([i, partes[2], partes[1], partes[0], assunto])
gravar("dim_assunto.csv", ["id_assunto", "Assunto", "Tema", "Grupo", "Assunto Completo"], linhas_assunto)

gravar("dim_faixa_etaria.csv", ["id_faixa_etaria", "Faixa Etária"],
       [[i, nome] for i, (_, _, nome) in enumerate(faixas, start=1)] + [[11, "Não informada"]])

gravar("dim_uf.csv", ["uf", "Estado", "Região"],
       [[uf, nome, regiao] for uf, (nome, regiao) in sorted(ufs.items())] + [["ND", "Não informada", "Não informada"]])

with open(modelo / "qualidade.json", "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
print(json.dumps(log, ensure_ascii=False, indent=2))
