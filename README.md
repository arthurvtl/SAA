# 🔆 Sistema de Análise de Alarmes (SAA)

## Descrição

Sistema de Business Intelligence desenvolvido em Python + Streamlit para análise e monitoramento de alarmes gerados por equipamentos em usinas de geração de energia solar.

## Características Principais

- ✅ **Queries SQL otimizadas** com índices e UNION ALL eficiente
- ✅ **Código modular** separado em módulos específicos
- ✅ **Clean Code** com funções pequenas e responsabilidade única
- ✅ **Variáveis descritivas** que deixam claro o propósito
- ✅ **Comentários claros** explicando funções, parâmetros e retornos

## Estrutura do Projeto

```
sistema_analise_alarmes/
├── app.py                          # Arquivo principal Streamlit
├── config.py                       # Configurações (DATABASE_URL)
├── requirements.txt                # Dependências
├── README.md                       # Este arquivo
├── database/
│   ├── __init__.py
│   ├── conexao.py                  # SQLAlchemy engine e session
│   ├── models.py                   # Modelos ORM
│   └── queries.py                  # Funções de consulta SQL
├── calculos/
│   ├── __init__.py
│   ├── kpis.py                     # Cálculo de KPIs
│   ├── agregacoes.py               # Agregações
│   └── formatacao.py               # Formatação de tempo
├── visualizacoes/
│   ├── __init__.py
│   ├── graficos.py                 # Gráficos PyEcharts
│   ├── tabelas.py                  # Tabelas Streamlit
│   └── cards.py                    # Cards de KPIs
└── utils/
    ├── __init__.py
    └── helpers.py                  # Funções auxiliares
```

## Requisitos

- Python 3.9 ou superior
- PostgreSQL 12 ou superior
- Acesso ao banco de dados

## Instalação

### 1. Clone ou copie o projeto

```bash
cd /home/ubuntu/sistema_analise_alarmes
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure a conexão com o banco de dados

Edite o arquivo `config.py` e ajuste a variável `DATABASE_URL` conforme necessário:

```python
DATABASE_URL = "postgresql+psycopg2://usuario:senha@host:porta/banco"
```

## Execução

### Executar o Sistema

```bash
streamlit run app.py
```

O sistema estará disponível em: **http://localhost:8501**

### Acessar de outra máquina na rede

```bash
streamlit run app.py --server.address=0.0.0.0
```

## Funcionalidades

### Página HOME

- **Filtros:** Ano (dropdown) e Meses (checkboxes, máx 3)
- **KPIs Gerais:** Total de Usinas, Total de Alarmes, Tempo Total, Tempo Médio
- **Gráfico Pizza:** Distribuição de Alarmes por Usina
- **Gráfico Barras:** Top 10 Usinas com Mais Alarmes
- **Tabela Ranking:** Todas as 55 usinas com botão "Analisar"

### Página ANÁLISE DETALHADA

#### Sidebar
- Seleção de Usina (dropdown)
- Seleção de Ano (dropdown)
- Seleção de Meses (checkboxes, máx 3)

#### Área Principal
- **4 KPIs principais:**
  1. Total de Alarmes
  2. Tempo Total Alarmado
  3. Tempo Médio por Alarme
  4. Tempo Médio de Reconhecimento

- **11 Gráficos:**
  1. Pizza - Tempo Total por Severidade
  2. Barras Horizontais - Top 5 Equipamentos (toggle Quantidade/Duração)
  3. Barras Horizontais - Top 5 Teleobjetos (toggle Quantidade/Duração)
  4. Barras Horizontais - Top 5 Equipamentos Sem Comunicação
  5. Barras Horizontais - Tempo Médio de Reconhecimento por Severidade
  6. Barras Horizontais - Top 5 Usuários que Mais Reconhecem
  7. Barras Horizontais - Alarmes Críticos por Equipamento
  8. Barras Horizontais - Alarmes Críticos por Teleobjeto
  9. Barras Horizontais - Top 10 Alarmes Não Finalizados
  10. Linha - Evolução Diária (toggle Quantidade/Tempo)
  11. Barras - Resumo por Mês (quando multi-mês)

- **Tabela de Alarmes:**
  - Paginação de 50 alarmes por página
  - Colunas: Data Início, Data Fim, Duração, Equipamento, Teleobjeto, Severidade, Descrição, Reconhecimento

## Regras de Negócio

### Limites
- Máximo de **3 meses** por consulta
- Alarmes não finalizados: `clear_date IS NULL`
- Sem comunicação: `description ILIKE '%sem comunicação%'`
- Alarmes críticos: `alarm_severity_id = 1`

### Cálculos
- **Duração:** `(clear_date - date_time)` ou `(NOW() - date_time)` se não finalizado
- **Evolução diária:** Alarmes que iniciaram naquele dia (`date_time`)
- **Tempo formatado:** X dias, Y horas, Z minutos

### Dados
- Sempre usar **NOMES** (não IDs) fazendo JOINs
- Tabelas dinâmicas: `alarm_{usina_id}_{ano}_{mes}`
- 55 usinas solares com dados de 2021 a 2025
- 1.637 tabelas dinâmicas de alarmes

## Tecnologias Utilizadas

- **Frontend:** Streamlit
- **Backend:** Python 3.9+
- **Banco de Dados:** PostgreSQL
- **ORM:** SQLAlchemy
- **Visualização:** PyEcharts
- **Manipulação de Dados:** Pandas, NumPy

## Estrutura do Banco de Dados

### Tabelas Principais

1. **power_station:** Cadastro de usinas
2. **equipment:** Cadastro de equipamentos
3. **skid:** Agrupamento de equipamentos
4. **tele_object:** Teleobjetos (pontos de monitoramento)
5. **tele_object_config:** Configuração de teleobjetos
6. **alarm_severity:** Níveis de severidade
7. **users:** Usuários do sistema
8. **alarm_*:** Tabelas dinâmicas de alarmes (por usina/ano/mês)

### Severidades (com cores)

| ID | Nome | Cor | Descrição |
|----|------|-----|------------|
| 1 | Crítica | #f14e4e | Vermelho |
| 2 | Alta | #fdc262 | Laranja |
| 3 | Média | #ffe00a | Amarelo |
| 4 | Baixa | #80FFFF | Azul claro |
| 5 | Não Apl. | #F0F0F0 | Cinza |
| 6 | Urgente | #000000 | Preto |

## Troubleshooting

### Erro de Conexão com Banco de Dados

```
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) could not connect to server
```

**Solução:**
1. Verifique se o PostgreSQL está rodando
2. Verifique as credenciais em `config.py`
3. Verifique se o host/porta estão corretos


