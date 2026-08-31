import numpy as np
import pandas as pd
from scipy.stats import spearmanr


print("=" * 75)
print("COMPARAÇÃO ENTRE Z-SCORE TRADICIONAL E ROBUST Z-SCORE")
print("=" * 75)


# =====================================================
# 1. CONFIGURAÇÕES
# =====================================================

ARQUIVO_ENTRADA = "dados_com_clusters.csv"

# Limiar já utilizado na modelagem principal
LIMIAR_Z_TRADICIONAL = 2.0

# Limiar usual para o Modified/Robust Z-Score
LIMIAR_Z_ROBUSTO = 3.5

# Constante de consistência para aproximação
# da escala da distribuição normal
FATOR_MAD = 0.6745

TOP_N = 20


# =====================================================
# 2. LEITURA E VALIDAÇÃO DA BASE
# =====================================================

df = pd.read_csv(ARQUIVO_ENTRADA)

colunas_obrigatorias = [
    "cartorio_id",
    "mes",
    "total_selos",
    "cluster_par"
]

colunas_faltantes = [
    coluna
    for coluna in colunas_obrigatorias
    if coluna not in df.columns
]

if colunas_faltantes:
    raise ValueError(
        "Colunas ausentes na base: "
        + ", ".join(colunas_faltantes)
    )

if df.empty:
    raise ValueError(
        "A base de dados está vazia."
    )

df["total_selos"] = pd.to_numeric(
    df["total_selos"],
    errors="coerce"
)

df["cluster_par"] = pd.to_numeric(
    df["cluster_par"],
    errors="coerce"
)

df["mes"] = pd.to_datetime(
    df["mes"],
    errors="coerce"
)

if df[
    [
        "total_selos",
        "cluster_par",
        "mes"
    ]
].isna().any().any():

    nulos = (
        df[
            [
                "total_selos",
                "cluster_par",
                "mes"
            ]
        ]
        .isna()
        .sum()
    )

    nulos = nulos[nulos > 0]

    raise ValueError(
        "Foram encontrados valores inválidos ou nulos:\n"
        + nulos.to_string()
    )

print(f"\nRegistros carregados: {len(df)}")


# =====================================================
# 3. Z-SCORE TRADICIONAL POR CLUSTER
# =====================================================

estatisticas_tradicionais = (
    df
    .groupby("cluster_par")["total_selos"]
    .agg(
        media_grupo="mean",
        desvio_grupo="std"
    )
    .reset_index()
)

df = df.merge(
    estatisticas_tradicionais,
    on="cluster_par",
    how="left"
)

# Evita divisão por zero ou desvio ausente
df["desvio_grupo"] = (
    df["desvio_grupo"]
    .fillna(0)
    .clip(lower=0.001)
)

df["z_score_tradicional"] = (
    (
        df["total_selos"]
        -
        df["media_grupo"]
    )
    /
    df["desvio_grupo"]
)

df["alerta_z_tradicional"] = (
    df["z_score_tradicional"].abs()
    >
    LIMIAR_Z_TRADICIONAL
)


# =====================================================
# 4. MEDIANA E MAD POR CLUSTER
# =====================================================

medianas = (
    df
    .groupby("cluster_par")["total_selos"]
    .median()
    .reset_index(name="mediana_grupo")
)

df = df.merge(
    medianas,
    on="cluster_par",
    how="left"
)

df["desvio_absoluto_mediana"] = (
    df["total_selos"]
    -
    df["mediana_grupo"]
).abs()

mad_por_cluster = (
    df
    .groupby("cluster_par")[
        "desvio_absoluto_mediana"
    ]
    .median()
    .reset_index(name="mad_grupo")
)

df = df.merge(
    mad_por_cluster,
    on="cluster_par",
    how="left"
)


# =====================================================
# 5. TRATAMENTO DE MAD IGUAL A ZERO
# =====================================================

clusters_mad_zero = (
    df.loc[
        df["mad_grupo"].fillna(0) == 0,
        "cluster_par"
    ]
    .drop_duplicates()
    .tolist()
)

if clusters_mad_zero:
    print(
        "\nAviso: clusters com MAD igual a zero:",
        clusters_mad_zero
    )

    print(
        "Nesses casos será utilizado um valor mínimo "
        "de 0,001 para evitar divisão por zero."
    )

df["mad_grupo_ajustado"] = (
    df["mad_grupo"]
    .fillna(0)
    .clip(lower=0.001)
)


# =====================================================
# 6. ROBUST Z-SCORE POR CLUSTER
# =====================================================

df["robust_z_score"] = (
    FATOR_MAD
    *
    (
        df["total_selos"]
        -
        df["mediana_grupo"]
    )
    /
    df["mad_grupo_ajustado"]
)

df["alerta_z_robusto"] = (
    df["robust_z_score"].abs()
    >
    LIMIAR_Z_ROBUSTO
)


# =====================================================
# 7. DIREÇÃO DOS DESVIOS
# =====================================================

def classificar_direcao(valor):
    if valor > 0:
        return "Acima do grupo"

    if valor < 0:
        return "Abaixo do grupo"

    return "Igual ao centro do grupo"


df["direcao_z_tradicional"] = (
    df["z_score_tradicional"]
    .apply(classificar_direcao)
)

df["direcao_z_robusto"] = (
    df["robust_z_score"]
    .apply(classificar_direcao)
)


# =====================================================
# 8. COMPARAÇÃO DOS ALERTAS
# =====================================================

df["alerta_ambos"] = (
    df["alerta_z_tradicional"]
    &
    df["alerta_z_robusto"]
)

df["somente_z_tradicional"] = (
    df["alerta_z_tradicional"]
    &
    ~df["alerta_z_robusto"]
)

df["somente_z_robusto"] = (
    ~df["alerta_z_tradicional"]
    &
    df["alerta_z_robusto"]
)

df["nenhum_metodo"] = (
    ~df["alerta_z_tradicional"]
    &
    ~df["alerta_z_robusto"]
)


# =====================================================
# 9. TABELA 20
# COMPARAÇÃO GERAL DOS MÉTODOS
# =====================================================

total_base = len(df)

quantidade_tradicional = int(
    df["alerta_z_tradicional"].sum()
)

quantidade_robusto = int(
    df["alerta_z_robusto"].sum()
)

quantidade_ambos = int(
    df["alerta_ambos"].sum()
)

quantidade_somente_tradicional = int(
    df["somente_z_tradicional"].sum()
)

quantidade_somente_robusto = int(
    df["somente_z_robusto"].sum()
)

tabela20 = pd.DataFrame(
    {
        "Método": [
            "Z-Score tradicional",
            "Robust Z-Score"
        ],
        "Limiar": [
            f"|Z| > {LIMIAR_Z_TRADICIONAL}",
            f"|RZ| > {LIMIAR_Z_ROBUSTO}"
        ],
        "Alertas": [
            quantidade_tradicional,
            quantidade_robusto
        ]
    }
)

tabela20["Percentual da Base (%)"] = (
    tabela20["Alertas"]
    /
    total_base
    * 100
).round(2)

print(
    "\nTabela 20 - Comparação entre "
    "Z-Score Tradicional e Robust Z-Score"
)

print(
    tabela20.to_string(index=False)
)

tabela20.to_csv(
    "Tabela20_Comparacao_ZScore_Robusto.csv",
    index=False
)


# =====================================================
# 10. TABELA 21
# SOBREPOSIÇÃO ENTRE OS MÉTODOS
# =====================================================

tabela21 = pd.DataFrame(
    {
        "Situação": [
            "Alertas identificados pelos dois métodos",
            "Somente Z-Score tradicional",
            "Somente Robust Z-Score",
            "Não identificados por nenhum método"
        ],
        "Quantidade": [
            quantidade_ambos,
            quantidade_somente_tradicional,
            quantidade_somente_robusto,
            int(df["nenhum_metodo"].sum())
        ]
    }
)

tabela21["Percentual da Base (%)"] = (
    tabela21["Quantidade"]
    /
    total_base
    * 100
).round(2)

print(
    "\nTabela 21 - Sobreposição entre os Métodos"
)

print(
    tabela21.to_string(index=False)
)

tabela21.to_csv(
    "Tabela21_Sobreposicao_ZScore_Robusto.csv",
    index=False
)


# =====================================================
# 11. TABELA 22
# RESULTADOS POR CLUSTER
# =====================================================

tabela22 = (
    df
    .groupby("cluster_par")
    .agg(
        Registros=("cluster_par", "size"),
        Alertas_Z_Tradicional=(
            "alerta_z_tradicional",
            "sum"
        ),
        Alertas_Z_Robusto=(
            "alerta_z_robusto",
            "sum"
        ),
        Alertas_Ambos=(
            "alerta_ambos",
            "sum"
        ),
        Somente_Tradicional=(
            "somente_z_tradicional",
            "sum"
        ),
        Somente_Robusto=(
            "somente_z_robusto",
            "sum"
        )
    )
    .reset_index()
)

tabela22[
    "Taxa_Z_Tradicional (%)"
] = (
    tabela22["Alertas_Z_Tradicional"]
    /
    tabela22["Registros"]
    * 100
).round(2)

tabela22[
    "Taxa_Z_Robusto (%)"
] = (
    tabela22["Alertas_Z_Robusto"]
    /
    tabela22["Registros"]
    * 100
).round(2)

tabela22 = tabela22.rename(
    columns={
        "cluster_par": "Cluster"
    }
)

print(
    "\nTabela 22 - Comparação dos Métodos por Cluster"
)

print(
    tabela22.to_string(index=False)
)

tabela22.to_csv(
    "Tabela22_ZScore_Robusto_Por_Cluster.csv",
    index=False
)


# =====================================================
# 12. CORRELAÇÃO ENTRE OS SCORES
# =====================================================

correlacao_spearman, p_valor = (
    spearmanr(
        df["z_score_tradicional"],
        df["robust_z_score"]
    )
)

tabela_correlacao = pd.DataFrame(
    {
        "Métrica": [
            "Correlação de Spearman",
            "P-valor"
        ],
        "Valor": [
            round(float(correlacao_spearman), 4),
            float(p_valor)
        ]
    }
)

print(
    "\nCorrelação entre os escores"
)

print(
    tabela_correlacao.to_string(index=False)
)

tabela_correlacao.to_csv(
    "Tabela23_Correlacao_ZScore_Robusto.csv",
    index=False
)


# =====================================================
# 13. TOP 20 PELO Z-SCORE TRADICIONAL
# =====================================================

top_tradicional = (
    df
    .assign(
        valor_absoluto_z=(
            df["z_score_tradicional"].abs()
        )
    )
    .sort_values(
        "valor_absoluto_z",
        ascending=False
    )
    .head(TOP_N)
    .copy()
)

top_tradicional["Posição"] = (
    range(1, len(top_tradicional) + 1)
)

top_tradicional["mes"] = (
    top_tradicional["mes"]
    .dt.strftime("%m/%Y")
)

top_tradicional = top_tradicional[
    [
        "Posição",
        "cartorio_id",
        "mes",
        "cluster_par",
        "total_selos",
        "z_score_tradicional",
        "robust_z_score",
        "alerta_z_robusto"
    ]
]

top_tradicional = top_tradicional.rename(
    columns={
        "cartorio_id": "Serventia",
        "mes": "Mês",
        "cluster_par": "Cluster",
        "total_selos": "Total de Selos",
        "z_score_tradicional": "Z-Score",
        "robust_z_score": "Robust Z-Score",
        "alerta_z_robusto": (
            "Também identificado pelo Robust Z-Score"
        )
    }
)

top_tradicional["Z-Score"] = (
    top_tradicional["Z-Score"]
    .round(2)
)

top_tradicional["Robust Z-Score"] = (
    top_tradicional["Robust Z-Score"]
    .round(2)
)

top_tradicional.to_csv(
    "Tabela24_Top20_ZScore_Tradicional.csv",
    index=False
)


# =====================================================
# 14. TOP 20 PELO ROBUST Z-SCORE
# =====================================================

top_robusto = (
    df
    .assign(
        valor_absoluto_robusto=(
            df["robust_z_score"].abs()
        )
    )
    .sort_values(
        "valor_absoluto_robusto",
        ascending=False
    )
    .head(TOP_N)
    .copy()
)

top_robusto["Posição"] = (
    range(1, len(top_robusto) + 1)
)

top_robusto["mes"] = (
    top_robusto["mes"]
    .dt.strftime("%m/%Y")
)

top_robusto = top_robusto[
    [
        "Posição",
        "cartorio_id",
        "mes",
        "cluster_par",
        "total_selos",
        "z_score_tradicional",
        "robust_z_score",
        "alerta_z_tradicional"
    ]
]

top_robusto = top_robusto.rename(
    columns={
        "cartorio_id": "Serventia",
        "mes": "Mês",
        "cluster_par": "Cluster",
        "total_selos": "Total de Selos",
        "z_score_tradicional": "Z-Score",
        "robust_z_score": "Robust Z-Score",
        "alerta_z_tradicional": (
            "Também identificado pelo Z-Score"
        )
    }
)

top_robusto["Z-Score"] = (
    top_robusto["Z-Score"]
    .round(2)
)

top_robusto["Robust Z-Score"] = (
    top_robusto["Robust Z-Score"]
    .round(2)
)

top_robusto.to_csv(
    "Tabela25_Top20_Robust_ZScore.csv",
    index=False
)


# =====================================================
# 15. EXPORTAÇÃO DA BASE COMPLETA
# =====================================================

df.to_csv(
    "dados_comparacao_zscore_robusto.csv",
    index=False
)


# =====================================================
# 16. RESUMO NO TERMINAL
# =====================================================

print("\nResumo do experimento:")

print(
    f"Z-Score tradicional: "
    f"{quantidade_tradicional} alertas "
    f"({quantidade_tradicional / total_base * 100:.2f}%)"
)

print(
    f"Robust Z-Score: "
    f"{quantidade_robusto} alertas "
    f"({quantidade_robusto / total_base * 100:.2f}%)"
)

print(
    f"Alertas em comum: "
    f"{quantidade_ambos}"
)

print(
    f"Somente Z-Score tradicional: "
    f"{quantidade_somente_tradicional}"
)

print(
    f"Somente Robust Z-Score: "
    f"{quantidade_somente_robusto}"
)

print(
    f"Correlação de Spearman: "
    f"{correlacao_spearman:.4f}"
)


print("\nArquivos gerados:")

arquivos_gerados = [
    "Tabela20_Comparacao_ZScore_Robusto.csv",
    "Tabela21_Sobreposicao_ZScore_Robusto.csv",
    "Tabela22_ZScore_Robusto_Por_Cluster.csv",
    "Tabela23_Correlacao_ZScore_Robusto.csv",
    "Tabela24_Top20_ZScore_Tradicional.csv",
    "Tabela25_Top20_Robust_ZScore.csv",
    "dados_comparacao_zscore_robusto.csv"
]

for arquivo in arquivos_gerados:
    print(f"✔ {arquivo}")

print(
    "\nExperimento concluído com sucesso."
)