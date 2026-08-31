import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

print("=" * 75)
print("ANÁLISE DA ESTABILIDADE TEMPORAL DOS CLUSTERS")
print("=" * 75)

# =====================================================
# 1. CONFIGURAÇÕES
# =====================================================

ARQUIVO_ENTRADA = "dados_com_clusters.csv"

ARQUIVO_FAIXAS = (
    "Tabela24_Faixas_Persistencia_Temporal.csv"
)

ARQUIVO_RESUMO = (
    "Tabela26_Resumo_Persistencia_Temporal.csv"
)

ARQUIVO_GRAFICO = (
    "grafico_persistencia_temporal_clusters.png"
)

# =====================================================
# 2. LEITURA E VALIDAÇÃO
# =====================================================

df = pd.read_csv(
    ARQUIVO_ENTRADA,
    parse_dates=["mes"]
)

colunas_obrigatorias = [
    "cartorio_id",
    "mes",
    "cluster_par"
]

colunas_faltantes = [
    coluna
    for coluna in colunas_obrigatorias
    if coluna not in df.columns
]

if colunas_faltantes:
    raise ValueError(
        "Colunas ausentes: "
        + ", ".join(colunas_faltantes)
    )

if df.empty:
    raise ValueError(
        "A base está vazia."
    )

if df[colunas_obrigatorias].isna().any().any():
    raise ValueError(
        "Existem valores nulos nas colunas obrigatórias."
    )

df["cluster_par"] = (
    df["cluster_par"].astype(int)
)

# =====================================================
# 3. VALIDAÇÃO DA CHAVE SERVENTIA × MÊS
# =====================================================

duplicados = df.duplicated(
    subset=[
        "cartorio_id",
        "mes"
    ]
)

if duplicados.any():
    raise ValueError(
        "Existem registros duplicados para "
        "cartorio_id × mes."
    )

df = (
    df
    .sort_values(
        [
            "cartorio_id",
            "mes"
        ]
    )
    .reset_index(drop=True)
)

print(f"\nRegistros: {len(df):,}")

print(
    "Serventias distintas:",
    f"{df['cartorio_id'].nunique():,}"
)

print(
    "Período:",
    df["mes"].min().strftime("%m/%Y"),
    "a",
    df["mes"].max().strftime("%m/%Y")
)

# =====================================================
# 4. IDENTIFICAÇÃO DO MÊS ANTERIOR
# =====================================================

df["cluster_anterior"] = (
    df.groupby("cartorio_id")[
        "cluster_par"
    ].shift(1)
)

df["mes_anterior"] = (
    df.groupby("cartorio_id")[
        "mes"
    ].shift(1)
)

# Índice mensal para calcular a distância
df["indice_mes"] = (
    df["mes"].dt.year * 12
    + df["mes"].dt.month
)

df["indice_mes_anterior"] = (
    df["mes_anterior"].dt.year * 12
    + df["mes_anterior"].dt.month
)

df["distancia_meses"] = (
    df["indice_mes"]
    - df["indice_mes_anterior"]
)

# Somente meses realmente consecutivos são comparados
df["comparacao_valida"] = (
    df["cluster_anterior"].notna()
    & (df["distancia_meses"] == 1)
)

df["mudou_cluster"] = (
    df["comparacao_valida"]
    & (
        df["cluster_par"]
        != df["cluster_anterior"]
    )
)

df["permaneceu_cluster"] = (
    df["comparacao_valida"]
    & (
        df["cluster_par"]
        == df["cluster_anterior"]
    )
)

# =====================================================
# 5. ESTABILIDADE POR SERVENTIA
# =====================================================

resultados_serventias = []

for cartorio_id, grupo in df.groupby(
    "cartorio_id"
):

    comparacoes = int(
        grupo["comparacao_valida"].sum()
    )

    mudancas = int(
        grupo["mudou_cluster"].sum()
    )

    permanencias = int(
        grupo["permaneceu_cluster"].sum()
    )

    if comparacoes > 0:
        persistencia = (
            permanencias
            / comparacoes
            * 100
        )
    else:
        persistencia = np.nan

    contagem_clusters = (
        grupo["cluster_par"]
        .value_counts()
    )

    resultados_serventias.append(
        {
            "cartorio_id": cartorio_id,
            "Meses_Observados": len(grupo),
            "Comparacoes_Consecutivas": comparacoes,
            "Mudancas_de_Cluster": mudancas,
            "Permanencias": permanencias,
            "Persistencia_Temporal": persistencia,
            "Cluster_Predominante": int(
                contagem_clusters.index[0]
            ),
            "Clusters_Visitados": int(
                grupo["cluster_par"].nunique()
            )
        }
    )

estabilidade = pd.DataFrame(
    resultados_serventias
)

# Serão usadas no cálculo apenas serventias com
# pelo menos uma comparação entre meses consecutivos
estabilidade_valida = estabilidade.dropna(
    subset=["Persistencia_Temporal"]
).copy()

# =====================================================
# 6. FAIXAS DE PERSISTÊNCIA
# =====================================================

def classificar_persistencia(valor):

    if valor >= 99:
        return "Muito alta (≥ 99%)"

    if valor >= 95:
        return "Alta (95% a 98,99%)"

    if valor >= 80:
        return "Moderada (80% a 94,99%)"

    return "Baixa (< 80%)"


estabilidade_valida["Faixa"] = (
    estabilidade_valida[
        "Persistencia_Temporal"
    ]
    .apply(classificar_persistencia)
)

ordem_faixas = [
    "Muito alta (≥ 99%)",
    "Alta (95% a 98,99%)",
    "Moderada (80% a 94,99%)",
    "Baixa (< 80%)"
]

tabela24 = (
    estabilidade_valida["Faixa"]
    .value_counts()
    .reindex(
        ordem_faixas,
        fill_value=0
    )
    .rename_axis(
        "Faixa de Persistência Temporal"
    )
    .reset_index(
        name="Serventias"
    )
)

tabela24["Percentual (%)"] = (
    tabela24["Serventias"]
    / len(estabilidade_valida)
    * 100
).round(2)

linha_total = pd.DataFrame(
    {
        "Faixa de Persistência Temporal": [
            "Total"
        ],
        "Serventias": [
            int(tabela24["Serventias"].sum())
        ],
        "Percentual (%)": [
            100.00
        ]
    }
)

tabela24 = pd.concat(
    [
        tabela24,
        linha_total
    ],
    ignore_index=True
)

tabela24.to_csv(
    ARQUIVO_FAIXAS,
    index=False
)

# =====================================================
# 7. RESUMO DA PERSISTÊNCIA
# =====================================================

sem_mudanca = int(
    (
        estabilidade_valida[
            "Mudancas_de_Cluster"
        ] == 0
    ).sum()
)

uma_mudanca = int(
    (
        estabilidade_valida[
            "Mudancas_de_Cluster"
        ] == 1
    ).sum()
)

duas_mudancas = int(
    (
        estabilidade_valida[
            "Mudancas_de_Cluster"
        ] == 2
    ).sum()
)

tres_ou_mais = int(
    (
        estabilidade_valida[
            "Mudancas_de_Cluster"
        ] >= 3
    ).sum()
)

com_alguma_mudanca = int(
    (
        estabilidade_valida[
            "Mudancas_de_Cluster"
        ] > 0
    ).sum()
)

sem_comparacao = int(
    estabilidade[
        "Persistencia_Temporal"
    ].isna().sum()
)

tabela26 = pd.DataFrame(
    {
        "Indicador": [
            "Total de serventias",
            "Serventias com comparações consecutivas",
            "Serventias sem comparação consecutiva",
            "Serventias sem mudança",
            "Serventias com uma mudança",
            "Serventias com duas mudanças",
            "Serventias com três ou mais mudanças",
            "Serventias com alguma mudança",
            "Persistência temporal média (%)",
            "Persistência temporal mediana (%)",
            "Menor persistência temporal (%)",
            "Maior persistência temporal (%)",
            "Média de mudanças por serventia",
            "Mediana de mudanças por serventia",
            "Maior número de mudanças"
        ],
        "Valor": [
            len(estabilidade),
            len(estabilidade_valida),
            sem_comparacao,
            sem_mudanca,
            uma_mudanca,
            duas_mudancas,
            tres_ou_mais,
            com_alguma_mudanca,
            round(
                estabilidade_valida[
                    "Persistencia_Temporal"
                ].mean(),
                2
            ),
            round(
                estabilidade_valida[
                    "Persistencia_Temporal"
                ].median(),
                2
            ),
            round(
                estabilidade_valida[
                    "Persistencia_Temporal"
                ].min(),
                2
            ),
            round(
                estabilidade_valida[
                    "Persistencia_Temporal"
                ].max(),
                2
            ),
            round(
                estabilidade_valida[
                    "Mudancas_de_Cluster"
                ].mean(),
                2
            ),
            round(
                estabilidade_valida[
                    "Mudancas_de_Cluster"
                ].median(),
                2
            ),
            int(
                estabilidade_valida[
                    "Mudancas_de_Cluster"
                ].max()
            )
        ]
    }
)

tabela26.to_csv(
    ARQUIVO_RESUMO,
    index=False
)

# =====================================================
# 8. TRANSIÇÕES — SOMENTE NO TERMINAL
# =====================================================

transicoes = df[
    df["mudou_cluster"]
].copy()

if not transicoes.empty:

    transicoes["cluster_anterior"] = (
        transicoes["cluster_anterior"]
        .astype(int)
    )

    tabela_transicoes = (
        transicoes
        .groupby(
            [
                "cluster_anterior",
                "cluster_par"
            ]
        )
        .size()
        .reset_index(
            name="Quantidade"
        )
        .rename(
            columns={
                "cluster_anterior": "Origem",
                "cluster_par": "Destino"
            }
        )
        .sort_values(
            "Quantidade",
            ascending=False
        )
    )

    print("\nTransições entre clusters:")
    print(
        tabela_transicoes.to_string(
            index=False
        )
    )

# =====================================================
# 9. SERVENTIAS MAIS INSTÁVEIS — TERMINAL
# =====================================================

mais_instaveis = (
    estabilidade_valida
    .sort_values(
        [
            "Persistencia_Temporal",
            "Mudancas_de_Cluster"
        ],
        ascending=[
            True,
            False
        ]
    )
    .head(20)
)

print("\nServentias com menor persistência:")
print(
    mais_instaveis.to_string(
        index=False
    )
)

# =====================================================
# 10. GRÁFICO
# =====================================================

plt.figure(
    figsize=(10, 6)
)

plt.hist(
    estabilidade_valida[
        "Persistencia_Temporal"
    ],
    bins=np.arange(
        0,
        105,
        5
    ),
    edgecolor="black",
    color="steelblue"
)

plt.xlim(
    0,
    100
)

plt.title(
    "Distribuição da Persistência Temporal "
    "das Serventias entre Clusters"
)

plt.xlabel(
    "Persistência em meses consecutivos (%)"
)

plt.ylabel(
    "Quantidade de serventias"
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4
)

plt.tight_layout()

plt.savefig(
    ARQUIVO_GRAFICO,
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# =====================================================
# 11. RESULTADOS
# =====================================================

print("\nTabela 24 — Faixas de Persistência")
print(
    tabela24.to_string(
        index=False
    )
)

print("\nTabela 26 — Resumo da Persistência")
print(
    tabela26.to_string(
        index=False
    )
)

print("\nArquivos gerados:")
print(f"✔ {ARQUIVO_FAIXAS}")
print(f"✔ {ARQUIVO_RESUMO}")
print(f"✔ {ARQUIVO_GRAFICO}")

print("\nExperimento concluído com sucesso.")