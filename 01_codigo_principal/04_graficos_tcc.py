import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

print("=" * 70)
print("GERAÇÃO DOS GRÁFICOS CORRIGIDOS DO TCC")
print("=" * 70)

# ==========================================
# 1. CONFIGURAÇÃO VISUAL
# ==========================================
sns.set_theme(
    style="whitegrid",
    context="notebook"
)

plt.rcParams["figure.dpi"] = 120
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["axes.titleweight"] = "bold"

cores_clusters = {
    0: "#4C78A8",
    1: "#F58518",
    2: "#54A24B",
    3: "#E45756"
}

nomes_clusters = {
    0: "Muito pequeno porte",
    1: "Pequeno porte",
    2: "Médio porte",
    3: "Grande porte"
}

cores_status = {
    "RISCO CRÍTICO": "#C62828",
    "ALERTA MODERADO": "#F9A825",
    "ALERTA MULTIVARIADO": "#1565C0"
}

# ==========================================
# 2. FUNÇÃO PARA SALVAR FIGURAS
# ==========================================
def salvar_figura(nome_arquivo):
    plt.tight_layout()

    plt.savefig(
        nome_arquivo,
        dpi=300,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close()

    print(f"✔ {nome_arquivo}")


# ==========================================
# 3. LEITURA DAS BASES
# ==========================================
df = pd.read_csv(
    "dados_com_clusters.csv",
    parse_dates=["mes"]
)

print(f"\nBase principal: {len(df)} observações")

try:
    alertas = pd.read_csv(
        "tabela_alertas_final.csv",
        parse_dates=["mes"]
    )

    print(f"Base de alertas: {len(alertas)} observações")

except FileNotFoundError:
    alertas = None

    print(
        "Aviso: tabela_alertas_final.csv não encontrada."
    )

try:
    diagnostico_inutilizado = pd.read_csv(
        "Diagnostico_Inutilizado_Por_Ano.csv"
    )

except FileNotFoundError:
    diagnostico_inutilizado = None

    print(
        "Aviso: Diagnostico_Inutilizado_Por_Ano.csv "
        "não encontrado."
    )

try:
    tabela_k = pd.read_csv(
        "Tabela_Comparacao_K.csv"
    )

except FileNotFoundError:
    tabela_k = None

    print(
        "Aviso: Tabela_Comparacao_K.csv não encontrada."
    )

# ==========================================
# 4. VALIDAÇÃO DAS COLUNAS
# ==========================================
colunas_df = [
    "cartorio_id",
    "mes",
    "total_selos",
    "taxa_cancelamento",
    "log_total_selos",
    "cluster_par"
]

colunas_ausentes = [
    coluna
    for coluna in colunas_df
    if coluna not in df.columns
]

if colunas_ausentes:
    raise ValueError(
        "Colunas ausentes em dados_com_clusters.csv: "
        + ", ".join(colunas_ausentes)
    )

df["taxa_cancelamento_pct"] = (
    df["taxa_cancelamento"]
    * 100
)

df["cluster_nome"] = (
    df["cluster_par"]
    .map(nomes_clusters)
)

# ==========================================
# GRÁFICO 01
# DISTRIBUIÇÃO DO VOLUME EM ESCALA LOG
# ==========================================
plt.figure(
    figsize=(10, 6)
)

sns.histplot(
    data=df,
    x="log_total_selos",
    bins=50,
    color="#4C78A8",
    edgecolor="white"
)

plt.title(
    "Distribuição do Volume de Selos em Escala Logarítmica"
)

plt.xlabel(
    "log(1 + total de selos)"
)

plt.ylabel(
    "Quantidade de observações"
)

salvar_figura(
    "grafico_01_histograma_log.png"
)

# ==========================================
# GRÁFICO 02
# BOXPLOT DO VOLUME
# ==========================================
plt.figure(
    figsize=(9, 6)
)

sns.boxplot(
    y=df["log_total_selos"],
    color="#4C78A8",
    showfliers=True,
    fliersize=2
)

plt.title(
    "Distribuição do Volume Mensal de Selos"
)

plt.ylabel(
    "Volume de selos em escala logarítmica"
)

plt.xlabel("")

salvar_figura(
    "grafico_02_boxplot_total_selos.png"
)

# ==========================================
# GRÁFICO 03
# DISTRIBUIÇÃO DA TAXA DE CANCELAMENTO
# ==========================================
# O percentil 99 é utilizado somente para melhorar
# a visualização. Os valores extremos não são
# removidos da base nem da modelagem.

limite_visual_cancelamento = (
    df["taxa_cancelamento_pct"]
    .quantile(0.99)
)

if limite_visual_cancelamento <= 0:
    limite_visual_cancelamento = (
        df["taxa_cancelamento_pct"]
        .max()
    )

dados_cancelamento_visual = df[
    df["taxa_cancelamento_pct"]
    <= limite_visual_cancelamento
].copy()

plt.figure(
    figsize=(10, 6)
)

sns.histplot(
    data=dados_cancelamento_visual,
    x="taxa_cancelamento_pct",
    bins=50,
    color="#E45756",
    edgecolor="white"
)

plt.title(
    "Distribuição da Taxa de Cancelamento até o Percentil 99"
)

plt.xlabel(
    "Taxa de cancelamento (%)"
)

plt.ylabel(
    "Quantidade de observações"
)

salvar_figura(
    "grafico_03_hist_cancelamento.png"
)

# ==========================================
# GRÁFICO 04
# QUALIDADE TEMPORAL DO CAMPO INUTILIZADO
# Substitui o antigo gráfico sem guia
# ==========================================
if diagnostico_inutilizado is not None:

    colunas_diagnostico = [
        "Ano",
        "percentual_inutilizado_nulo"
    ]

    ausentes_diagnostico = [
        coluna
        for coluna in colunas_diagnostico
        if coluna not in diagnostico_inutilizado.columns
    ]

    if not ausentes_diagnostico:

        diagnostico_plot = (
            diagnostico_inutilizado[
                diagnostico_inutilizado["Ano"]
                .between(
                    2016,
                    2025
                )
            ]
            .sort_values("Ano")
            .copy()
        )

        plt.figure(
            figsize=(11, 6)
        )

        sns.lineplot(
            data=diagnostico_plot,
            x="Ano",
            y="percentual_inutilizado_nulo",
            marker="o",
            linewidth=2.5,
            color="#7A5195"
        )

        plt.axvline(
            x=2019,
            color="#C62828",
            linestyle="--",
            alpha=0.8,
            label="Transição observada em 2019"
        )

        plt.title(
            "Evolução dos Valores Nulos no Campo Inutilizado"
        )

        plt.xlabel(
            "Ano"
        )

        plt.ylabel(
            "Registros com inutilizado nulo (%)"
        )

        plt.xticks(
            diagnostico_plot["Ano"]
            .astype(int)
        )

        plt.ylim(
            bottom=0
        )

        plt.legend()

        salvar_figura(
            "grafico_04_qualidade_inutilizado.png"
        )

# ==========================================
# GRÁFICO 05
# GRUPOS DE PARES POR PORTE
# ==========================================
# Os clusters foram formados somente com
# log_total_selos. A taxa de cancelamento aparece
# no eixo vertical apenas para interpretação.

tamanho_amostra = min(
    15000,
    len(df)
)

amostra_clusters = df.sample(
    n=tamanho_amostra,
    random_state=42
).copy()

limite_visual_scatter = (
    df["taxa_cancelamento_pct"]
    .quantile(0.995)
)

if limite_visual_scatter <= 0:
    limite_visual_scatter = (
        df["taxa_cancelamento_pct"]
        .max()
    )

plt.figure(
    figsize=(11, 7)
)

for cluster in sorted(
    amostra_clusters["cluster_par"].unique()
):

    dados_cluster = amostra_clusters[
        amostra_clusters["cluster_par"]
        == cluster
    ]

    plt.scatter(
        dados_cluster["log_total_selos"],
        dados_cluster[
            "taxa_cancelamento_pct"
        ].clip(
            upper=limite_visual_scatter
        ),
        s=15,
        alpha=0.45,
        color=cores_clusters[cluster],
        label=(
            f"Cluster {cluster} – "
            f"{nomes_clusters[cluster]}"
        )
    )

plt.title("Faixas de Porte Operacional")

plt.xlabel(
    "Volume de selos em escala logarítmica"
)

plt.ylabel(
    "Taxa de cancelamento (%)"
)

plt.legend(
    frameon=True,
    fontsize=9
)

plt.grid(
    alpha=0.25
)

salvar_figura(
    "grafico_05_clusters.png"
)

# ==========================================
# GRÁFICO 06
# QUANTIDADE DE OBSERVAÇÕES POR CLUSTER
# ==========================================
cluster_count = (
    df["cluster_par"]
    .value_counts()
    .sort_index()
)

plt.figure(
    figsize=(9, 6)
)

barras = plt.bar(
    cluster_count.index.astype(str),
    cluster_count.values,
    color=[
        cores_clusters[int(cluster)]
        for cluster in cluster_count.index
    ]
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

for barra, valor in zip(
    barras,
    cluster_count.values
):
    plt.text(
        barra.get_x()
        + barra.get_width() / 2,
        barra.get_height(),
        f"{valor:,}".replace(",", "."),
        ha="center",
        va="bottom",
        fontsize=9
    )

salvar_figura(
    "grafico_06_qtd_clusters.png"
)

# ==========================================
# GRÁFICO 07
# EVOLUÇÃO TEMPORAL DO CONSUMO DE SELOS
# ==========================================
serie = (
    df
    .groupby("mes")["total_selos"]
    .sum()
    .sort_index()
)

plt.figure(
    figsize=(14, 6)
)

plt.plot(
    serie.index,
    serie.values,
    color="#4C78A8",
    linewidth=2
)

plt.title(
    "Evolução Temporal do Consumo de Selos"
)

plt.xlabel(
    "Período"
)

plt.ylabel(
    "Total mensal de selos"
)

plt.grid(
    alpha=0.25
)

salvar_figura(
    "grafico_07_serie_historica.png"
)

# ==========================================
# GRÁFICO 08
# DISTRIBUIÇÃO DOS ALERTAS
# ==========================================
if alertas is not None:

    ordem_status = [
        "RISCO CRÍTICO",
        "ALERTA MODERADO",
        "ALERTA MULTIVARIADO"
    ]

    quantidade_status = (
        alertas["status_metodologico"]
        .value_counts()
        .reindex(
            ordem_status,
            fill_value=0
        )
    )

    plt.figure(
        figsize=(9, 6)
    )

    barras = plt.bar(
        quantidade_status.index,
        quantidade_status.values,
        color=[
            cores_status[status]
            for status in quantidade_status.index
        ]
    )

    plt.title(
        "Distribuição dos Alertas por Nível de Criticidade"
    )

    plt.xlabel(
        "Classificação"
    )

    plt.ylabel(
        "Quantidade de alertas"
    )

    plt.xticks(
        rotation=10
    )

    for barra, valor in zip(
        barras,
        quantidade_status.values
    ):
        plt.text(
            barra.get_x()
            + barra.get_width() / 2,
            barra.get_height(),
            str(valor),
            ha="center",
            va="bottom"
        )

    salvar_figura(
        "grafico_08_alertas.png"
    )

# ==========================================
# GRÁFICO 09
# TOP 20 CASOS PRIORITÁRIOS
# ==========================================
if alertas is not None:

    top20 = (
        alertas
        .nlargest(
            20,
            "score_prioridade"
        )
        .sort_values(
            "score_prioridade",
            ascending=True
        )
        .copy()
    )

    top20["caso"] = (
        "Serventia "
        + top20["cartorio_id"].astype(str)
        + " | "
        + top20["mes"].dt.strftime("%m/%Y")
    )

    cores_top20 = [
        cores_status.get(
            status,
            "#777777"
        )
        for status in top20[
            "status_metodologico"
        ]
    ]

    plt.figure(
        figsize=(12, 9)
    )

    plt.barh(
        top20["caso"],
        top20["score_prioridade"],
        color=cores_top20
    )

    plt.title(
        "Top 20 Casos Prioritários"
    )

    plt.xlabel(
        "Score de prioridade"
    )

    plt.ylabel(
        "Serventia e competência"
    )

    salvar_figura(
        "grafico_09_top20_alertas.png"
    )

# ==========================================
# GRÁFICO 10
# ALERTAS POR CLUSTER
# ==========================================
if alertas is not None:

    alertas_cluster = pd.crosstab(
        alertas["cluster_par"],
        alertas["status_metodologico"]
    )

    alertas_cluster = (
        alertas_cluster
        .reindex(
            columns=[
                "RISCO CRÍTICO",
                "ALERTA MODERADO",
                "ALERTA MULTIVARIADO"
            ],
            fill_value=0
        )
        .sort_index()
    )

    plt.figure(
        figsize=(10, 6)
    )

    alertas_cluster.plot(
        kind="bar",
        stacked=True,
        color=[
            cores_status["RISCO CRÍTICO"],
            cores_status["ALERTA MODERADO"],
            cores_status["ALERTA MULTIVARIADO"]
        ],
        figsize=(10, 6)
    )

    plt.title(
        "Distribuição dos Alertas por Grupo de Porte"
    )

    plt.xlabel(
        "Cluster"
    )

    plt.ylabel(
        "Quantidade de alertas"
    )

    plt.xticks(
        rotation=0
    )

    plt.legend(
        title="Classificação"
    )

    salvar_figura(
        "grafico_10_alertas_por_cluster.png"
    )

# ==========================================
# GRÁFICO 11
# EVOLUÇÃO TEMPORAL DOS ALERTAS
# ==========================================
if alertas is not None:

    alertas_ano = (
        alertas
        .assign(
            Ano=alertas["mes"].dt.year
        )
        .groupby(
            [
                "Ano",
                "status_metodologico"
            ]
        )
        .size()
        .reset_index(
            name="Quantidade"
        )
    )

    plt.figure(
        figsize=(12, 6)
    )

    sns.lineplot(
        data=alertas_ano,
        x="Ano",
        y="Quantidade",
        hue="status_metodologico",
        hue_order=[
            "RISCO CRÍTICO",
            "ALERTA MODERADO",
            "ALERTA MULTIVARIADO"
        ],
        palette=cores_status,
        marker="o",
        linewidth=2
    )

    plt.title(
        "Evolução Anual dos Alertas"
    )

    plt.xlabel(
        "Ano"
    )

    plt.ylabel(
        "Quantidade de alertas"
    )

    plt.xticks(
        sorted(
            alertas_ano["Ano"].unique()
        )
    )

    plt.legend(
        title="Classificação"
    )

    salvar_figura(
        "grafico_11_alertas_por_ano.png"
    )

# ==========================================
# GRÁFICO 12
# MÉTODO DO COTOVELO
# ==========================================
if tabela_k is not None:

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        tabela_k["k"],
        tabela_k["inercia"],
        marker="o",
        color="#4C78A8"
    )

    plt.axvline(
        x=4,
        color="#C62828",
        linestyle="--",
        label="k escolhido = 4"
    )

    plt.title(
        "Método do Cotovelo"
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

    salvar_figura(
        "grafico_12_metodo_cotovelo.png"
    )

# ==========================================
# GRÁFICO 13
# COEFICIENTE SILHOUETTE
# ==========================================
if tabela_k is not None:

    plt.figure(
        figsize=(8, 5)
    )

    plt.plot(
        tabela_k["k"],
        tabela_k["silhouette"],
        marker="o",
        color="#54A24B"
    )

    plt.axvline(
        x=4,
        color="#C62828",
        linestyle="--",
        label="k escolhido = 4"
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

    salvar_figura(
        "grafico_13_silhouette.png"
    )

print("\n" + "=" * 70)
print("GRÁFICOS GERADOS COM SUCESSO")
print("=" * 70)

print(
    "\nNão utilize mais o arquivo antigo "
    "'grafico_04_hist_sem_guia.png'."
)