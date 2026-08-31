import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import (
    silhouette_score,
    davies_bouldin_score,
    calinski_harabasz_score
)

print("=" * 70)
print("ENGENHARIA DE VARIÁVEIS E FORMAÇÃO DOS GRUPOS DE PARES")
print("=" * 70)

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================
arquivo_entrada = "dados_brutos.csv"
arquivo_saida = "dados_com_clusters.csv"

random_state = 42
n_init = 10

# Quatro grupos de porte operacional.
# A escolha prioriza interpretação, tamanho adequado
# dos grupos e compatibilidade com o objetivo da PoC.
k_escolhido = 4

# ==========================================
# 2. LEITURA DA BASE CORRIGIDA
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
    "total_cancelados"
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

# ==========================================
# 4. ENGENHARIA DE VARIÁVEIS
# ==========================================

# Taxa de cancelamento
df["taxa_cancelamento"] = (
    df["total_cancelados"]
    / df["total_selos"].clip(lower=1)
)

# Transformação logarítmica do volume.
# Reduz a influência dos valores extremos.
df["log_total_selos"] = np.log1p(
    df["total_selos"]
)

# ==========================================
# 5. VERIFICAÇÃO DOS DADOS
# ==========================================
variaveis_verificacao = [
    "total_selos",
    "total_cancelados",
    "taxa_cancelamento",
    "log_total_selos"
]

if df[variaveis_verificacao].isnull().any().any():
    print("\nValores nulos encontrados:")
    print(
        df[variaveis_verificacao]
        .isnull()
        .sum()
    )

    raise ValueError(
        "Existem valores nulos nas variáveis necessárias."
    )

if np.isinf(
    df[variaveis_verificacao].to_numpy()
).any():
    raise ValueError(
        "Existem valores infinitos nas variáveis necessárias."
    )

# ==========================================
# 6. VARIÁVEL UTILIZADA NO K-MEANS
# ==========================================
# O K-Means forma grupos de pares somente pelo
# porte operacional da observação.
#
# A taxa de cancelamento não entra no K-Means.
# Ela será analisada posteriormente pelo Z-Score
# dentro dos grupos de porte e pelo Isolation Forest.

features_kmeans = [
    "log_total_selos"
]

print("\nVariável utilizada no K-Means:")
print(features_kmeans)

# ==========================================
# 7. PADRONIZAÇÃO
# ==========================================
scaler = StandardScaler()

X_scaled = scaler.fit_transform(
    df[features_kmeans]
)

# ==========================================
# 8. COMPARAÇÃO DOS VALORES DE K
# ==========================================
resultados_k = []

for k in range(2, 7):

    print(f"Testando k = {k}...")

    modelo_teste = KMeans(
        n_clusters=k,
        random_state=random_state,
        n_init=n_init
    )

    labels_teste = modelo_teste.fit_predict(
        X_scaled
    )

    tamanho_amostra = min(
        5000,
        len(df)
    )

    silhouette = silhouette_score(
        X_scaled,
        labels_teste,
        sample_size=tamanho_amostra,
        random_state=random_state
    )

    davies_bouldin = davies_bouldin_score(
        X_scaled,
        labels_teste
    )

    calinski_harabasz = calinski_harabasz_score(
        X_scaled,
        labels_teste
    )

    quantidades_clusters = (
        pd.Series(labels_teste)
        .value_counts()
    )

    resultados_k.append(
        {
            "k": k,
            "inercia": modelo_teste.inertia_,
            "silhouette": silhouette,
            "davies_bouldin": davies_bouldin,
            "calinski_harabasz": calinski_harabasz,
            "menor_cluster": int(
                quantidades_clusters.min()
            ),
            "maior_cluster": int(
                quantidades_clusters.max()
            )
        }
    )

# ==========================================
# 9. TABELA DE COMPARAÇÃO DE K
# ==========================================
tabela_k = pd.DataFrame(
    resultados_k
)

tabela_k = tabela_k.round(
    {
        "inercia": 2,
        "silhouette": 4,
        "davies_bouldin": 4,
        "calinski_harabasz": 2
    }
)

tabela_k.to_csv(
    "Tabela_Comparacao_K.csv",
    index=False
)

print("\n==============================")
print("COMPARAÇÃO DOS VALORES DE K")
print("==============================")

print(
    tabela_k.to_string(
        index=False
    )
)

print(
    f"\nK escolhido para os grupos de pares: "
    f"{k_escolhido}"
)

# ==========================================
# 10. K-MEANS DEFINITIVO
# ==========================================
kmeans = KMeans(
    n_clusters=k_escolhido,
    random_state=random_state,
    n_init=n_init
)

df["cluster_original"] = kmeans.fit_predict(
    X_scaled
)

# ==========================================
# 11. ORDENAÇÃO DOS CLUSTERS POR PORTE
# ==========================================
# Os números atribuídos pelo K-Means são arbitrários.
# Este procedimento reorganiza os grupos:
#
# Cluster 0: menor porte
# Cluster 1: pequeno/médio porte
# Cluster 2: médio/grande porte
# Cluster 3: maior porte

ordem_clusters = (
    df
    .groupby("cluster_original")[
        "log_total_selos"
    ]
    .mean()
    .sort_values()
    .index
    .tolist()
)

mapa_clusters = {
    cluster_antigo: cluster_novo
    for cluster_novo, cluster_antigo
    in enumerate(ordem_clusters)
}

df["cluster_par"] = (
    df["cluster_original"]
    .map(mapa_clusters)
    .astype(int)
)

df = df.drop(
    columns=["cluster_original"]
)

# ==========================================
# 12. CARACTERIZAÇÃO DOS CLUSTERS
# ==========================================
tabela_clusters = (
    df
    .groupby("cluster_par")
    .agg(
        registros=(
            "cartorio_id",
            "size"
        ),
        serventias_distintas=(
            "cartorio_id",
            "nunique"
        ),
        minimo_total_selos=(
            "total_selos",
            "min"
        ),
        media_total_selos=(
            "total_selos",
            "mean"
        ),
        mediana_total_selos=(
            "total_selos",
            "median"
        ),
        maximo_total_selos=(
            "total_selos",
            "max"
        ),
        media_taxa_cancelamento=(
            "taxa_cancelamento",
            "mean"
        ),
        mediana_taxa_cancelamento=(
            "taxa_cancelamento",
            "median"
        )
    )
    .reset_index()
)

tabela_clusters["percentual_base"] = (
    tabela_clusters["registros"]
    / len(df)
    * 100
)

# Conversão das taxas para percentual
tabela_clusters[
    "media_taxa_cancelamento"
] = (
    tabela_clusters[
        "media_taxa_cancelamento"
    ]
    * 100
)

tabela_clusters[
    "mediana_taxa_cancelamento"
] = (
    tabela_clusters[
        "mediana_taxa_cancelamento"
    ]
    * 100
)

tabela_clusters = tabela_clusters.round(
    {
        "percentual_base": 2,
        "media_total_selos": 2,
        "mediana_total_selos": 2,
        "media_taxa_cancelamento": 4,
        "mediana_taxa_cancelamento": 4
    }
)

tabela_clusters.to_csv(
    "Tabela_Caracterizacao_Clusters.csv",
    index=False
)

print("\n==============================")
print("CARACTERIZAÇÃO DOS CLUSTERS")
print("==============================")

print(
    tabela_clusters.to_string(
        index=False
    )
)

# ==========================================
# 13. DISTRIBUIÇÃO DOS CLUSTERS POR ANO
# ==========================================
tabela_cluster_ano = (
    df
    .assign(
        Ano=df["mes"].dt.year
    )
    .groupby(
        [
            "Ano",
            "cluster_par"
        ]
    )
    .size()
    .reset_index(
        name="Quantidade"
    )
)

tabela_cluster_ano.to_csv(
    "Tabela_Clusters_Por_Ano.csv",
    index=False
)

# ==========================================
# 14. SALVAR BASE COM CLUSTERS
# ==========================================
df = df.sort_values(
    [
        "cartorio_id",
        "mes"
    ]
).reset_index(drop=True)

df.to_csv(
    arquivo_saida,
    index=False
)

print("\nBase com clusters salva:")
print(f"✔ {arquivo_saida}")

# ==========================================
# 15. GRÁFICO DO MÉTODO DO COTOVELO
# ==========================================
plt.figure(
    figsize=(8, 5)
)

plt.plot(
    tabela_k["k"],
    tabela_k["inercia"],
    marker="o",
    color="steelblue"
)

plt.axvline(
    x=k_escolhido,
    color="red",
    linestyle="--",
    label=f"k escolhido = {k_escolhido}"
)

plt.title(
    "Método do Cotovelo para Definição do Número de Clusters"
)

plt.xlabel(
    "Número de clusters (k)"
)

plt.ylabel(
    "Inércia"
)

plt.xticks(
    tabela_k["k"]
)

plt.legend()

plt.grid(
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "grafico_metodo_cotovelo_corrigido.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 16. GRÁFICO DO SILHOUETTE
# ==========================================
plt.figure(
    figsize=(8, 5)
)

plt.plot(
    tabela_k["k"],
    tabela_k["silhouette"],
    marker="o",
    color="darkgreen"
)

plt.axvline(
    x=k_escolhido,
    color="red",
    linestyle="--",
    label=f"k escolhido = {k_escolhido}"
)

plt.title(
    "Coeficiente Silhouette por Número de Clusters"
)

plt.xlabel(
    "Número de clusters (k)"
)

plt.ylabel(
    "Coeficiente Silhouette"
)

plt.xticks(
    tabela_k["k"]
)

plt.legend()

plt.grid(
    alpha=0.3
)

plt.tight_layout()

plt.savefig(
    "grafico_silhouette_corrigido.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 17. QUANTIDADE POR CLUSTER
# ==========================================
quantidade_clusters = (
    df["cluster_par"]
    .value_counts()
    .sort_index()
)

plt.figure(
    figsize=(8, 5)
)

quantidade_clusters.plot(
    kind="bar",
    color="steelblue"
)

plt.title(
    "Quantidade de Observações por Grupo de Porte"
)

plt.xlabel(
    "Cluster"
)

plt.ylabel(
    "Quantidade de observações"
)

plt.xticks(
    rotation=0
)

plt.tight_layout()

plt.savefig(
    "grafico_quantidade_clusters_corrigido.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 18. GRÁFICO DOS GRUPOS DE PARES
# ==========================================
# A taxa de cancelamento aparece apenas no eixo
# vertical para interpretação. Ela não foi usada
# na formação dos clusters.

tamanho_amostra_grafico = min(
    15000,
    len(df)
)

amostra_grafico = df.sample(
    n=tamanho_amostra_grafico,
    random_state=random_state
)

plt.figure(
    figsize=(10, 6)
)

for cluster in sorted(
    amostra_grafico["cluster_par"].unique()
):

    dados_cluster = amostra_grafico[
        amostra_grafico["cluster_par"]
        == cluster
    ]

    plt.scatter(
        dados_cluster["log_total_selos"],
        dados_cluster["taxa_cancelamento"] * 100,
        s=12,
        alpha=0.45,
        label=f"Cluster {cluster}"
    )

plt.title(
    "Grupos de Pares por Porte Operacional"
)

plt.xlabel(
    "Volume de selos em escala logarítmica"
)

plt.ylabel(
    "Taxa de cancelamento (%)"
)

plt.legend()

plt.grid(
    alpha=0.2
)

plt.tight_layout()

plt.savefig(
    "grafico_clusters_corrigido.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 19. BOXPLOT DO VOLUME POR CLUSTER
# ==========================================
clusters_ordenados = sorted(
    df["cluster_par"].unique()
)

dados_boxplot = [
    df.loc[
        df["cluster_par"] == cluster,
        "log_total_selos"
    ]
    for cluster in clusters_ordenados
]

rotulos_boxplot = [
    f"Cluster {cluster}"
    for cluster in clusters_ordenados
]

plt.figure(
    figsize=(9, 6)
)

plt.boxplot(
    dados_boxplot,
    tick_labels=rotulos_boxplot,
    showfliers=False
)

plt.title(
    "Distribuição do Volume por Grupo de Porte"
)

plt.xlabel(
    "Cluster"
)

plt.ylabel(
    "Volume de selos em escala logarítmica"
)

plt.grid(
    axis="y",
    alpha=0.2
)

plt.tight_layout()

plt.savefig(
    "grafico_boxplot_clusters_corrigido.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 20. ESTATÍSTICAS DESCRITIVAS
# ==========================================
estatisticas = df[
    [
        "total_selos",
        "log_total_selos",
        "taxa_cancelamento"
    ]
].describe()

estatisticas.to_csv(
    "Estatisticas_Descritivas_Corrigidas.csv"
)

print("\n==============================")
print("ESTATÍSTICAS DESCRITIVAS")
print("==============================")

print(
    estatisticas
)

print("\nArquivos gerados:")
print("✔ dados_com_clusters.csv")
print("✔ Tabela_Comparacao_K.csv")
print("✔ Tabela_Caracterizacao_Clusters.csv")
print("✔ Tabela_Clusters_Por_Ano.csv")
print("✔ Estatisticas_Descritivas_Corrigidas.csv")
print("✔ grafico_metodo_cotovelo_corrigido.png")
print("✔ grafico_silhouette_corrigido.png")
print("✔ grafico_quantidade_clusters_corrigido.png")
print("✔ grafico_clusters_corrigido.png")
print("✔ grafico_boxplot_clusters_corrigido.png")
