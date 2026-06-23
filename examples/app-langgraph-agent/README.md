# Telco Churn Analyst — LangGraph + Teradata MCP

Agente conversacional para análisis de churn de clientes Telco. Usa LangGraph (ReAct agent) conectado a Teradata VantageCloud mediante el servidor MCP en Google Cloud Run. La interfaz de demo es un Jupyter Notebook ejecutable en VS Code.

## Arquitectura

```
VS Code (Notebook)  →  LangGraph Agent (Claude Sonnet)
                              ↕ HTTP/SSE
                    MCP Server (Google Cloud Run)
                              ↕ JDBC
                    Teradata VantageCloud
                    └── DEMO_Telco.Customer_Churn
                    └── DEMO_Telco.Cdr_Data
```

## Requisitos

- Python 3.11+
- Jupyter extension para VS Code
- ANTHROPIC_API_KEY
- Acceso al MCP Server de Teradata en Cloud Run

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu ANTHROPIC_API_KEY
```

## Configuración (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
MCP_URL=https://teradata-mcp-server-xxx.run.app/mcp/
LLM_MODEL=claude-sonnet-4-6
```

## Ejecutar el Demo

Abre `demo_churn_telco.ipynb` en VS Code y ejecuta las celdas en orden.

El notebook sigue 5 actos narrativos:
1. **Estado actual** — tasa de churn global e ingreso en riesgo
2. **Segmentos de riesgo** — qué clientes se van y por qué
3. **Señales CDR** — llamadas al soporte como indicador de insatisfacción
4. **Clientes en riesgo** — top candidatos para acción inmediata
5. **Plan de retención** — 3 acciones concretas con impacto estimado

## Ejecutar como CLI

```bash
python agent.py
```

## Estructura

```
app-langgraph-agent/
├── demo_churn_telco.ipynb  # Demo principal (interfaz VS Code)
├── agent.py                # LangGraph ReAct agent + ChurnAnalyst class
├── prompts.py              # System prompt especializado Telco Churn
├── requirements.txt
├── .env.example
└── README.md
```

## Dataset

**DEMO_Telco.Customer_Churn** — 7,043 clientes con 21 atributos (contrato, servicios, cargos, churn)

**DEMO_Telco.Cdr_Data** — Registros de llamadas (CDR) por cliente con minutos, cargos y llamadas al soporte

Para cargar el dataset en Teradata:
```sql
CALL demo_user.get_data('DEMO_Telco_cloud');
```
