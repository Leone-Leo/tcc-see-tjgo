# TCC — Modelagem Analítica e Aprendizado de Máquina no SEE/TJGO

Prova de Conceito para **triagem de ocorrências potencialmente atípicas** no Sistema Extrajudicial Eletrônico do Tribunal de Justiça do Estado de Goiás — SEE/TJGO.

O projeto aplica técnicas de análise estatística, agrupamento e aprendizado de máquina para reduzir o universo de registros que merece revisão humana, preservando o contexto operacional de cada serventia.

> **Importante:** o projeto identifica padrões estatisticamente atípicos. Ele não detecta fraude, não comprova irregularidade e não substitui a análise técnica ou institucional.

## Objetivos

* analisar dados históricos do SEE/TJGO;
* segmentar serventias por porte operacional;
* identificar desvios relativos ao comportamento de cada grupo;
* priorizar ocorrências para revisão humana;
* produzir tabelas, gráficos e painéis gerenciais;
* manter um processo auditável, rastreável e reproduzível.

## Pergunta de pesquisa

Em que medida uma arquitetura analítica baseada em segmentação por porte, indicadores estatísticos e detecção não supervisionada pode reduzir e contextualizar o universo de ocorrências priorizadas em comparação com regras globais simples?

## Dados analisados

A unidade de análise é **Serventia × Mês**.

| Indicador                                        |                       Resultado |
| ------------------------------------------------ | ------------------------------: |
| Período analisado                                | Janeiro de 2016 a julho de 2025 |
| Meses analisados                                 |                             115 |
| Observações na extração inicial                  |                          76.862 |
| Observações removidas pelo recorte temporal      |                          19.382 |
| Base analítica final                             |                          57.480 |
| Serventias analisadas                            |                             524 |
| Serventias excluídas por falta de período válido |                              29 |

Os dados originais pertencem ao TJGO e não são publicados neste repositório por motivos de segurança, governança e autorização institucional.

## Metodologia

```mermaid
flowchart TD
    A["Extração e qualidade"] --> B["Engenharia de variáveis"]
    B --> C["Segmentação por porte"]
    C --> D["Z-Score e Isolation Forest"]
    D --> E["Alertas, tabelas e painéis"]
```

### 1. Extração e qualidade

Os dados são submetidos a verificações de:

* período;
* duplicidade;
* valores ausentes;
* consistência dos campos;
* volume de registros;
* integridade das variáveis utilizadas.

### 2. Engenharia de variáveis

| Variável            | Descrição                                              |
| ------------------- | ------------------------------------------------------ |
| `cartorio_id`       | Identificador da serventia, usado para rastreabilidade |
| `mes`               | Competência mensal da observação                       |
| `total_selos`       | Volume mensal de selos                                 |
| `total_cancelados`  | Quantidade mensal de cancelamentos                     |
| `taxa_cancelamento` | Razão entre cancelamentos e total de selos             |
| `log_total_selos`   | Transformação logarítmica do volume                    |
| `cluster_par`       | Grupo de porte operacional                             |
| `z_score_par`       | Desvio relativo dentro do grupo de porte               |
| `iforest_score`     | Resultado da detecção não supervisionada               |
| `score_prioridade`  | Ordem de prioridade para revisão                       |

### 3. Segmentação por porte

O K-Means agrupa as observações de acordo com o volume operacional.

Essa etapa evita comparar diretamente serventias com escalas muito diferentes. Uma ocorrência pode ser comum em uma serventia grande, mas atípica em uma serventia pequena.

### 4. Detecção de padrões atípicos

A arquitetura utiliza:

* **K-Means:** formação de grupos de porte operacional;
* **Z-Score:** avaliação do afastamento em relação ao comportamento do próprio grupo;
* **Isolation Forest:** identificação de combinações pouco frequentes entre volume e taxa de cancelamento.

O `score_prioridade` organiza os registros para análise posterior. Ele não representa probabilidade de irregularidade.

## Resultados principais

A arquitetura híbrida reduziu o universo priorizado de:

* **8.166 observações na baseline;**
* para **790 observações na arquitetura contextualizada;**
* correspondendo a uma redução de aproximadamente **90,3%**.

Essa redução representa **seletividade da triagem**, e não acurácia. Como o projeto não possui rótulos confirmados de irregularidade para todos os registros, não são apresentadas métricas tradicionais de classificação, como precisão, recall ou taxa de falsos positivos.

## Resultados visuais

Os gráficos estão na pasta:

```text
04_resultados/03_graficos/
```

### Segmentação por porte operacional

![Segmentação por porte operacional](04_resultados/03_graficos/grafico_05_clusters.png)

Apresenta os agrupamentos formados pelo K-Means e permite observar a separação das observações segundo o porte operacional.

### Evolução histórica

![Série histórica](04_resultados/03_graficos/grafico_07_serie_historica.png)

Mostra o comportamento dos indicadores ao longo do período analisado, ajudando a distinguir alterações pontuais de padrões persistentes.

### Distribuição das ocorrências priorizadas

![Distribuição dos alertas](04_resultados/03_graficos/grafico_08_alertas.png)

Apresenta a distribuição dos registros classificados como potencialmente atípicos pela arquitetura analítica.

### Principais ocorrências priorizadas

![Top 20 alertas](04_resultados/03_graficos/grafico_09_top20_alertas.png)

Organiza as ocorrências com maior prioridade para facilitar a revisão inicial.

### Alertas por grupo de porte

![Alertas por cluster](04_resultados/03_graficos/grafico_10_alertas_por_cluster.png)

Mostra como os registros priorizados se distribuem entre os diferentes grupos de porte operacional.

Os gráficos são resultados agregados da análise. Imagens adicionais do Power BI só devem ser publicadas quando houver autorização e quando não apresentarem informações restritas.

## Estrutura do projeto

```text
TCC_Geyson_TJGO/
├── 00_documentos/
│   ├── artigo ou monografia
│   ├── relatório técnico
│   └── apresentação
├── 01_codigo_principal/
│   ├── 01_extracao_e_qualidade.py
│   ├── 02_feature_engineering_e_clusters.py
│   ├── 03_modelagem_zscore_e_iforest.py
│   ├── 04_graficos_tcc.py
│   └── 05_tabelas.py
├── 02_analises_complementares/
│   ├── 06_sensibilidade_zscore.py
│   ├── 10_teste_contamination.py
│   ├── 11_teste_robust_zscore.py
│   └── 13_estabilidade_temporal_clusters.py
├── 03_dados/
│   ├── bases de origem
│   └── bases processadas
├── 04_resultados/
│   ├── tabelas
│   └── 03_graficos/
│       ├── grafico_01_histograma_log.png
│       ├── grafico_02_boxplot_total_selos.png
│       ├── grafico_03_hist_cancelamento.png
│       ├── grafico_04_qualidade_inutilizado.png
│       ├── grafico_05_clusters.png
│       ├── grafico_06_qtd_clusters.png
│       ├── grafico_07_serie_historica.png
│       ├── grafico_08_alertas.png
│       ├── grafico_09_top20_alertas.png
│       ├── grafico_10_alertas_por_cluster.png
│       ├── grafico_11_alertas_por_ano.png
│       ├── grafico_12_metodo_cotovelo.png
│       ├── grafico_13_silhouette.png
│       └── grafico_persistencia_temporal_clusters.png
├── 99_arquivo_exploratorio/
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

A pasta `99_arquivo_exploratorio/` contém testes, versões antigas e saídas auxiliares preservadas para rastreabilidade. Ela não faz parte da execução principal.

## Ordem principal de execução

Os scripts devem ser executados a partir da raiz do projeto:

```bash
python 01_codigo_principal/01_extracao_e_qualidade.py
python 01_codigo_principal/02_feature_engineering_e_clusters.py
python 01_codigo_principal/03_modelagem_zscore_e_iforest.py
python 01_codigo_principal/04_graficos_tcc.py
python 01_codigo_principal/05_tabelas.py
```

As análises complementares podem ser executadas depois:

```bash
python 02_analises_complementares/06_sensibilidade_zscore.py
python 02_analises_complementares/10_teste_contamination.py
python 02_analises_complementares/11_teste_robust_zscore.py
python 02_analises_complementares/13_estabilidade_temporal_clusters.py
```

## Dados e reprodutibilidade

Os dados utilizados nesta Prova de Conceito pertencem ao Tribunal de Justiça do Estado de Goiás e não são distribuídos neste repositório.

A extração original depende de acesso ao ambiente institucional do SEE/TJGO. Por esse motivo, a execução completa do pipeline não é possível fora desse ambiente autorizado.

O repositório disponibiliza:

* os scripts de tratamento e modelagem;
* a metodologia utilizada;
* as análises complementares;
* os gráficos gerados;
* as tabelas e resultados consolidados;
* a documentação técnica do projeto.

A reprodução integral depende de uma base autorizada com a mesma estrutura de dados. Para demonstrações públicas, pode ser utilizada uma base sintética ou anonimizada, desde que preserve o esquema necessário para os scripts.

## Ambiente de desenvolvimento

Para instalar as dependências e consultar o código:

### Linux ou macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

A pasta `venv/` não deve ser versionada no GitHub.

## Segurança e publicação

Por motivos de governança, segurança e proteção de informações institucionais, este repositório não inclui:

* credenciais de acesso;
* usuário ou senha do banco;
* URLs de conexão;
* tokens;
* arquivos `.env`;
* bases originais do SEE/TJGO;
* dados pessoais ou identificáveis;
* capturas de tela com informações restritas.

O arquivo `.env.example` contém apenas valores de exemplo. Arquivos reais de configuração devem permanecer fora do GitHub e nunca devem ser enviados em commits ou compartilhados publicamente.

A pasta `03_dados/` deve conter apenas arquivos autorizados, anonimizados ou instruções sobre como obter os dados em ambiente institucional.

## Tecnologias utilizadas

* Python;
* Pandas;
* NumPy;
* SciPy;
* scikit-learn;
* Matplotlib;
* Seaborn;
* PostgreSQL;
* Power BI;
* K-Means;
* Z-Score;
* Isolation Forest.

## Limitações

* o projeto é uma Prova de Conceito;
* os alertas não foram validados como irregularidades confirmadas;
* não há rótulos completos para medir precisão e recall;
* o comportamento atípico pode ter explicações legítimas;
* a qualidade depende da cobertura e da semântica dos dados;
* a interpretação de valores nulos depende das regras institucionais do SEE;
* os resultados não devem ser usados para decisões automáticas;
* a implantação em produção exigiria governança, controle de acesso, monitoramento e validação institucional.

## Uso responsável

O sistema deve ser utilizado como apoio à triagem.

A interpretação correta é:

> “Este registro apresenta um padrão estatisticamente diferente dos demais e pode merecer revisão.”

A interpretação incorreta seria:

> “Este registro representa fraude.”

Qualquer conclusão deve ser confirmada por profissionais responsáveis, com consulta aos documentos e às fontes oficiais.

## Documentos do TCC

Os materiais acadêmicos e técnicos estão disponíveis em [`00_documentos/`](00_documentos/), incluindo:

* monografia ou artigo;
* relatório técnico;
* apresentação de defesa;
* materiais complementares.

## Monografia

O trabalho completo apresenta a metodologia, os resultados e as limitações da Prova de Conceito.

[Leia a monografia completa em PDF](Monografia_PRTI_TJGO-9.pdf)

## Autor

Geyson de Araújo Sousa

## Licença

Projeto acadêmico e de pesquisa aplicada. A publicação de código, documentos, gráficos e dados deve respeitar as autorizações institucionais aplicáveis.

