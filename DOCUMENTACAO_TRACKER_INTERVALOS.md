# 📘 Documentação: Nova Lógica de Cálculo de Tempo de Alarmes para Trackers

## 🎯 Objetivo da Mudança
Eliminar a **duplicidade de tempo** nos cálculos de alarmes de Trackers (TR-XXX), contabilizando corretamente a **disponibilidade real** do equipamento quando múltiplos alarmes ocorrem simultaneamente.

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

## 🟢 Nova Lógica (Aglutinação de Intervalos)

### Como Funciona
A nova lógica **funde intervalos temporais sobrepostos** antes de somar. Ela cria uma "linha do tempo limpa" onde cada minuto é contado apenas uma vez.

### Pseudocódigo Novo
```pseudocode
PARA CADA tracker (TR-001, TR-002, etc):
    # 1. Ordenar alarmes pelo horário de início
    alarmes_ordenados = ORDENAR(alarmes_do_tracker, POR=inicio)
    
    intervalos_fundidos = []
    intervalo_atual = alarmes_ordenados[0]
    
    # 2. Fundir sobreposições
    PARA CADA alarme EM alarmes_ordenados[1:]:
        SE alarme.inicio <= intervalo_atual.fim:
            # Sobreposição detectada! Estende o fim do intervalo
            intervalo_atual.fim = MAXIMO(intervalo_atual.fim, alarme.fim)
        SENAO:
            # Sem sobreposição (gap). Salva o atual e começa um novo
            ADICIONAR(intervalos_fundidos, intervalo_atual)
            intervalo_atual = alarme
            
    ADICIONAR(intervalos_fundidos, intervalo_atual)
    
    # 3. Somar apenas os intervalos já fundidos
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

## 🛠️ Implementação SQL (Nova Query)

### Estratégia: CTEs com Window Functions

A query utiliza **6 passos** implementados com CTEs (Common Table Expressions):

```sql
WITH alarmes_tracker AS (
    -- Passo 1: Buscar todos os alarmes de trackers
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
),
alarmes_ordenados AS (
    -- Passo 2: Ordenar e trazer o fim do alarme anterior
    SELECT
        tracker_code,
        inicio,
        fim,
        alarm_id,
        LAG(fim) OVER (PARTITION BY tracker_code ORDER BY inicio) AS fim_anterior
    FROM alarmes_tracker
),
grupos_sobrepostos AS (
    -- Passo 3: Detectar início de novo grupo (sem sobreposição)
    SELECT
        tracker_code,
        inicio,
        fim,
        alarm_id,
        fim_anterior,
        CASE 
            -- Primeiro alarme do tracker
            WHEN fim_anterior IS NULL THEN 1
            -- Alarme começa DEPOIS do anterior terminar (GAP)
            WHEN inicio > fim_anterior THEN 1
            -- Alarme sobrepõe o anterior
            ELSE 0
        END AS novo_grupo
    FROM alarmes_ordenados
),
grupos_numerados AS (
    -- Passo 4: Numerar grupos com soma cumulativa
    SELECT
        tracker_code,
        inicio,
        fim,
        alarm_id,
        SUM(novo_grupo) OVER (PARTITION BY tracker_code ORDER BY inicio) AS grupo_id
    FROM grupos_sobrepostos
),
intervalos_fundidos AS (
    -- Passo 5: Fundir intervalos dentro de cada grupo
    SELECT
        tracker_code,
        grupo_id,
        MIN(inicio) AS inicio_intervalo,
        MAX(fim) AS fim_intervalo,
        COUNT(alarm_id) AS qtd_alarmes_no_intervalo
    FROM grupos_numerados
    GROUP BY tracker_code, grupo_id
)
-- Passo 6: Resultado final
SELECT
    tracker_code,
    SUM(qtd_alarmes_no_intervalo) AS quantidade_alarmes,
    ROUND(
        SUM(
            EXTRACT(EPOCH FROM (fim_intervalo - inicio_intervalo)) / 60
        ), 2
    ) AS duracao_total_minutos
FROM intervalos_fundidos
GROUP BY tracker_code
ORDER BY duracao_total_minutos DESC
LIMIT :limite
```

---

## 📊 Explicação Detalhada dos Passos

### Passo 1: `alarmes_tracker`
Busca todos os alarmes dos trackers (TR-XXX), normalizando os timestamps.

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | alarm_id |
|--------------|------------------|------------------|----------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | 1234     |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 1235     |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 1236     |

---

### Passo 2: `alarmes_ordenados`
Ordena os alarmes por `tracker_code` e `inicio`, e usa a função **LAG()** para trazer o horário de término do alarme anterior.

**Função LAG():**
```sql
LAG(fim) OVER (PARTITION BY tracker_code ORDER BY inicio) AS fim_anterior
```
- **PARTITION BY tracker_code:** Agrupa por tracker
- **ORDER BY inicio:** Ordena por horário de início
- **LAG(fim):** Pega o valor de `fim` da linha anterior

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | alarm_id | fim_anterior     |
|--------------|------------------|------------------|----------|------------------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | 1234     | NULL             |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 1235     | 2025-06-01 15:00 |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 1236     | 2025-06-01 15:00 |

---

### Passo 3: `grupos_sobrepostos`
Detecta se o alarme atual **sobrepõe** o anterior ou se há um **gap** (intervalo de tempo sem alarmes).

**Lógica:**
- Se `inicio > fim_anterior` → **GAP** → `novo_grupo = 1`
- Se `inicio <= fim_anterior` → **Sobreposição** → `novo_grupo = 0`

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | fim_anterior     | novo_grupo |
|--------------|------------------|------------------|------------------|------------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | NULL             | 1          |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 2025-06-01 15:00 | 0          |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 2025-06-01 15:00 | 1          |

---

### Passo 4: `grupos_numerados`
Usa **SUM() OVER** para criar um ID de grupo, somando cumulativamente o campo `novo_grupo`.

**Exemplo de resultado:**
| tracker_code | inicio           | fim              | grupo_id |
|--------------|------------------|------------------|----------|
| TR-001       | 2025-06-01 12:00 | 2025-06-01 15:00 | 1        |
| TR-001       | 2025-06-01 13:00 | 2025-06-01 15:00 | 1        |
| TR-001       | 2025-06-01 16:00 | 2025-06-01 18:00 | 2        |

📌 **Nota:** Alarmes 1 e 2 estão no mesmo grupo (sobrepostos), alarme 3 está em grupo separado.

---

### Passo 5: `intervalos_fundidos`
Funde os alarmes dentro de cada grupo, pegando:
- **MIN(inicio)**: Início do primeiro alarme do grupo
- **MAX(fim)**: Fim do último alarme do grupo

**Exemplo de resultado:**
| tracker_code | grupo_id | inicio_intervalo | fim_intervalo    | qtd_alarmes_no_intervalo |
|--------------|----------|------------------|------------------|--------------------------|
| TR-001       | 1        | 2025-06-01 12:00 | 2025-06-01 15:00 | 2                        |
| TR-001       | 2        | 2025-06-01 16:00 | 2025-06-01 18:00 | 1                        |

---

### Passo 6: Resultado Final
Soma a duração dos intervalos fundidos e retorna o tempo total correto.

**Exemplo de resultado:**
| tracker_code | quantidade_alarmes | duracao_total_minutos |
|--------------|--------------------|-----------------------|
| TR-001       | 3                  | 300.00                |

✅ **3 horas (12h-15h) + 2 horas (16h-18h) = 5 horas de TEMPO REAL**

---

## 🎯 Impacto Esperado

### Antes (Lógica Antiga)
- **Alarme A:** 12:00-15:00 = 180 min
- **Alarme B:** 13:00-15:00 = 120 min
- **Total:** 300 min ❌

### Depois (Lógica Nova)
- **Intervalo Fundido:** 12:00-15:00 = 180 min
- **Total:** 180 min ✅

### Redução Esperada
É esperado que o "Tempo Total Alarmado" dos Trackers **diminua**, pois deixamos de contar o mesmo minuto várias vezes. A métrica agora reflete a **indisponibilidade real** do equipamento.

---

## 📍 Localização
**Arquivo:** `database/queries.py`  
**Função:** `obter_alarmes_trackers`  
**Linhas:** 1218-1323

## 📅 Data da Implementação
09 de dezembro de 2025
