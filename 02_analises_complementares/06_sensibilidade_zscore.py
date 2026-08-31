import pandas as pd
import numpy as np

# ==========================================
# 1. CARREGAMENTO DA BASE
# ==========================================

ARQUIVO = "dados_com_clusters.csv"

df = pd.read_csv(ARQUIVO)

print(f"Registros carregados: {len(df):,}")
print()

# ==========================================
# 2. VALIDAÇÃO DAS COLUNAS
# ==========================================

colunas_obrigatorias = [
    "cartorio_id",
    "mes",
    "cluster_par",
    "taxa_cancelamento",
]

faltantes = [
    c for c in colunas_obrigatorias
    if c not in df.columns
]

if faltantes:
    raise ValueError(
        f"Colunas ausentes no arquivo: {faltantes}"
    )

df["taxa_cancelamento"] = pd.to_numeric(
    df["taxa_cancelamento"],
    errors="coerce"
)

if df["taxa_cancelamento"].isna().any():
    raise ValueError(
        "Existem valores nulos ou inválidos em taxa_cancelamento."
    )

# ==========================================
# 3. MEDIANA E MAD POR CLUSTER
# ==========================================

resultados = []

for cluster, grupo in df.groupby("cluster_par"):

    valores = grupo["taxa_cancelamento"]

    mediana = valores.median()

    mad = np.median(
        np.abs(valores - mediana)
    )

    resultados.append({
        "cluster_par": cluster,
        "observacoes": len(grupo),
        "mediana_taxa": mediana,
        "mad": mad,
        "taxa_minima": valores.min(),
        "taxa_maxima": valores.max(),
        "percentual_zero": (
            (valores == 0).mean() * 100
        )
    })

resultado = pd.DataFrame(resultados)

print("DIAGNÓSTICO PARA Z-SCORE ROBUSTO")
print("=" * 70)
print(resultado.to_string(index=False))
print()

# ==========================================
# 4. VERIFICAÇÃO DO MAD
# ==========================================

clusters_mad_zero = resultado[
    resultado["mad"] == 0
]

if len(clusters_mad_zero) > 0:

    print("ATENÇÃO:")
    print(
        "Foram encontrados clusters com MAD igual a zero."
    )
    print(
        "Nesses grupos, o Z-Score robusto baseado em "
        "mediana/MAD não pode ser calculado diretamente."
    )
    print()

    print(
        clusters_mad_zero[
            [
                "cluster_par",
                "observacoes",
                "mediana_taxa",
                "mad",
                "percentual_zero"
            ]
        ].to_string(index=False)
    )

else:

    print(
        "Todos os clusters possuem MAD maior que zero."
    )
    print(
        "É possível prosseguir com o cálculo do "
        "Z-Score robusto."
    )

# ==========================================
# 5. SALVAR RESULTADO
# ==========================================

resultado.to_csv(
    "diagnostico_zscore_robusto.csv",
    index=False
)

print()
print(
    "Arquivo gerado: diagnostico_zscore_robusto.csv"
)

import pandas as pd

# ==========================================
# 1. CARREGAMENTO DA BASE
# ==========================================

ARQUIVO = "dados_com_clusters.csv"

df = pd.read_csv(ARQUIVO)

print(f"Registros carregados: {len(df):,}")
print()

# ==========================================
# 2. VALIDAÇÃO DAS COLUNAS
# ==========================================

colunas_obrigatorias = [
    "cartorio_id",
    "mes",
    "cluster_par",
    "taxa_cancelamento",
]

faltantes = [
    c for c in colunas_obrigatorias
    if c not in df.columns
]

if faltantes:
    raise ValueError(
        f"Colunas ausentes no arquivo: {faltantes}"
    )

df["taxa_cancelamento"] = pd.to_numeric(
    df["taxa_cancelamento"],
    errors="coerce"
)

if df["taxa_cancelamento"].isna().any():
    raise ValueError(
        "Existem valores nulos ou inválidos em taxa_cancelamento."
    )

# ==========================================
# 3. Z-SCORE CONVENCIONAL POR CLUSTER
# ==========================================

media_cluster = df.groupby("cluster_par")[
    "taxa_cancelamento"
].transform("mean")

desvio_cluster = df.groupby("cluster_par")[
    "taxa_cancelamento"
].transform(
    lambda x: x.std(ddof=0)
)

df["z_score_convencional"] = (
    df["taxa_cancelamento"] - media_cluster
) / desvio_cluster

df["alerta_z"] = (
    df["z_score_convencional"] > 2
)

# ==========================================
# 4. PERCENTIS POR CLUSTER
# ==========================================

percentis = [
    0.95,
    0.975,
    0.99
]

resultados = []

for cluster, grupo in df.groupby("cluster_par"):

    for p in percentis:

        limite = grupo[
            "taxa_cancelamento"
        ].quantile(p)

        alerta_percentil = (
            grupo["taxa_cancelamento"] > limite
        )

        alerta_z = grupo["alerta_z"]

        qtd_z = alerta_z.sum()

        qtd_percentil = (
            alerta_percentil.sum()
        )

        intersecao = (
            alerta_percentil
            & alerta_z
        ).sum()

        percentual_sobreposicao = (
            100 * intersecao / qtd_z
            if qtd_z > 0
            else 0
        )

        resultados.append({
            "cluster_par": cluster,
            "percentil": p,
            "limite_taxa": limite,
            "alertas_z_maior_2": qtd_z,
            "alertas_percentil": qtd_percentil,
            "alertas_em_comum": intersecao,
            "perc_alertas_z_mantidos":
                percentual_sobreposicao
        })

resultado = pd.DataFrame(resultados)

# ==========================================
# 5. RESULTADOS POR CLUSTER
# ==========================================

print(
    "ANÁLISE DE SENSIBILIDADE - "
    "Z-SCORE x PERCENTIS"
)

print("=" * 90)

print(
    resultado.to_string(
        index=False
    )
)

# ==========================================
# 6. RESUMO GLOBAL
# ==========================================

print()
print("=" * 90)
print("RESUMO GLOBAL")
print("=" * 90)

total_z = df["alerta_z"].sum()

print(
    f"Alertas pelo Z-Score > 2: "
    f"{total_z:,}"
)

print()

for p in percentis:

    limites = df.groupby(
        "cluster_par"
    )["taxa_cancelamento"].transform(
        lambda x: x.quantile(p)
    )

    alerta_percentil = (
        df["taxa_cancelamento"] > limites
    )

    total_percentil = (
        alerta_percentil.sum()
    )

    intersecao = (
        alerta_percentil
        & df["alerta_z"]
    ).sum()

    percentual_z_mantido = (
        100 * intersecao / total_z
        if total_z > 0
        else 0
    )

    print(
        f"Percentil {p * 100:.1f}:"
    )

    print(
        f"  Alertas pelo percentil: "
        f"{total_percentil:,}"
    )

    print(
        f"  Em comum com Z > 2: "
        f"{intersecao:,}"
    )

    print(
        f"  Percentual dos alertas Z mantidos: "
        f"{percentual_z_mantido:.2f}%"
    )

    print()

# ==========================================
# 7. SALVAR RESULTADO
# ==========================================

resultado.to_csv(
    "sensibilidade_zscore_percentis.csv",
    index=False
)

print(
    "Arquivo gerado: "
    "sensibilidade_zscore_percentis.csv"
)