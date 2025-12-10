# 📘 Documentação: Lógica de Cálculo de Tempo de Alarmes para Trackers com Subqueries

## 🎯 Objetivo da Mudança
Eliminar a **duplicidade de tempo** nos cálculos de alarmes de Trackers (TR-XXX), contabilizando corretamente a **disponibilidade real** do equipamento quando múltiplos alarmes ocorrem simultaneamente.

A implementação usa **SUBQUERIES ALINHADAS** para fundir intervalos temporais sobrepostos.

---

## 🔴 Lógica Antiga (Soma Simples)

### Como Funcionava
A lógica antiga simplesmente **somava a duração individual** de cada alarme, sem verificar se eles aconteciam ao mesmo tempo.

### Pseudocódigo Antigo
```pseudocode
PARA CADA tracker (TR-001, TR-002, etc):
    tempo_total = 0
    
    PARA CADA alarme DO tracker:
        duracao = alarme.fim - alarme.inicio
        tempo_total = tempo_total + duracao
        
    RETORNAR tempo_total
```

### Query SQL Antiga
```sql
SELECT
    SPLIT_PART(toc.name, ' - ', 1) AS tracker_code,
    COUNT(a.id) AS quantidade_alarmes,
    ROUND(
        SUM(
            EXTRACT(EPOCH FROM (
                COALESCE(a.clear_date, NOW()) - a.date_time
            )) / 60
        ), 2
    ) AS duracao_total_minutos
FROM (
    -- UNION ALL das tabelas mensais
) a
JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
WHERE a.power_station_id = :usina_id
AND toc.name LIKE 'TR-%'
GROUP BY tracker_code
ORDER BY duracao_total_minutos DESC
LIMIT :limite
```

### ⚠️ Problema
**Exemplo:**
- **Alarme A (Tracker Fora de Posição):** 12:00 às 15:00 = 3 horas
- **Alarme B (Erro na Bateria):** 13:00 às 15:00 = 2 horas
- **Cálculo Antigo:** 3h + 2h = **5 horas** ❌

O tracker esteve indisponível apenas por **3 horas de relógio**, das 12:00 às 15:00. Contar 5 horas distorce a métrica de disponibilidade.

---

## 🟢 Nova Lógica (Aglutinação de Intervalos com Subqueries)

### Como Funciona
A nova lógica **funde intervalos temporais sobrepostos** antes de somar. Ela cria uma "linha do tempo limpa" onde cada minuto é contado apenas uma vez.

### Conceito de Tracker Aglutinado
Os **Trackers** são **teleobjetos de Equipamentos** (das NCUs e afins). Um tracker tem o seguinte formato:

**Formato:** `TR-XXX - Descrição do Alarme`

**Exemplos:**
- `TR-001 - Posição do Tracker`
- `TR-001 - Tensão da Bateria`
- `TR-017 - Erro de Comunicação`
- `TR-017 - Falha no GPS`

**Aglutinação:** Pegamos apenas a parte `TR-XXX` e agrupamos **todos os alarmes** daquele tracker, independente da descrição.

### Pseudocódigo Novo
```pseudocode
PARA CADA tracker (TR-001, TR-002, etc):
    # 1. Buscar todos os alarmes daquele tracker
    alarmes = BUSCAR_ALARMES(tracker)
    
    # 2. Ordenar alarmes pelo horário de início
    alarmes_ordenados = ORDENAR(alarmes, POR=inicio)
    
    # 3. Inicializar lista de intervalos fundidos
    intervalos_fundidos = []
    
    SE alarmes_ordenados ESTÁ VAZIO:
        RETORNAR 0
    
    intervalo_atual = alarmes_ordenados[0]
    
    # 4. Fundir sobreposições percorrendo os alarmes
    PARA CADA alarme EM alarmes_ordenados[1:]:
        SE alarme.inicio <= intervalo_atual.fim:
            # SOBREPOSIÇÃO DETECTADA! 
            # Estende o fim do intervalo atual até o máximo
            intervalo_atual.fim = MAXIMO(intervalo_atual.fim, alarme.fim)
        SENAO:
            # SEM SOBREPOSIÇÃO (existe um GAP)
            # Salva o intervalo atual e inicia um novo
            ADICIONAR(intervalos_fundidos, intervalo_atual)
            intervalo_atual = alarme
    
    # 5. Adicionar o último intervalo
    ADICIONAR(intervalos_fundidos, intervalo_atual)
    
    # 6. Somar apenas os intervalos já fundidos
    tempo_total = 0
    PARA CADA intervalo EM intervalos_fundidos:
        tempo_total = tempo_total + (intervalo.fim - intervalo.inicio)
        
    RETORNAR tempo_total
```

### ✅ Solução
**Mesmo Exemplo:**
- **Alarme A:** 12:00 às 15:00
- **Alarme B:** 13:00 às 15:00
- **Intervalo Fundido:** 12:00 às 15:00
- **Cálculo Novo:** **3 horas** ✅

---

## 🛠️ Implementação SQL (Query com Subqueries Aninhadas)

### 🔑 Diferença: CTEs vs Subqueries

#### CTEs (Common Table Expressions) - Versão Antiga
```sql
WITH cte1 AS (
    SELECT ...
),
cte2 AS (
    SELECT ... FROM cte1
),
cte3 AS (
    SELECT ... FROM cte2
)
SELECT ... FROM cte3
```

**Características:**
- ✅ Mais legível e organizado
- ✅ Pode referenciar CTEs anteriores por nome
- ❌ Pode ser menos eficiente em alguns casos

#### Subqueries Aninhadas - Versão Nova
```sql
SELECT ...
FROM (
    SELECT ...
    FROM (
        SELECT ...
        FROM table
    ) subquery1
) subquery2
```

**Características:**
- ✅ Mais compacto
- ✅ Otimizador pode fazer melhores decisões em alguns casos
- ❌ Menos legível (exige comentários detalhados)

---

### Estratégia: Subqueries com Window Functions

A query utiliza **6 níveis de subqueries aninhadas**, lendo de dentro para fora:

```sql
-- ==========================================================================
-- ESTRUTURA GERAL (6 NÍVEIS)
-- ==========================================================================
-- Lógica: De dentro (nível 1) para fora (nível 6)
-- 
-- Nível 1 (mais interno): Extrai dados brutos dos alarmes
-- Nível 2: Ordena e detecta sobreposições com LAG()
-- Nível 3: Marca início de novos grupos (gaps vs sobreposições)
-- Nível 4: Numera grupos com SUM() OVER
-- Nível 5: Funde intervalos dentro de cada grupo
-- Nível 6 (mais externo): Agrega tempo total por tracker
-- ==========================================================================

SELECT 
    -- NÍVEL 6: AGREGAÇÃO FINAL POR TRACKER
    tracker_code,
    SUM(qtd_alarmes_no_intervalo) AS quantidade_alarmes,
    ROUND(
        SUM(EXTRACT(EPOCH FROM (fim_intervalo - inicio_intervalo)) / 60), 2
    ) AS duracao_total_minutos
FROM (
    -- NÍVEL 5: FUSÃO DE INTERVALOS DENTRO DE CADA GRUPO
    SELECT
        tracker_code,
        grupo_id,
        MIN(inicio) AS inicio_intervalo,
        MAX(fim) AS fim_intervalo,
        COUNT(alarm_id) AS qtd_alarmes_no_intervalo
    FROM (
        -- NÍVEL 4: NUMERAÇÃO DE GRUPOS
        SELECT
            tracker_code,
            inicio,
            fim,
            alarm_id,
            SUM(novo_grupo) OVER (
                PARTITION BY tracker_code 
                ORDER BY inicio
            ) AS grupo_id
        FROM (
            -- NÍVEL 3: DETECÇÃO DE GRUPOS SOBREPOSTOS
            SELECT
                tracker_code,
                inicio,
                fim,
                alarm_id,
                fim_anterior,
                CASE 
                    WHEN fim_anterior IS NULL THEN 1
                    WHEN inicio > fim_anterior THEN 1
                    ELSE 0
                END AS novo_grupo
            FROM (
                -- NÍVEL 2: ORDENAÇÃO E DETECÇÃO DE SOBREPOSIÇÃO
                SELECT
                    tracker_code,
                    inicio,
                    fim,
                    alarm_id,
                    LAG(fim) OVER (
                        PARTITION BY tracker_code 
                        ORDER BY inicio
                    ) AS fim_anterior
                FROM (
                    -- NÍVEL 1: EXTRAÇÃO DOS DADOS
                    SELECT
                        SPLIT_PART(toc.name, ' - ', 1) AS tracker_code,
                        a.date_time AS inicio,
                        COALESCE(a.clear_date, NOW()) AS fim,
                        a.id AS alarm_id
                    FROM (
                        -- UNION ALL das tabelas mensais
                    ) a
                    JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
                    JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
                    WHERE a.power_station_id = :usina_id
                    AND toc.name LIKE 'TR-%'
                ) alarmes_tracker
            ) alarmes_ordenados
        ) grupos_sobrepostos
    ) grupos_numerados
    GROUP BY tracker_code, grupo_id
) intervalos_fundidos
GROUP BY tracker_code
ORDER BY duracao_total_minutos DESC
LIMIT :limite
```

---

## 📊 Explicação Detalhada dos Níveis (De Dentro Para Fora)

### 🔹 Nível 1: Extração dos Dados (`alarmes_tracker`)

**Objetivo:** Buscar todos os alarmes dos trackers (TR-XXX), normalizando os timestamps.

**SQL:**
```sql
SELECT
    -- Extrai apenas 'TR-001' de 'TR-001 - Posição do Tracker'
    SPLIT_PART(toc.name, ' - ', 1) AS tracker_code,
    a.date_time AS inicio,
    -- Se alarme ainda não foi cleared, usa NOW()
    COALESCE(a.clear_date, NOW()) AS fim,
    a.id AS alarm_id
FROM (...)
JOIN public.tele_object tobj ON a.tele_object_id = tobj.id
JOIN public.tele_object_config toc ON tobj.tele_object_config_id = toc.id
WHERE a.power_station_id = :usina_id
AND toc.name LIKE 'TR-%'
```

**Pseudocódigo:**
```pseudocode
PARA CADA alarme NA tabela de alarmes:
    SE alarme.teleobjeto COMEÇA COM 'TR-':
        tracker_code = EXTRAIR_PREFIXO(alarme.teleobjeto)  # Ex: 'TR-001'
        inicio = alarme.data_hora
        fim = SE alarme.foi_cleared ENTÃO alarme.clear_date SENÃO AGORA()
        RETORNAR (tracker_code, inicio, fim, alarm_id)
```

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | alarm_id |
|--------------|------------------|------------------|----------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | 1234     |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 1235     |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 1236     |
| TR-017       | 2025-06-01 10:00 | 2025-06-02 17:00 | 1237     |

---

### 🔹 Nível 2: Ordenação e Detecção de Sobreposição (`alarmes_ordenados`)

**Objetivo:** Ordenar os alarmes por tracker e início, e usar **LAG()** para trazer o horário de término do alarme anterior.

**SQL:**
```sql
SELECT
    tracker_code,
    inicio,
    fim,
    alarm_id,
    LAG(fim) OVER (
        PARTITION BY tracker_code 
        ORDER BY inicio
    ) AS fim_anterior
FROM (...) alarmes_tracker
```

**Função LAG() Explicada:**
```
LAG(fim) OVER (PARTITION BY tracker_code ORDER BY inicio)
     │              │                         │
     │              │                         └─ Ordena por horário de início
     │              └─ Agrupa por tracker (cada tracker separado)
     └─ Pega o valor de 'fim' da LINHA ANTERIOR
```

**Pseudocódigo:**
```pseudocode
alarmes_ordenados = ORDENAR(alarmes_tracker, POR=[tracker_code, inicio])

PARA CADA linha EM alarmes_ordenados:
    SE é_primeira_linha_do_tracker(linha):
        linha.fim_anterior = NULL
    SENAO:
        linha.fim_anterior = linha_anterior.fim
```

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | alarm_id | fim_anterior     |
|--------------|------------------|------------------|----------|------------------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | 1234     | NULL             |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 1235     | 2025-06-01 15:00 |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 1236     | 2025-06-01 15:00 |

---

### 🔹 Nível 3: Detecção de Grupos Sobrepostos (`grupos_sobrepostos`)

**Objetivo:** Detectar se o alarme atual **sobrepõe** o anterior ou se há um **gap** (intervalo de tempo sem alarmes).

**SQL:**
```sql
SELECT
    tracker_code,
    inicio,
    fim,
    alarm_id,
    fim_anterior,
    CASE 
        -- Primeiro alarme do tracker
        WHEN fim_anterior IS NULL THEN 1
        -- Alarme começa DEPOIS do anterior terminar (existe GAP)
        WHEN inicio > fim_anterior THEN 1
        -- Alarme sobrepõe o anterior
        ELSE 0
    END AS novo_grupo
FROM (...) alarmes_ordenados
```

**Lógica Visual:**
```
Alarme Anterior:  [======]
Alarme Atual:              [======]  → GAP → novo_grupo = 1

Alarme Anterior:  [=========]
Alarme Atual:         [======]      → SOBREPOSIÇÃO → novo_grupo = 0

Alarme Anterior:  [===]
Alarme Atual:         [======]      → SOBREPOSIÇÃO → novo_grupo = 0
```

**Pseudocódigo:**
```pseudocode
PARA CADA alarme EM alarmes_ordenados:
    SE alarme.fim_anterior É NULL:
        # Primeiro alarme do tracker
        alarme.novo_grupo = 1
    SENAO SE alarme.inicio > alarme.fim_anterior:
        # Existe um GAP entre os alarmes
        alarme.novo_grupo = 1
    SENAO:
        # Alarme sobrepõe o anterior
        alarme.novo_grupo = 0
```

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | fim_anterior     | novo_grupo |
|--------------|------------------|------------------|------------------|------------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | NULL             | 1          |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 2025-06-01 15:00 | 0          |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 2025-06-01 15:00 | 1          |

📌 **Interpretação:**
- Alarme 1: Primeiro do tracker → `novo_grupo = 1`
- Alarme 2: Sobrepõe o alarme 1 (13:00 < 15:00) → `novo_grupo = 0`
- Alarme 3: Começa depois do alarme 2 (16:00 > 15:00) → `novo_grupo = 1`

---

### 🔹 Nível 4: Numeração de Grupos (`grupos_numerados`)

**Objetivo:** Usar **SUM() OVER** para criar um ID de grupo, somando cumulativamente o campo `novo_grupo`.

**SQL:**
```sql
SELECT
    tracker_code,
    inicio,
    fim,
    alarm_id,
    SUM(novo_grupo) OVER (
        PARTITION BY tracker_code 
        ORDER BY inicio
    ) AS grupo_id
FROM (...) grupos_sobrepostos
```

**Como SUM() OVER funciona:**
```
novo_grupo:  1,  0,  0,  1,  0
             │   │   │   │   │
SUM() OVER → 1 → 1 → 1 → 2 → 2  (soma cumulativa)
             └───┴───┘   └───┘
             Grupo 1     Grupo 2
```

**Pseudocódigo:**
```pseudocode
grupo_acumulado = 0

PARA CADA alarme EM grupos_sobrepostos:
    grupo_acumulado = grupo_acumulado + alarme.novo_grupo
    alarme.grupo_id = grupo_acumulado
```

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | novo_grupo | grupo_id |
|--------------|------------------|------------------|------------|----------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | 1          | 1        |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 0          | 1        |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 1          | 2        |

📌 **Nota:** Alarmes 1 e 2 ficam no **mesmo grupo (1)** porque estão sobrepostos. Alarme 3 está em **grupo separado (2)**.

---

### 🔹 Nível 5: Fusão de Intervalos (`intervalos_fundidos`)

**Objetivo:** Fundir os alarmes dentro de cada grupo, pegando o início do primeiro e o fim do último.

**SQL:**
```sql
SELECT
    tracker_code,
    grupo_id,
    MIN(inicio) AS inicio_intervalo,
    MAX(fim) AS fim_intervalo,
    COUNT(alarm_id) AS qtd_alarmes_no_intervalo
FROM (...) grupos_numerados
GROUP BY tracker_code, grupo_id
```

**Lógica Visual:**
```
Grupo 1:
  Alarme 1: [12:00 ──────── 15:00]
  Alarme 2:     [13:00 ─── 15:00]
  ────────────────────────────────
  Fundido:  [12:00 ──────── 15:00]  (MIN inicio, MAX fim)

Grupo 2:
  Alarme 3: [16:00 ──── 18:00]
  ────────────────────────────
  Fundido:  [16:00 ──── 18:00]
```

**Pseudocódigo:**
```pseudocode
intervalos_fundidos = []

PARA CADA (tracker, grupo) EM grupos_numerados:
    alarmes_do_grupo = FILTRAR(grupos_numerados, tracker=tracker, grupo=grupo)
    
    inicio_intervalo = MINIMO(alarmes_do_grupo.inicio)
    fim_intervalo = MAXIMO(alarmes_do_grupo.fim)
    qtd_alarmes = CONTAR(alarmes_do_grupo)
    
    ADICIONAR(intervalos_fundidos, {
        tracker_code: tracker,
        grupo_id: grupo,
        inicio_intervalo: inicio_intervalo,
        fim_intervalo: fim_intervalo,
        qtd_alarmes_no_intervalo: qtd_alarmes
    })
```

**Exemplo de resultado:**
| tracker_code | grupo_id | inicio_intervalo | fim_intervalo    | qtd_alarmes_no_intervalo |
|--------------|----------|------------------|------------------|--------------------------| 
| TR-001       | 1        | 2025-06-01 12:00 | 2025-06-01 15:00 | 2                        |
| TR-001       | 2        | 2025-06-01 16:00 | 2025-06-01 18:00 | 1                        |

---

### 🔹 Nível 6: Agregação Final (`SELECT` externo)

**Objetivo:** Somar a duração dos intervalos fundidos e retornar o tempo total correto.

**SQL:**
```sql
SELECT
    tracker_code,
    SUM(qtd_alarmes_no_intervalo) AS quantidade_alarmes,
    ROUND(
        SUM(
            EXTRACT(EPOCH FROM (fim_intervalo - inicio_intervalo)) / 60
        ), 2
    ) AS duracao_total_minutos
FROM (...) intervalos_fundidos
GROUP BY tracker_code
ORDER BY duracao_total_minutos DESC
LIMIT :limite
```

**Pseudocódigo:**
```pseudocode
resultado_final = []

PARA CADA tracker EM intervalos_fundidos:
    intervalos = FILTRAR(intervalos_fundidos, tracker_code=tracker)
    
    tempo_total = 0
    quantidade_total = 0
    
    PARA CADA intervalo EM intervalos:
        duracao = (intervalo.fim - intervalo.inicio) EM MINUTOS
        tempo_total = tempo_total + duracao
        quantidade_total = quantidade_total + intervalo.qtd_alarmes
    
    ADICIONAR(resultado_final, {
        tracker_code: tracker,
        quantidade_alarmes: quantidade_total,
        duracao_total_minutos: ARREDONDAR(tempo_total, 2)
    })

ORDENAR(resultado_final, POR=duracao_total_minutos, ORDEM=DECRESCENTE)
RETORNAR PRIMEIROS(:limite) DE resultado_final
```

**Exemplo de resultado final:**
| tracker_code | quantidade_alarmes | duracao_total_minutos |
|--------------|--------------------|-----------------------|
| TR-001       | 3                  | 300.00                |

✅ **Cálculo:** 
- Intervalo 1: 12:00-15:00 = 180 min
- Intervalo 2: 16:00-18:00 = 120 min
- **Total: 300 min (5 horas de TEMPO REAL)**

---

## 🎯 Impacto Esperado

### Antes (Lógica Antiga - Soma Simples)
- **Alarme A:** 12:00-15:00 = 180 min
- **Alarme B:** 13:00-15:00 = 120 min
- **Total:** 300 min ❌ (contou duplicado!)

### Depois (Lógica Nova - Intervalos Fundidos)
- **Intervalo Fundido:** 12:00-15:00 = 180 min
- **Total:** 180 min ✅

### Redução Esperada
É esperado que o "Tempo Total Alarmado" dos Trackers **diminua**, pois deixamos de contar o mesmo minuto várias vezes. A métrica agora reflete a **indisponibilidade real** do equipamento.

---

## 📍 Localização no Código
**Arquivo:** `database/queries.py`  
**Função:** `obter_alarmes_trackers`  
**Linhas:** 1218-1334

## 📅 Data da Implementação
10 de dezembro de 2025

## 🔄 Histórico de Versões
- **09/12/2025:** Implementação inicial com CTEs (Common Table Expressions)
- **10/12/2025:** Refatoração para Subqueries Aninhadas com comentários detalhados
