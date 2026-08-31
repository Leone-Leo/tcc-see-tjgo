import os
import pandas as pd
from sqlalchemy import create_engine

# ==========================================
# 1. CONEXÃO
# ==========================================
url_banco = os.getenv("SEE_DATABASE_URL")
if not url_banco:
    raise RuntimeError("Defina a variável de ambiente SEE_DATABASE_URL antes de executar a extração.")

motor = create_engine(
    url_banco,
    pool_pre_ping=True
)

# ==========================================
# 2. EXTRAÇÃO
# Unidade: Serventia × Mês
# ==========================================
query = """
SELECT
    f.cartorio_id,
    DATE_TRUNC('month', f.data_hora_utilizacao) AS mes,

    COUNT(*) AS total_selos,

    SUM(
        CASE
            WHEN f.inutilizado IS TRUE
            THEN 1
            ELSE 0
        END
    ) AS total_cancelados,

    SUM(
        CASE
            WHEN f.inutilizado IS FALSE
            THEN 1
            ELSE 0
        END
    ) AS total_nao_cancelados_explicitos,

    SUM(
        CASE
            WHEN f.inutilizado IS NULL
            THEN 1
            ELSE 0
        END
    ) AS total_inutilizado_nulo

FROM public.controle_de_atos_utilizados f

GROUP BY
    f.cartorio_id,
    DATE_TRUNC('month', f.data_hora_utilizacao)

ORDER BY
    f.cartorio_id,
    DATE_TRUNC('month', f.data_hora_utilizacao);
"""

print("Extraindo dados...")

try:
    df = pd.read_sql(
        query,
        motor
    )
finally:
    motor.dispose()

print("Extração concluída.")

# ==========================================
# 3. BACKUP DA BASE ORIGINAL
# ==========================================
df_original = df.copy()

df_original.to_csv(
    "dados_brutos_original.csv",
    index=False
)

print("Base original salva.")

# ==========================================
# 4. TRATAMENTO DAS DATAS
# ==========================================
df["mes"] = pd.to_datetime(
    df["mes"],
    errors="coerce"
)

df_original["mes"] = pd.to_datetime(
    df_original["mes"],
    errors="coerce"
)

total_inicial = len(df)

# ------------------------------------------
# Observações com data inválida
# ------------------------------------------
datas_invalidas = df[
    df["mes"].isna()
].copy()

df = df.dropna(
    subset=["mes"]
).copy()

# ------------------------------------------
# Período oficial do TCC
# Janeiro/2016 a julho/2025
# ------------------------------------------
data_inicio = pd.Timestamp(
    "2016-01-01"
)

data_fim = pd.Timestamp(
    "2025-07-01"
)

antes_periodo = df[
    df["mes"] < data_inicio
].copy()

apos_periodo = df[
    df["mes"] > data_fim
].copy()

# ------------------------------------------
# Aplicação do recorte temporal
# ------------------------------------------
df = df[
    (df["mes"] >= data_inicio)
    & (df["mes"] <= data_fim)
].copy()

df = df.sort_values(
    [
        "cartorio_id",
        "mes"
    ]
).reset_index(drop=True)

total_final = len(df)
removidos = total_inicial - total_final

# ==========================================
# 5. BASE DAS OBSERVAÇÕES REMOVIDAS
# ==========================================
removidos_df = pd.concat(
    [
        datas_invalidas,
        antes_periodo,
        apos_periodo
    ],
    ignore_index=True
)

removidos_df.to_csv(
    "registros_removidos.csv",
    index=False
)

# ==========================================
# 6. RELATÓRIO DE QUALIDADE
# ==========================================
duplicados_chave = df.duplicated(
    subset=[
        "cartorio_id",
        "mes"
    ]
).sum()

print("\n==============================")
print("RELATÓRIO DE QUALIDADE")
print("==============================")

print(
    f"Observações extraídas : {total_inicial}"
)

print(
    f"Observações finais    : {total_final}"
)

print(
    f"Observações removidas : {removidos}"
)

print("\nMotivos da remoção")

print(
    f"Datas inválidas       : {len(datas_invalidas)}"
)

print(
    f"Antes de 2016         : {len(antes_periodo)}"
)

print(
    f"Após julho de 2025    : {len(apos_periodo)}"
)

print("\nValores nulos na base agregada")

print(
    df.isnull().sum()
)

print("\nDuplicidades na chave Serventia × Mês")

print(
    duplicados_chave
)

print("\nPeríodo utilizado")

print(
    "Início:",
    df["mes"].min()
)

print(
    "Fim   :",
    df["mes"].max()
)

print("\nQualidade do campo inutilizado")

print(
    "Registros transacionais com inutilizado nulo:",
    int(
        df["total_inutilizado_nulo"].sum()
    )
)

print(
    "Registros explicitamente não inutilizados:",
    int(
        df[
            "total_nao_cancelados_explicitos"
        ].sum()
    )
)

print(
    "Registros inutilizados/cancelados:",
    int(
        df["total_cancelados"].sum()
    )
)

# ==========================================
# 7. TABELA DE MOTIVOS DA REMOÇÃO
# ==========================================
tabela_motivos = pd.DataFrame(
    {
        "Motivo": [
            "Datas inválidas",
            "Antes de 2016",
            "Após julho de 2025"
        ],
        "Quantidade": [
            len(datas_invalidas),
            len(antes_periodo),
            len(apos_periodo)
        ]
    }
)

tabela_motivos.to_csv(
    "Tabela_Motivos_Remocao.csv",
    index=False
)

# ==========================================
# 8. TABELA ANTES × DEPOIS POR ANO
# ==========================================
base_antes = (
    df_original
    .dropna(
        subset=["mes"]
    )
    .assign(
        Ano=lambda x: x["mes"].dt.year
    )
)

antes = (
    base_antes
    .groupby("Ano")
    .size()
    .reset_index(
        name="Antes"
    )
)

depois = (
    df
    .assign(
        Ano=lambda x: x["mes"].dt.year
    )
    .groupby("Ano")
    .size()
    .reset_index(
        name="Depois"
    )
)

tabela_ano = antes.merge(
    depois,
    on="Ano",
    how="left"
)

tabela_ano["Depois"] = (
    tabela_ano["Depois"]
    .fillna(0)
    .astype(int)
)

tabela_ano["Removidos"] = (
    tabela_ano["Antes"]
    - tabela_ano["Depois"]
)

tabela_ano["Percentual_Removido"] = (
    tabela_ano["Removidos"]
    .div(
        tabela_ano["Antes"]
    )
    .mul(100)
    .round(2)
)

tabela_ano.to_csv(
    "Tabela_Saneamento_Por_Ano.csv",
    index=False
)

# ==========================================
# 9. DIAGNÓSTICO DO CAMPO INUTILIZADO
# Arquivo de auditoria, não entra no modelo
# ==========================================
diagnostico_inutilizado = (
    df
    .assign(
        Ano=lambda x: x["mes"].dt.year
    )
    .groupby(
        "Ano",
        as_index=False
    )
    .agg(
        total_registros_transacionais=(
            "total_selos",
            "sum"
        ),
        total_cancelados=(
            "total_cancelados",
            "sum"
        ),
        total_nao_cancelados_explicitos=(
            "total_nao_cancelados_explicitos",
            "sum"
        ),
        total_inutilizado_nulo=(
            "total_inutilizado_nulo",
            "sum"
        )
    )
)

diagnostico_inutilizado[
    "percentual_inutilizado_nulo"
] = (
    diagnostico_inutilizado[
        "total_inutilizado_nulo"
    ]
    .div(
        diagnostico_inutilizado[
            "total_registros_transacionais"
        ]
    )
    .mul(100)
    .round(2)
)

diagnostico_inutilizado.to_csv(
    "Diagnostico_Inutilizado_Por_Ano.csv",
    index=False
)

# ==========================================
# 10. SALVAR BASE LIMPA
# ==========================================
df.to_csv(
    "dados_brutos.csv",
    index=False
)

print("\nBase limpa salva.")

print("\nArquivos gerados:")

print(
    "✔ dados_brutos_original.csv"
)

print(
    "✔ dados_brutos.csv"
)

print(
    "✔ registros_removidos.csv"
)

print(
    "✔ Tabela_Motivos_Remocao.csv"
)

print(
    "✔ Tabela_Saneamento_Por_Ano.csv"
)

print(
    "✔ Diagnostico_Inutilizado_Por_Ano.csv"
)