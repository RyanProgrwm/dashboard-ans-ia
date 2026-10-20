# Reclamações contra planos de saúde · ANS 2025 (versão com IA)

Segunda versão do meu [dashboard de reclamações da ANS](https://github.com/RyanProgrwm/dashboard-reclamacoes-ans), construída **com apoio de IA (Claude Code)**. A primeira versão eu fiz sozinho, aprendendo Power BI do zero. Nesta, usei IA para levar o mesmo projeto a outro nível de análise, automação e acabamento. Eu defini as perguntas e as métricas, revisei o código e validei os números e o painel no Power BI Desktop.

## O que mudou em relação à primeira versão

| | Versão 1 (feita por mim) | Versão 2 (com IA) |
|---|---|---|
| Métrica principal | Volume de reclamações | **Taxa por 10 mil beneficiários/mês**, que compara operadoras de tamanhos diferentes |
| Fontes | Reclamações e cadastro de operadoras | + beneficiários por operadora e **nota de qualidade IDSS** da ANS |
| Tratamento | Power Query manual | **ETL em Python**, reproduzível, com log de qualidade |
| Projeto | Arquivo `.pbix` | **PBIP** (modelo em TMDL e relatório em PBIR), versionável no Git e gerado por script |
| Páginas | 2 + dica | 5 páginas de análise + detalhe da operadora + dica |
| Visual | Tema escuro padrão | Tema próprio, fundos desenhados, menu lateral com navegação |

## Por que a taxa importa

Uma operadora com milhões de clientes sempre vai ter mais reclamações em número absoluto. Para comparar de forma justa, a reclamação precisa ser dividida pelo tamanho da carteira. É a mesma lógica do IGR, o índice oficial de reclamações da ANS:

```
taxa por 10 mil = reclamações / (beneficiários × meses) × 10.000
```

Com essa régua, o mercado fica em **3,1 reclamações por 10 mil beneficiários por mês** em 2025.

## Principais achados

- A **Unimed FERJ**, que assumiu a carteira da Unimed-Rio, tem **55,7 reclamações por 10 mil beneficiários por mês**, cerca de **18 vezes a média do mercado**. É, de longe, a pior entre as operadoras de grande porte.
- **Nota de qualidade alta não garante pouca reclamação:** o Bradesco Saúde tem IDSS de 0,81, na faixa mais alta, e ainda assim uma taxa de 7,7, mais que o dobro do mercado. A dispersão IDSS × taxa mostra esses casos.
- Operadoras **odontológicas** quase não aparecem nas reclamações. Várias têm mais de 100 mil beneficiários e menos de 5 reclamações no ano.
- O assunto mais reclamado é **regras para acesso aos atendimentos** (79,5 mil reclamações), à frente de prazos máximos de atendimento e reembolso.

## Páginas

1. **Visão geral:** 6 KPIs, evolução mensal com variação, leitura automática ("narrativa" em DAX), resposta do beneficiário, temas e top 10 operadoras.
2. **Operadoras:** dispersão IDSS × taxa (bolha = beneficiários), ranking das operadoras de grande porte com formatação condicional, e taxa por modalidade e por porte.
3. **Assuntos:** mapa de calor assunto × mês, % de resolução por assunto e natureza da demanda.
4. **Perfil:** faixas etárias da ANS (colunas de volume + linha de % de resolução), sexo, tipo de plano, canal e dia da semana.
5. **Geografia:** reclamações por UF e treemap região › estado.
6. **Detalhe da operadora** (drill-through): título dinâmico, taxa da operadora × mercado mês a mês, posição no ranking e assuntos.
7. **Dica personalizada:** mini-painel ao passar o mouse numa operadora.

## Arquitetura

```
dados abertos ANS (CSV)
        │
        ▼
etl/preparar_dados.py ──► dados/modelo/  (fato + 4 dimensões em formato estrela + qualidade.json)
        │
        ▼
gerador/gerar.py ──► painel-ans.SemanticModel/ (TMDL: tabelas, relacionamentos, 24 medidas DAX)
                 └─► painel-ans.Report/        (PBIR: páginas, visuais, tema, fundos)
```

- **Modelo estrela:** `fReclamacoes` (325 mil linhas) com `dOperadora`, `dAssunto`, `dFaixaEtaria`, `dUF` e `dCalendario` (gerada em DAX).
- **Medidas de destaque:**
  - `Taxa por 10 mil` e `Taxa Mercado` (com `removefilters` sobre a dimensão de operadora);
  - `Índice vs Mercado`;
  - `Ranking Taxa` (posição entre as de grande porte, calculada com `calculatetable` + `addcolumns`);
  - `Narrativa` (texto montado a partir dos filtros ativos).
- **Fundos:** desenhados em HTML/CSS e convertidos para PNG com o Chrome headless. Os visuais ficam transparentes por cima.

## Qualidade de dados (log do ETL)

| Problema | Ocorrências | Tratamento |
|---|---|---|
| Assuntos com espaço sobrando ou caractere corrompido (`¿`) | 40 valores viram 19 | Limpeza de texto antes de criar a dimensão |
| Operadoras canceladas depois da reclamação | 126 operadoras | Dimensão junta ativas e canceladas |
| Nomes fantasia repetidos entre operadoras | 316 nomes | Nome ganha o registro ANS, para o drill-through funcionar |
| Reclamações sem operadora | 49 | Membro "(não informada)" |
| Idade inválida (acima de 110 anos, até 2022) | 9 | Tratada como não informada |
| Beneficiários em série mensal | 920 operadoras | Média dos 12 meses de 2025 como denominador |

## Como rodar

1. Baixe os dados abertos da ANS para `dados/brutos/`:
   - [reclamações NIP 2025](https://dadosabertos.ans.gov.br/FTP/PDA/demandas_dos_consumidores_nip/)
   - [operadoras ativas](https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/) e [canceladas](https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_canceladas/)
   - [beneficiários por operadora](https://dadosabertos.ans.gov.br/FTP/PDA/beneficiarios_vinculos_tipo_contratacao_vda/) (salvar como `beneficiarios_operadora.csv`)
   - [histórico do IDSS](https://dadosabertos.ans.gov.br/FTP/PDA/historico_idss-020/) (salvar como `idss_2016_2025.csv`)
2. `python etl/preparar_dados.py`
3. Abra `painel-ans.pbip` no Power BI Desktop. Em *Transformar dados* → *Editar parâmetros*, aponte `PastaDados` para a sua pasta `dados/modelo/` e clique em *Atualizar*.

Para regerar o projeto depois de mudar o layout ou as medidas: `python gerador/gerar.py` (precisa do Chrome instalado para desenhar os fundos).

## Como a IA entrou no processo

- **Eu:** escolhi o tema e as perguntas, defini a taxa por beneficiário e o cruzamento com o IDSS como os próximos passos depois da versão 1, conferi os números com a fonte e validei cada página no Power BI Desktop.
- **A IA (Claude Code):** escreveu o ETL e o gerador do projeto, encontrou e tratou os problemas de dados listados acima e desenhou o layout.
- **O que aprendi com isso:** projeto Power BI como código (TMDL/PBIR), medidas DAX mais avançadas (ranking, comparação com o mercado, narrativa dinâmica) e como uma métrica normalizada muda completamente a leitura de um ranking.

Fonte: Portal de Dados Abertos da ANS · dados públicos extraídos em outubro de 2026.

---

Ryan Saldanha · [LinkedIn](https://www.linkedin.com/in/ryansaldanha1302) · [GitHub](https://github.com/RyanProgrwm)
