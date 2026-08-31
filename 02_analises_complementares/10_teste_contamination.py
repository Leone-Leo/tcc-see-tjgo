import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

print("=" * 70)
print("AVALIAÇÃO DO PARÂMETRO CONTAMINATION")
print("=" * 70)

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

ARQUIVO_ENTRADA = "dados_com_clusters.csv"

VALORES_CONTAMINATION = [
    0.01,
    0.03,
    0.05
]

LIMIAR_Z_ALERTA = 2
LIMIAR_Z_CRITICO = 3

RANDOM_STATE = 42
N_ESTIMATORS = 200

# ==========================================
# 2. LEITURA DA BASE
# ==========================================

df = pd.read_csv(
    ARQUIVO_ENTRADA,
    parse_dates=["mes"]
)

colunas_obrigatorias = [
    "cartorio_id",
    "mes",
    "total_selos",
    "log_total_selos",
    "taxa_cancelamento",
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

print(f"\nRegistros carregados: {len(df):,}")

# ==========================================
# 3. Z-SCORE DA TAXA DE CANCELAMENTO
# POR CLUSTER DE PORTE
# ==========================================

df["media_cancelamento_grupo"] = (
    df.groupby("cluster_par")[
        "taxa_cancelamento"
    ].transform("mean")
)

df["desvio_cancelamento_grupo"] = (
    df.groupby("cluster_par")[
        "taxa_cancelamento"
    ].transform("std")
)

desvio = (
    df["desvio_cancelamento_grupo"]
    .replace(0, np.nan)
)

df["z_score_par"] = (
    (
        df["taxa_cancelamento"]
        - df["media_cancelamento_grupo"]
    )
    / desvio
)

df["z_score_par"] = (
    df["z_score_par"]
    .replace(
        [np.inf, -np.inf],
        np.nan
    )
    .fillna(0)
)

# Somente cancelamentos acima do grupo
df["alerta_zscore"] = (
    df["z_score_par"] > LIMIAR_Z_ALERTA
)

# ==========================================
# 4. VARIÁVEIS DO ISOLATION FOREST
# ==========================================

features = [
    "log_total_selos",
    "taxa_cancelamento"
]

scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    df[features]
)

# ==========================================
# 5. TESTES DE CONTAMINATION
# ==========================================

resultados = []
resultados_detalhados = {}

total_base = len(df)

for contamination in VALORES_CONTAMINATION:

    print(
        f"Testando contamination = "
        f"{contamination * 100:.0f}%..."
    )

    modelo = IsolationForest(
        n_estimators=N_ESTIMATORS,
        contamination=contamination,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    predicao = modelo.fit_predict(
        X_scaled
    )

    alerta_iforest = (
        predicao == -1
    )

    alerta_hibrido = (
        df["alerta_zscore"]
        | alerta_iforest
    )

    risco_critico = (
        (
            df["z_score_par"]
            > LIMIAR_Z_CRITICO
        )
        & alerta_iforest
    )

    convergencia = (
        df["alerta_zscore"]
        & alerta_iforest
    )

    somente_iforest = (
        ~df["alerta_zscore"]
        & alerta_iforest
    )

    somente_zscore = (
        df["alerta_zscore"]
        & ~alerta_iforest
    )

    quantidade_iforest = int(
        alerta_iforest.sum()
    )

    quantidade_hibrido = int(
        alerta_hibrido.sum()
    )

    quantidade_criticos = int(
        risco_critico.sum()
    )

    quantidade_convergencia = int(
        convergencia.sum()
    )

    quantidade_somente_iforest = int(
        somente_iforest.sum()
    )

    quantidade_somente_zscore = int(
        somente_zscore.sum()
    )

    resultados.append(
        {
            "Contamination (%)": int(
                contamination * 100
            ),
            "Alertas Isolation Forest": (
                quantidade_iforest
            ),
            "Isolation Forest (% da Base)": round(
                quantidade_iforest
                / total_base
                * 100,
                2
            ),
            "Alertas Híbridos": (
                quantidade_hibrido
            ),
            "Modelo Híbrido (% da Base)": round(
                quantidade_hibrido
                / total_base
                * 100,
                2
            ),
            "Riscos Críticos": (
                quantidade_criticos
            ),
            "Riscos Críticos (% da Base)": round(
                quantidade_criticos
                / total_base
                * 100,
                4
            ),
            "Convergência Z-Score + IF": (
                quantidade_convergencia
            ),
            "Somente Isolation Forest": (
                quantidade_somente_iforest
            ),
            "Somente Z-Score": (
                quantidade_somente_zscore
            )
        }
    )

    # Mantido somente na memória para produzir a Tabela 19
    resultados_detalhados[contamination] = {
        "iforest": alerta_iforest,
        "hibrido": alerta_hibrido
    }

# ==========================================
# 6. TABELA 18 — COMPARAÇÃO
# ==========================================

tabela18 = pd.DataFrame(
    resultados
)

print(
    "\nTabela 18 — Comparação do Parâmetro Contamination"
)

print(
    tabela18.to_string(index=False)
)

tabela18.to_csv(
    "Tabela18_Comparacao_Contamination.csv",
    index=False
)

# ==========================================
# 7. TABELA 19 — NOVOS E COMPARTILHADOS
# ==========================================

base_1_iforest = resultados_detalhados[
    0.01
]["iforest"]

base_1_hibrido = resultados_detalhados[
    0.01
]["hibrido"]

ids_1_iforest = set(
    df.index[base_1_iforest]
)

ids_1_hibrido = set(
    df.index[base_1_hibrido]
)

comparacoes = []

for contamination in [
    0.03,
    0.05
]:

    alerta_iforest_teste = (
        resultados_detalhados[
            contamination
        ]["iforest"]
    )

    alerta_hibrido_teste = (
        resultados_detalhados[
            contamination
        ]["hibrido"]
    )

    ids_teste_iforest = set(
        df.index[alerta_iforest_teste]
    )

    ids_teste_hibrido = set(
        df.index[alerta_hibrido_teste]
    )

    compartilhados_iforest = len(
        ids_1_iforest
        & ids_teste_iforest
    )

    novos_iforest = len(
        ids_teste_iforest
        - ids_1_iforest
    )

    compartilhados_hibrido = len(
        ids_1_hibrido
        & ids_teste_hibrido
    )

    novos_hibrido = len(
        ids_teste_hibrido
        - ids_1_hibrido
    )

    comparacoes.append(
        {
            "Contamination comparada (%)": int(
                contamination * 100
            ),
            "Alertas IF compartilhados com 1%": (
                compartilhados_iforest
            ),
            "Novos alertas IF": (
                novos_iforest
            ),
            "Alertas híbridos compartilhados com 1%": (
                compartilhados_hibrido
            ),
            "Novos alertas híbridos": (
                novos_hibrido
            )
        }
    )

tabela19 = pd.DataFrame(
    comparacoes
)

print(
    "\nTabela 19 — Comparação com Contamination de 1%"
)

print(
    tabela19.to_string(index=False)
)

tabela19.to_csv(
    "Tabela19_Sobreposicao_Contamination.csv",
    index=False
)

# ==========================================
# 8. RESUMO
# ==========================================

print("\nConfigurações utilizadas:")

print(
    f"Z-Score para alerta: "
    f"Z > {LIMIAR_Z_ALERTA}"
)

print(
    f"Z-Score para risco crítico: "
    f"Z > {LIMIAR_Z_CRITICO}"
)

print(
    "Variáveis do Isolation Forest: "
    "log_total_selos e taxa_cancelamento"
)

print(
    "Valores testados: 1%, 3% e 5%"
)

print("\nArquivos gerados:")
print("✔ Tabela18_Comparacao_Contamination.csv")
print("✔ Tabela19_Sobreposicao_Contamination.csv")

print("\nExperimento concluído com sucesso.")