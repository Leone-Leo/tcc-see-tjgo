import pandas as pd

print("="*60)
print("ANÁLISES COMPLEMENTARES DO TCC")
print("="*60)

# =====================================================
# LEITURA DAS BASES
# =====================================================

df_original = pd.read_csv("dados_brutos_original.csv")
df_limpo = pd.read_csv("dados_brutos.csv")

df_original["mes"] = pd.to_datetime(df_original["mes"], errors="coerce")
df_limpo["mes"] = pd.to_datetime(df_limpo["mes"], errors="coerce")

# =====================================================
# TABELA 1
# DISTRIBUIÇÃO TEMPORAL
# =====================================================

antes = (
    df_original
    .groupby(df_original["mes"].dt.year)
    .size()
    .reset_index(name="Antes")
)

depois = (
    df_limpo
    .groupby(df_limpo["mes"].dt.year)
    .size()
    .reset_index(name="Depois")
)

tabela_ano = antes.merge(
    depois,
    on="mes",
    how="outer"
).fillna(0)

tabela_ano.rename(columns={"mes":"Ano"}, inplace=True)

tabela_ano["Removidos"] = (
    tabela_ano["Antes"]
    -
    tabela_ano["Depois"]
)

tabela_ano["% Removido"] = (
    tabela_ano["Removidos"]
    /
    tabela_ano["Antes"]
    *100
).round(2)

print("\nTabela 1")
print(tabela_ano)

tabela_ano.to_csv(
    "Tabela01_Saneamento_Por_Ano.csv",
    index=False
)

# =====================================================
# TABELA 2
# POR CARTÓRIO
# =====================================================

antes = (
    df_original
    .groupby("cartorio_id")
    .size()
    .reset_index(name="Antes")
)

depois = (
    df_limpo
    .groupby("cartorio_id")
    .size()
    .reset_index(name="Depois")
)

tabela_cartorio = antes.merge(
    depois,
    on="cartorio_id",
    how="outer"
).fillna(0)

tabela_cartorio["Removidos"] = (
    tabela_cartorio["Antes"]
    -
    tabela_cartorio["Depois"]
)

tabela_cartorio["% Removido"] = (
    tabela_cartorio["Removidos"]
    /
    tabela_cartorio["Antes"]
    *100
).round(2)

tabela_cartorio = tabela_cartorio.sort_values(
    "Removidos",
    ascending=False
)

print("\nTabela 2")
print(tabela_cartorio.head(20))

tabela_cartorio.to_csv(
    "Tabela02_Remocao_Por_Cartorio.csv",
    index=False
)

# =====================================================
# TABELA 3
# MOTIVOS DA REMOÇÃO
# =====================================================

motivos = {
    "Datas inválidas":
        df_original["mes"].isna().sum(),

    "Antes de 2016":
        (df_original["mes"] < "2016-01-01").sum(),

    "Após Julho/2025":
        (df_original["mes"] > "2025-07-01").sum()
}

tabela_motivos = pd.DataFrame(
    motivos.items(),
    columns=[
        "Motivo",
        "Quantidade"
    ]
)

print("\nTabela 3")
print(tabela_motivos)

tabela_motivos.to_csv(
    "Tabela03_Motivos_Remocao.csv",
    index=False
)

# =====================================================
# TABELA 4
# ESTATÍSTICAS GERAIS
# =====================================================

estatisticas = pd.DataFrame({

    "Indicador":[

        "Registros Originais",

        "Registros Após Limpeza",

        "Removidos",

        "% Removido"

    ],

    "Valor":[

        len(df_original),

        len(df_limpo),

        len(df_original)-len(df_limpo),

        round(
            (
                (len(df_original)-len(df_limpo))
                /
                len(df_original)
            )*100,
            2
        )

    ]

})

print("\nTabela 4")
print(estatisticas)

estatisticas.to_csv(
    "Tabela04_Estatisticas_Gerais.csv",
    index=False
)

# =====================================================
# TABELA 5
# PERÍODO DA BASE
# =====================================================

periodo = pd.DataFrame({

    "Descrição":[

        "Data mínima",

        "Data máxima"

    ],

    "Valor":[

        df_limpo["mes"].min(),

        df_limpo["mes"].max()

    ]

})

periodo.to_csv(
    "Tabela05_Periodo_Base.csv",
    index=False
)

print("\nTabela 5")
print(periodo)

print("\nArquivos gerados com sucesso.")
# =====================================================
# =====================================================
# TABELA 6
# ANÁLISE DA DISTRIBUIÇÃO DA REMOÇÃO POR SERVENTIA
# =====================================================

# Apenas serventias presentes na base final
tabela_cartorio_modelo = tabela_cartorio[
    tabela_cartorio["Depois"] > 0
].copy()

# Quantidade de serventias
total_original = df_original["cartorio_id"].nunique()
total_final = df_limpo["cartorio_id"].nunique()
total_removidas = total_original - total_final

# Estatísticas apenas das serventias utilizadas no modelo
estatisticas_remocao = pd.DataFrame({

    "Estatística":[
        "Serventias na base original",
        "Serventias na base analítica",
        "Serventias excluídas integralmente",
        "Média (%) de registros removidos",
        "Mediana (%)",
        "Desvio padrão (%)",
        "Mínimo (%)",
        "Máximo (%)"
    ],

    "Valor":[

        total_original,

        total_final,

        total_removidas,

        round(
            tabela_cartorio_modelo["% Removido"].mean(),
            2
        ),

        round(
            tabela_cartorio_modelo["% Removido"].median(),
            2
        ),

        round(
            tabela_cartorio_modelo["% Removido"].std(),
            2
        ),

        round(
            tabela_cartorio_modelo["% Removido"].min(),
            2
        ),

        round(
            tabela_cartorio_modelo["% Removido"].max(),
            2
        )

    ]

})

print("\nTabela 6")
print(estatisticas_remocao)

estatisticas_remocao.to_csv(
    "Tabela06_Estatisticas_Remocao_Serventias.csv",
    index=False
)

print("\n==============================================")
print("RESUMO DAS SERVENTIAS")
print("==============================================")

print(f"Serventias na base original : {total_original}")
print(f"Serventias na base analítica: {total_final}")
print(f"Serventias excluídas        : {total_removidas}")

print("\nResumo estatístico da remoção (%):")
print(tabela_cartorio_modelo["% Removido"].describe())



# =====================================================
# TABELA 7
# SERVENTIAS EXCLUÍDAS INTEGRALMENTE
# =====================================================

serventias_excluidas = tabela_cartorio[
    tabela_cartorio["Depois"] == 0
].copy()

print("\nTabela 7 - Serventias excluídas")
print(serventias_excluidas)

serventias_excluidas.to_csv(
    "Tabela07_Serventias_Excluidas.csv",
    index=False
)

# registros apenas das serventias excluídas

ids = serventias_excluidas["cartorio_id"]

base = df_original[
    df_original["cartorio_id"].isin(ids)
].copy()

base["ano"] = base["mes"].dt.year

tabela = (
    base
    .groupby(["cartorio_id","ano"])
    .size()
    .reset_index(name="Registros")
)

print(tabela)

tabela.to_csv(
    "Tabela08_Anos_Serventias_Excluidas.csv",
    index=False
)
# =====================================================
# TABELA 9
# CARACTERIZAÇÃO DOS CLUSTERS
# =====================================================

df_clusters = pd.read_csv("dados_com_clusters.csv")

tabela_clusters = (
    df_clusters
    .groupby("cluster_par")
    .agg(
        Registros=("cluster_par", "size"),
        Serventias=("cartorio_id", "nunique"),
        Media_Selos=("total_selos", "mean"),
        Media_Cancelamento=("taxa_cancelamento", "mean"),
        Media_Sem_Guia=("perc_sem_guia", "mean")
    )
    .reset_index()
)

# Percentual da base
tabela_clusters["Percentual_Base"] = (
    tabela_clusters["Registros"]
    /
    tabela_clusters["Registros"].sum()
    * 100
).round(2)

# Caracterização automática do perfil
def definir_perfil(linha):

    if linha["Media_Cancelamento"] >= 0.30:
        return "Alta taxa de cancelamento"

    elif linha["Media_Selos"] >= 30000:
        return "Alto volume operacional"

    elif linha["Media_Sem_Guia"] >= 0.90:
        return "Alta incidência de selos sem guia"

    else:
        return "Baixa incidência de selos sem guia"

tabela_clusters["Perfil"] = tabela_clusters.apply(
    definir_perfil,
    axis=1
)

# Conversão para percentual
tabela_clusters["Media_Cancelamento"] = (
    tabela_clusters["Media_Cancelamento"] * 100
).round(2)

tabela_clusters["Media_Sem_Guia"] = (
    tabela_clusters["Media_Sem_Guia"] * 100
).round(2)

tabela_clusters["Media_Selos"] = (
    tabela_clusters["Media_Selos"]
).round(0).astype(int)

# Organização das colunas
tabela_clusters = tabela_clusters[
    [
        "cluster_par",
        "Registros",
        "Percentual_Base",
        "Serventias",
        "Media_Selos",
        "Media_Cancelamento",
        "Media_Sem_Guia",
        "Perfil"
    ]
]

# Renomeia para apresentação
tabela_clusters.columns = [
    "Cluster",
    "Registros",
    "% da Base",
    "Serventias",
    "Média de Selos",
    "Média Cancelamento (%)",
    "Média Selos sem Guia (%)",
    "Perfil Operacional"
]

print("\nTabela 9 - Caracterização dos Clusters")
print(tabela_clusters)

tabela_clusters.to_csv(
    "Tabela09_Caracterizacao_Clusters.csv",
    index=False
)

print("\nTabela 9 salva com sucesso.")

# =====================================================
# =====================================================
# LEITURA DA BASE DE ALERTAS
# =====================================================

alertas = pd.read_csv(
    "tabela_alertas_final.csv"
)

df_clusters = pd.read_csv(
    "dados_com_clusters.csv"
)


# =====================================================
# TABELA 10
# DISTRIBUIÇÃO DOS MOTIVOS DETALHADOS
# =====================================================

tabela10 = (
    alertas
    .groupby("categoria_motivo")
    .size()
    .reset_index(name="Quantidade")
)

tabela10["Percentual (%)"] = (
    tabela10["Quantidade"]
    /
    len(alertas)
    * 100
).round(2)

tabela10 = tabela10.sort_values(
    "Quantidade",
    ascending=False
).reset_index(drop=True)

tabela10 = tabela10.rename(
    columns={
        "categoria_motivo": "Motivo do Alerta"
    }
)

print("\nTabela 10 - Motivos Detalhados dos Alertas")
print(tabela10.to_string(index=False))

tabela10.to_csv(
    "Tabela10_Motivos_Detalhados_Alertas.csv",
    index=False
)


# =====================================================
# TABELA 11
# DISTRIBUIÇÃO DOS ALERTAS POR CLUSTER
# =====================================================

alertas_por_cluster = (
    alertas
    .groupby("cluster_par")
    .size()
    .reset_index(name="Alertas")
)

registros_por_cluster = (
    df_clusters
    .groupby("cluster_par")
    .size()
    .reset_index(name="Registros do Cluster")
)

tabela11 = alertas_por_cluster.merge(
    registros_por_cluster,
    on="cluster_par",
    how="left"
)

tabela11["% dos Alertas"] = (
    tabela11["Alertas"]
    /
    len(alertas)
    * 100
).round(2)

tabela11["Taxa de Alertas no Cluster (%)"] = (
    tabela11["Alertas"]
    /
    tabela11["Registros do Cluster"]
    * 100
).round(2)

tabela11 = tabela11.rename(
    columns={
        "cluster_par": "Cluster"
    }
)

tabela11 = tabela11[
    [
        "Cluster",
        "Alertas",
        "Registros do Cluster",
        "% dos Alertas",
        "Taxa de Alertas no Cluster (%)"
    ]
]

print("\nTabela 11 - Distribuição dos Alertas por Cluster")
print(tabela11.to_string(index=False))

tabela11.to_csv(
    "Tabela11_Distribuicao_Alertas_Cluster.csv",
    index=False
)


# =====================================================
# TABELA 12
# TOP 20 CASOS PRIORITÁRIOS
# =====================================================

tabela12 = (
    alertas
    .sort_values(
        "score_prioridade",
        ascending=False
    )
    .head(20)
    .copy()
)

tabela12["mes"] = pd.to_datetime(
    tabela12["mes"],
    errors="coerce"
).dt.strftime("%m/%Y")

tabela12["z_score_par"] = (
    tabela12["z_score_par"]
    .round(2)
)

tabela12["score_prioridade"] = (
    tabela12["score_prioridade"]
    .round(2)
)

tabela12 = tabela12[
    [
        "posicao_ranking",
        "cartorio_id",
        "mes",
        "cluster_par",
        "z_score_par",
        "score_prioridade",
        "status_metodologico",
        "categoria_motivo",
        "justificativa_alerta"
    ]
]

tabela12 = tabela12.rename(
    columns={
        "posicao_ranking": "Posição",
        "cartorio_id": "Serventia",
        "mes": "Mês",
        "cluster_par": "Cluster",
        "z_score_par": "Z-Score",
        "score_prioridade": "Score de Prioridade",
        "status_metodologico": "Status",
        "categoria_motivo": "Motivo",
        "justificativa_alerta": "Justificativa"
    }
)

print("\nTabela 12 - Top 20 Casos Prioritários")
print(tabela12.to_string(index=False))

tabela12.to_csv(
    "Tabela12_Top20_Casos_Prioritarios.csv",
    index=False
)

print("\nTabelas 10, 11 e 12 geradas com sucesso.")