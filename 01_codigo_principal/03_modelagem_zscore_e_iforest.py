import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

print("=" * 70)
print("MODELAGEM CORRIGIDA: Z-SCORE E ISOLATION FOREST")
print("=" * 70)

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
arquivo_entrada = "dados_com_clusters.csv"
arquivo_base_modelada = "dados_modelados_corrigidos.csv"
arquivo_alertas = "tabela_alertas_final.csv"

random_state = 42
contamination_escolhido = 0.01
n_estimators = 200

# Limiares do Z-Score
limiar_moderado = 2
limiar_critico = 3

# ==========================================
# 2. LEITURA DA BASE
# ==========================================
df = pd.read_csv(
    arquivo_entrada,
    parse_dates=["mes"]
)

print("\nBase carregada.")
print(f"Quantidade de observações: {len(df)}")

# ==========================================
# 3. VALIDAÇÃO DAS COLUNAS
# ==========================================
colunas_obrigatorias = [
    "cartorio_id",
    "mes",
    "total_selos",
    "total_cancelados",
    "taxa_cancelamento",
    "log_total_selos",
    "cluster_par"
]

colunas_ausentes = [
    coluna
    for coluna in colunas_obrigatorias
    if coluna not in df.columns
]

if colunas_ausentes:
    raise ValueError(
        "Colunas ausentes na base: "
        + ", ".join(colunas_ausentes)
    )

if df["mes"].isna().any():
    raise ValueError(
        "Foram encontradas datas inválidas na coluna 'mes'."
    )

if df[colunas_obrigatorias].isnull().any().any():
    print("\nValores nulos encontrados:")
    print(
        df[colunas_obrigatorias]
        .isnull()
        .sum()
    )

    raise ValueError(
        "Existem valores nulos nas colunas obrigatórias."
    )

if np.isinf(
    df[
        [
            "total_selos",
            "total_cancelados",
            "taxa_cancelamento",
            "log_total_selos"
        ]
    ].to_numpy()
).any():
    raise ValueError(
        "Existem valores infinitos na base."
    )

duplicados = df.duplicated(
    subset=[
        "cartorio_id",
        "mes"
    ]
).sum()

if duplicados > 0:
    raise ValueError(
        f"Foram encontradas {duplicados} duplicidades "
        "na chave Serventia × Mês."
    )

quantidade_clusters = df["cluster_par"].nunique()

print(f"Quantidade de clusters: {quantidade_clusters}")

# ==========================================
# 4. ESTATÍSTICAS DA TAXA DE CANCELAMENTO
# POR GRUPO DE PARES
# ==========================================
estatisticas_grupo = (
    df
    .groupby("cluster_par")
    .agg(
        quantidade_grupo=(
            "cartorio_id",
            "size"
        ),
        media_cancelamento_grupo=(
            "taxa_cancelamento",
            "mean"
        ),
        mediana_cancelamento_grupo=(
            "taxa_cancelamento",
            "median"
        ),
        desvio_cancelamento_grupo=(
            "taxa_cancelamento",
            "std"
        ),
        percentil90_cancelamento_grupo=(
            "taxa_cancelamento",
            lambda serie: serie.quantile(0.90)
        ),
        media_selos_grupo=(
            "total_selos",
            "mean"
        ),
        mediana_selos_grupo=(
            "total_selos",
            "median"
        )
    )
    .reset_index()
)

# Verificação de tamanho mínimo dos grupos
grupos_pequenos = estatisticas_grupo[
    estatisticas_grupo["quantidade_grupo"] < 30
]

if not grupos_pequenos.empty:
    raise ValueError(
        "Existem clusters com menos de 30 observações. "
        "Revise a formação dos grupos de pares."
    )

# Evita divisão por zero no cálculo do Z-Score
estatisticas_grupo[
    "desvio_cancelamento_grupo"
] = (
    estatisticas_grupo[
        "desvio_cancelamento_grupo"
    ]
    .fillna(0)
    .clip(lower=0.000000001)
)

df = df.merge(
    estatisticas_grupo,
    on="cluster_par",
    how="left",
    validate="many_to_one"
)

# ==========================================
# 5. Z-SCORE DA TAXA DE CANCELAMENTO
# ==========================================
df["z_score_par"] = (
    df["taxa_cancelamento"]
    - df["media_cancelamento_grupo"]
) / df["desvio_cancelamento_grupo"]

# Diferença em pontos percentuais
df["diferenca_cancelamento_pp"] = (
    df["taxa_cancelamento"]
    - df["media_cancelamento_grupo"]
) * 100

# Razão entre a taxa observada e a média do grupo
df["razao_cancelamento_grupo"] = np.where(
    df["media_cancelamento_grupo"] > 0,
    (
        df["taxa_cancelamento"]
        / df["media_cancelamento_grupo"]
    ),
    np.nan
)

print("\nEstatísticas da taxa de cancelamento por cluster:")

estatisticas_exibicao = (
    estatisticas_grupo.copy()
)

estatisticas_exibicao[
    "media_cancelamento_grupo_pct"
] = (
    estatisticas_exibicao[
        "media_cancelamento_grupo"
    ] * 100
)

estatisticas_exibicao[
    "mediana_cancelamento_grupo_pct"
] = (
    estatisticas_exibicao[
        "mediana_cancelamento_grupo"
    ] * 100
)

estatisticas_exibicao[
    "percentil90_cancelamento_grupo_pct"
] = (
    estatisticas_exibicao[
        "percentil90_cancelamento_grupo"
    ] * 100
)

print(
    estatisticas_exibicao[
        [
            "cluster_par",
            "quantidade_grupo",
            "media_cancelamento_grupo_pct",
            "mediana_cancelamento_grupo_pct",
            "percentil90_cancelamento_grupo_pct",
            "media_selos_grupo",
            "mediana_selos_grupo"
        ]
    ]
    .round(4)
    .to_string(index=False)
)

# ==========================================
# 6. ISOLATION FOREST
# ==========================================
features_iforest = [
    "log_total_selos",
    "taxa_cancelamento"
]

scaler_iforest = StandardScaler()

X_iforest = scaler_iforest.fit_transform(
    df[features_iforest]
)

iforest = IsolationForest(
    n_estimators=n_estimators,
    contamination=contamination_escolhido,
    random_state=random_state,
    n_jobs=-1
)

df["iforest_score"] = iforest.fit_predict(
    X_iforest
)

# Quanto menor, mais atípica é a observação
df["iforest_decision"] = (
    iforest.decision_function(
        X_iforest
    )
)

# Inversão para que valores maiores representem
# maior intensidade da anomalia
df["iforest_intensidade"] = (
    -df["iforest_decision"]
)

# ==========================================
# 7. FLAGS DOS MÉTODOS
# ==========================================

# Z-Score positivo: cancelamento acima do grupo
df["flag_z_moderado"] = (
    df["z_score_par"] > limiar_moderado
)

df["flag_z_critico"] = (
    df["z_score_par"] > limiar_critico
)

df["flag_iforest"] = (
    df["iforest_score"] == -1
)

# ==========================================
# 8. CLASSIFICAÇÃO METODOLÓGICA
# ==========================================
condicoes = [
    (
        df["flag_z_critico"]
        & df["flag_iforest"]
    ),
    df["flag_z_moderado"],
    df["flag_iforest"]
]

classificacoes = [
    "RISCO CRÍTICO",
    "ALERTA MODERADO",
    "ALERTA MULTIVARIADO"
]

df["status_metodologico"] = np.select(
    condicoes,
    classificacoes,
    default="NORMAL"
)

# ==========================================
# 9. CATEGORIA DO MOTIVO
# ==========================================
def gerar_categoria_motivo(row):
    motivos = []

    if row["flag_z_critico"]:
        motivos.append(
            "Cancelamento muito acima do grupo"
        )

    elif row["flag_z_moderado"]:
        motivos.append(
            "Cancelamento acima do grupo"
        )

    if row["flag_iforest"]:
        motivos.append(
            "Anomalia multivariada"
        )

    if not motivos:
        return "Sem motivo adicional"

    return " + ".join(motivos)


df["categoria_motivo"] = df.apply(
    gerar_categoria_motivo,
    axis=1
)

# ==========================================
# 10. EXPLICAÇÃO DO ALERTA
# ==========================================
def gerar_explicacao_alerta(row):
    motivos = []

    if row["flag_z_critico"]:
        motivos.append(
            "Taxa de cancelamento superior a três "
            "desvios-padrão em relação ao grupo de porte"
        )

    elif row["flag_z_moderado"]:
        motivos.append(
            "Taxa de cancelamento superior a dois "
            "desvios-padrão em relação ao grupo de porte"
        )

    if row["flag_iforest"]:
        motivos.append(
            "Combinação entre volume e cancelamento "
            "classificada como atípica pelo Isolation Forest"
        )

    if not motivos:
        return "Sem motivo adicional identificado"

    return " | ".join(motivos)


df["explicacao_alerta"] = df.apply(
    gerar_explicacao_alerta,
    axis=1
)

# ==========================================
# 11. JUSTIFICATIVA AUTOMÁTICA
# ==========================================
def gerar_justificativa(row):
    partes = []

    cluster = int(
        row["cluster_par"]
    )

    taxa_observada = (
        row["taxa_cancelamento"]
        * 100
    )

    taxa_media_grupo = (
        row["media_cancelamento_grupo"]
        * 100
    )

    if row["flag_z_moderado"]:
        partes.append(
            f"taxa de cancelamento de "
            f"{taxa_observada:.4f}%"
        )

        partes.append(
            f"média de {taxa_media_grupo:.4f}% "
            f"no Cluster {cluster}"
        )

        partes.append(
            f"Z-Score de {row['z_score_par']:.2f}"
        )

    if row["flag_iforest"]:
        partes.append(
            "combinação entre volume operacional e "
            "cancelamento classificada como atípica "
            "pelo Isolation Forest"
        )

    if not partes:
        return (
            "Registro sem evidência adicional "
            "de comportamento atípico."
        )

    justificativa = "; ".join(
        partes
    )

    return (
        justificativa[0].upper()
        + justificativa[1:]
        + "."
    )


df["justificativa_alerta"] = df.apply(
    gerar_justificativa,
    axis=1
)

# ==========================================
# 12. SCORE DE PRIORIDADE
# ==========================================
# O score utiliza apenas o desvio positivo da taxa
# de cancelamento e a convergência do Isolation Forest.
#
# Score = max(Z, 0) + I
#
# I = 1 quando o Isolation Forest identifica anomalia.

df["score_prioridade"] = (
    df["z_score_par"].clip(lower=0)
    + df["flag_iforest"].astype(int)
)

# ==========================================
# 13. FILTRO E RANKING DOS ALERTAS
# ==========================================
alertas = df[
    df["status_metodologico"] != "NORMAL"
].copy()

alertas = (
    alertas
    .sort_values(
        by=[
            "score_prioridade",
            "iforest_intensidade"
        ],
        ascending=[
            False,
            False
        ]
    )
    .reset_index(drop=True)
)

alertas["posicao_ranking"] = (
    alertas.index + 1
)

# ==========================================
# 14. DISTRIBUIÇÃO DOS STATUS
# ==========================================
distribuicao_status = (
    alertas["status_metodologico"]
    .value_counts()
    .rename_axis("Status")
    .reset_index(name="Quantidade")
)

if len(alertas) > 0:
    distribuicao_status[
        "Percentual_Alertas"
    ] = (
        distribuicao_status["Quantidade"]
        / len(alertas)
        * 100
    ).round(2)

    distribuicao_status[
        "Percentual_Base"
    ] = (
        distribuicao_status["Quantidade"]
        / len(df)
        * 100
    ).round(2)
else:
    distribuicao_status[
        "Percentual_Alertas"
    ] = 0

    distribuicao_status[
        "Percentual_Base"
    ] = 0

# ==========================================
# 15. DISTRIBUIÇÃO DOS MOTIVOS
# ==========================================
distribuicao_motivos = (
    alertas["categoria_motivo"]
    .value_counts()
    .rename_axis("Motivo")
    .reset_index(name="Quantidade")
)

if len(alertas) > 0:
    distribuicao_motivos[
        "Percentual"
    ] = (
        distribuicao_motivos["Quantidade"]
        / len(alertas)
        * 100
    ).round(2)
else:
    distribuicao_motivos[
        "Percentual"
    ] = 0

# ==========================================
# 16. TOP 20 CASOS
# ==========================================
colunas_top20 = [
    "posicao_ranking",
    "cartorio_id",
    "mes",
    "cluster_par",
    "total_selos",
    "total_cancelados",
    "taxa_cancelamento",
    "media_cancelamento_grupo",
    "z_score_par",
    "iforest_score",
    "iforest_intensidade",
    "score_prioridade",
    "status_metodologico",
    "categoria_motivo",
    "justificativa_alerta"
]

top20 = (
    alertas[colunas_top20]
    .head(20)
    .copy()
)

# ==========================================
# 17. TABELA DE ESTATÍSTICAS DOS GRUPOS
# ==========================================
tabela_estatisticas_grupos = (
    estatisticas_grupo.copy()
)

tabela_estatisticas_grupos[
    "media_cancelamento_pct"
] = (
    tabela_estatisticas_grupos[
        "media_cancelamento_grupo"
    ] * 100
)

tabela_estatisticas_grupos[
    "mediana_cancelamento_pct"
] = (
    tabela_estatisticas_grupos[
        "mediana_cancelamento_grupo"
    ] * 100
)

tabela_estatisticas_grupos[
    "desvio_cancelamento_pct"
] = (
    tabela_estatisticas_grupos[
        "desvio_cancelamento_grupo"
    ] * 100
)

tabela_estatisticas_grupos[
    "percentil90_cancelamento_pct"
] = (
    tabela_estatisticas_grupos[
        "percentil90_cancelamento_grupo"
    ] * 100
)

# ==========================================
# 18. EXPORTAÇÃO
# ==========================================
df.to_csv(
    arquivo_base_modelada,
    index=False
)

alertas.to_csv(
    arquivo_alertas,
    index=False
)

distribuicao_status.to_csv(
    "Tabela_Distribuicao_Alertas.csv",
    index=False
)

distribuicao_motivos.to_csv(
    "Tabela_Distribuicao_Motivos.csv",
    index=False
)

top20.to_csv(
    "Tabela_Top20_Casos.csv",
    index=False
)

tabela_estatisticas_grupos.to_csv(
    "Tabela_Estatisticas_Cancelamento_Clusters.csv",
    index=False
)

# ==========================================
# 19. ESTATÍSTICAS DESCRITIVAS
# ==========================================
estatisticas_modelagem = df[
    [
        "total_selos",
        "total_cancelados",
        "taxa_cancelamento",
        "z_score_par",
        "iforest_decision",
        "score_prioridade"
    ]
].describe()

estatisticas_modelagem.to_csv(
    "Estatisticas_Modelagem_Corrigida.csv"
)

# ==========================================
# 20. RESULTADOS NO TERMINAL
# ==========================================
print("\n" + "=" * 70)
print("PROCESSAMENTO CONCLUÍDO")
print("=" * 70)

print(
    f"Total de observações analisadas: {len(df)}"
)

print(
    f"Total de alertas gerados: {len(alertas)}"
)

if len(df) > 0:
    print(
        "Percentual de alertas na base:",
        f"{len(alertas) / len(df) * 100:.2f}%"
    )

print("\nDistribuição dos status:")

print(
    distribuicao_status.to_string(
        index=False
    )
)

print("\nDistribuição dos motivos:")

print(
    distribuicao_motivos.to_string(
        index=False
    )
)

print("\nTop 20 casos prioritários:")

print(
    top20.to_string(
        index=False
    )
)

print("\nArquivos gerados:")
print("✔ dados_modelados_corrigidos.csv")
print("✔ tabela_alertas_final.csv")
print("✔ Tabela_Distribuicao_Alertas.csv")
print("✔ Tabela_Distribuicao_Motivos.csv")
print("✔ Tabela_Top20_Casos.csv")
print("✔ Tabela_Estatisticas_Cancelamento_Clusters.csv")
print("✔ Estatisticas_Modelagem_Corrigida.csv")