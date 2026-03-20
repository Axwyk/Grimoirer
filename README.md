# Grimoire

Sistema de ranking ELO para batallas ZvZ de Albion Online. Rastrea el rendimiento de jugadores por roles (DPS, Healer, Tank, Support), calcula puntuaciones normalizadas por batalla y asigna ELO basado en contribución individual.

### Features

- **Ranking ELO** con sistema de tiers (Hierro → Gran Maestro)
- **Scoring por rol** — fórmulas adaptadas a DPS, Healer, Tank y Support
- **Detección automática de roles** por arma equipada
- **Agrupación de batallas** desde eventos individuales de la API de Albion
- **Auto-update** — pipeline automático que sincroniza datos periódicamente
- **Dashboard** con stats globales, top jugadores y sistema de rangos
- **Leaderboard** con arma principal, rol y ELO peak
- **Detalle de batallas** con tabla ordenable y gráfico de composición

## Stack Tecnológico

- **Backend:** Django 6 + Django REST Framework
- **Frontend:** React 19 + Vite + React Router
- **Base de datos:** SQLite
- **Fuente de datos:** [API pública de Albion Online](https://wiki.albiononline.com/wiki/API)

---

## Cómo Funciona el Sistema

El sistema opera en un pipeline de 5 pasos que se ejecuta con el comando:

```bash
python manage.py process_all
```

### Paso 1 — Recolección de Batallas del Gremio

Se consulta el endpoint `/battles?guildId=X` de la API de Albion para obtener batallas recientes donde participó el gremio. Para cada batalla, se obtienen los detalles completos (jugadores, kills, deaths, killFame) y se crean **eventos sintéticos** que representan cada kill ocurrido.

### Paso 2 — Recolección de Eventos

Se consulta `/events?guildId=X` para obtener eventos de kill individuales con datos adicionales como **daño hecho** (`DamageDone`) y **curación** (`SupportHealingDone`) por participante.

### Paso 3 — Agrupación en Batallas

Los eventos se agrupan en batallas usando dos criterios:

1. **Por `BattleId` de la API** (prioridad) — todos los eventos con el mismo ID de batalla se agrupan juntos.
2. **Por zona + ventana temporal** (fallback) — eventos en la misma zona dentro de una ventana de 5 minutos.

Una batalla se considera **válida** si cumple los mínimos:
- ≥ 4 jugadores
- ≥ 2 kills
- ≥ 2 gremios involucrados

#### Fusión de Batallas

Similar a [albionbb.com](https://albionbb.com), el sistema detecta **batallas fragmentadas** (el API de Albion a veces reporta la misma pelea como múltiples batallas). Se fusionan automáticamente si:

- Ocurren dentro de una ventana de **10 minutos** entre sí.
- Comparten al menos el **50%** de jugadores en común.

Los eventos de la batalla absorbida se mueven a la batalla superviviente, y se actualizan los tiempos de inicio/fin.

### Paso 4 — Cálculo de Estadísticas

Para cada batalla válida, se calculan las estadísticas individuales de cada jugador y se genera un **score de rendimiento**.

#### Datos adicionales por jugador

- **Item Power (IP):** Se extrae de `AverageItemPower` en los eventos de la API. Se muestra en el detalle de batalla y en el historial del jugador.
- **Kill Feed:** Se registra quién mató a quién, con timestamp y fama ganada.
- **Fama:** Se obtiene `KillFame` de cada evento.

#### Fórmula del Raw Score

El sistema detecta automáticamente el **rol** del jugador por su **arma equipada** (disponible en `Equipment.MainHand.Type` de la API). Si no hay datos de arma, se usa el fallback de `healing > damage`.

**Fórmula DPS (Damage Dealers):**
```
Raw Score = (Daño × 0.18) + (Kills × 600) + (Asistencias × 150) - (Muertes × 600)
```

**Fórmula Healer:**
```
Raw Score = (Curación × 0.40) + (Asistencias × 400) + (Kills × 600) - (Muertes × 500)
```

**Fórmula Tank:**
```
Raw Score = (Asistencias × 800) + (Daño × 0.12) + (Kills × 600) - (Muertes × 500)
```

**Fórmula Support:**
```
Raw Score = (Asistencias × 800) + (Curación × 0.18) + (Daño × 0.08) + (Kills × 600) - (Muertes × 500)
```

| Componente   | DPS    | Healer | Tank   | Support | Descripción                     |
|--------------|--------|--------|--------|---------|---------------------------------|
| Daño         | ×0.18  | —      | ×0.12  | ×0.08   | Daño total infligido            |
| Curación     | —      | ×0.40  | —      | ×0.18   | Curación de soporte             |
| Kills        | ×600   | ×600   | ×600   | ×600    | Eliminaciones confirmadas       |
| Asistencias  | ×150   | ×400   | ×800   | ×800    | Participación en kills          |
| Muertes      | −600   | −500   | −500   | −500    | Penalización por muerte         |

#### Normalización Z-Score

El raw score se normaliza dentro de cada batalla usando **z-score**:

$$z = \frac{score - \mu}{\sigma}$$

Donde $\mu$ es la media y $\sigma$ la desviación estándar de todos los scores en esa batalla. Esto permite comparar rendimiento entre batallas de diferentes tamaños y niveles de actividad.

### Paso 5 — Actualización de ELO

Se actualiza el ELO de todos los jugadores que participaron en batallas válidas.

#### Cálculo del cambio de ELO

```
ΔELO = K × clamp(z, -3, 3) / 3
```

El score normalizado se acota al rango **[-3, +3]** para evitar cambios extremos, y luego se escala por el factor K. La ganancia máxima está **capeada en +31** por batalla, mientras que la pérdida máxima es **-K**.

#### Factor K (volatilidad)

El factor K decrece con la experiencia del jugador:

| Batallas jugadas | Factor K | Volatilidad |
|------------------|----------|-------------|
| < 10             | 40       | Alta — calibración inicial |
| 10 – 29          | 30       | Media — ajuste              |
| ≥ 30             | 20       | Baja — estabilidad          |

Los jugadores nuevos tienen cambios de ELO más grandes para calibrarse rápidamente. A medida que acumulan batallas, su rating se estabiliza.

#### ELO Inicial

Todos los jugadores comienzan con **600 ELO** (Plata 3). El mínimo es 0 (no puede ser negativo).

---

## Rangos

Cada rango tiene 3 subdivisiones (3 → 2 → 1, donde 1 es la más alta), excepto Maestro y Gran Maestro.

| Rango         | ELO Mínimo | Color   |
|---------------|------------|----------|
| Hierro 3      | 0          | Gris     |
| Hierro 2      | 100        | Gris     |
| Hierro 1      | 200        | Gris     |
| Bronce 3      | 300        | Bronce   |
| Bronce 2      | 400        | Bronce   |
| Bronce 1      | 500        | Bronce   |
| **Plata 3**   | **600**    | **Plata** | ← ELO inicial
| Plata 2       | 700        | Plata    |
| Plata 1       | 800        | Plata    |
| Oro 3         | 900        | Dorado   |
| Oro 2         | 1000       | Dorado   |
| Oro 1         | 1100       | Dorado   |
| Platino 3     | 1200       | Cyan     |
| Platino 2     | 1300       | Cyan     |
| Platino 1     | 1400       | Cyan     |
| Diamante 3    | 1500       | Violeta  |
| Diamante 2    | 1600       | Violeta  |
| Diamante 1    | 1700       | Violeta  |
| Maestro       | 1800       | Rosa     |
| Gran Maestro  | 2000       | Rojo     |

Como el ELO inicial es 600, todos arrancan en **Plata 3**. Subir requiere rendimiento consistentemente por encima del promedio.

---

## Ejemplo Práctico

> **Jugador DPS:** QGatoQ — 17 batallas jugadas (K=30)
>
> En una batalla con 8 participantes, QGatoQ hizo 12,000 de daño, 3 asistencias, 1 kill y 0 muertes.
>
> 1. **Raw Score** = (12000 × 0.4) + (3 × 0.3) + (1 × 0.2) - (0 × 0.3) = 4801.1
> 2. **Z-Score** = Supongamos que queda en z = +1.8 (muy por encima del promedio de esa batalla)
> 3. **ΔLO** = 30 × 1.8 / 3 = **+18 ELO**
>
> Si su ELO anterior era 753, pasa a **771 ELO** (Plata 2).

> **Jugador Healer:** ARZID — 6 batallas (K=40)
>
> En una batalla, ARZID hizo 8,000 de curación, 5 asistencias, 0 kills y 1 muerte.
>
> 1. **Raw Score (healer)** = (8000 × 0.5) + (5 × 0.3) + (0 × 0.1) - (1 × 0.2) = 4001.3
> 2. **Z-Score** = z = +1.5
> 3. **ΔLO** = 40 × 1.5 / 3 = **+20 ELO**

### Detección de Rol por Arma

El sistema detecta automáticamente el rol del jugador a partir del **arma principal equipada** (`Equipment.MainHand.Type`). El ID de arma sigue el formato `T{tier}_{slot}_{tipo}_{variante}@{encantamiento}` (ej: `T6_MAIN_HOLYSTAFF_AVALON@2`). Se extrae el tipo base y se clasifica:

| Rol       | Armas detectadas                                                                 |
|-----------|---------------------------------------------------------------------------------|
| **Healer**  | Holy Staff, Divine Staff, Nature Staff, Wild Staff y variantes                |
| **Tank**    | Hammer, Polehammer, Dualhammer, Mace, Flail, Rockmace, Dualmace, Knuckles   |
| **Support** | Arcane Staff, Enigmatic Staff, Enigmatic Orb                                  |
| **DPS**     | Cualquier otra arma (default)                                                 |

Si no hay datos de arma (algunos eventos sintéticos), se usa el fallback: `healing > damage → Healer`.

#### Iconos de Arma

Los iconos se obtienen del **Albion Online Render API**:
```
https://render.albiononline.com/v1/item/{ITEM_ID}.png
```
Ejemplo: `https://render.albiononline.com/v1/item/T6_MAIN_HOLYSTAFF_AVALON@2.png`

#### Nota sobre Tanks y Soportes

La API pública de Albion Online **no proporciona** datos de daño recibido ni CC. Para compensar, los **Tanks** y **Soportes** usan fórmulas centradas en **asistencias** (×500), ya que su labor principal es facilitar kills del equipo, no infligir daño.

---

## Estructura del Proyecto

```
grimoire/
├── backend/          # Configuración Django (settings, urls, wsgi)
├── events/           # Recolección y almacenamiento de eventos de la API
├── battles/          # Agrupación de batallas, cálculo de stats
├── ranking/          # Sistema ELO, rangos, vistas de ranking
├── players/          # Modelo y API de jugadores
├── frontend/         # React + Vite (Dashboard, Leaderboard, Battles, Players)
├── manage.py
└── requirements.txt
```

## Uso

### Instalación

```bash
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python manage.py migrate
```

### Ejecutar el pipeline

```bash
# Pipeline completo (fetch → group → stats → elo)
python manage.py process_all

# Con más páginas de datos
python manage.py process_all --battle-pages 5 --pages 10
```

### Levantar servidores

```bash
# Backend (puerto 8000)
python manage.py runserver 0.0.0.0:8000

# Frontend (puerto 5173)
cd frontend && npm install && npm run dev
```

### API Endpoints

| Endpoint                       | Descripción                                               |
|--------------------------------|-----------------------------------------------------------|
| `GET /api/ranking/`            | Top 100 jugadores por ELO (con rol, arma e icono)         |
| `GET /api/stats/`              | Resumen general (batallas, jugadores)                     |
| `GET /api/battles/`            | Lista de batallas válidas                                 |
| `GET /api/battles/:id/`        | Detalle de batalla con stats, IP, kill feed, arma y rol   |
| `GET /api/players/`            | Lista de jugadores del gremio                             |
| `GET /api/players/:id/`        | Perfil de jugador                                         |
| `GET /api/players/:id/stats/`  | Historial de batallas con arma, rol, IP e iconos          |
