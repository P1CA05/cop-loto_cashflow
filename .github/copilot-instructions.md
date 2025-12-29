# Copilot Instructions - Copiloto de Supervivencia Financiera

## Project Overview

**Copiloto de Supervivencia Financiera para PYMEs** es una aplicación web Flask completa para análisis de cashflow con interpretación IA. El proyecto implementa un principio fundamental: **Python calcula números, IA solo interpreta** (anti-alucinación).

## Architecture

### Stack
- **Backend**: Python 3.10+ con Flask 3.0
- **Frontend**: HTML5 + Jinja2 templates + CSS3 + Vanilla JavaScript
- **Data Processing**: Pandas + openpyxl para parsing de CSV/Excel
- **IA**: Claude 4.5 (Anthropic) o GPT-4 (OpenAI) - opcional
- **Persistencia**: JSON (sin base de datos)

### Módulos Core (`core/`)

- `validators.py`: Validación de inputs del usuario
- `bank_import.py`: Parser robusto de extractos bancarios (tolera múltiples formatos)
- `invoices_import.py`: Parser de facturas emitidas/recibidas
- `events.py`: Constructor de eventos de caja unificados
- `cashflow.py`: Proyector de cashflow determinista
- `kpis.py`: Calculador de métricas de supervivencia
- `finance_bridge.py`: Análisis de línea de crédito y suficiencia
- `scenarios.py`: Generador de escenarios (base/conservador/optimista)
- `alerts.py`: Generador de alertas accionables con evidencia
- `reporting.py`: Constructor de plan de acción priorizado
- `quality.py`: Evaluador de calidad y cobertura de datos
- `prompts.py`: Constructor de prompts IA con reglas anti-alucinación
- `llm_client.py`: Cliente API LLM con fallback rules-based
- `postcheck.py`: Verificador post-generación para detectar alucinaciones
- `snapshot_tools.py`: Persistencia de análisis en JSON

### Rutas Flask (`app.py`)

- `GET /`: Formulario de análisis
- `POST /analyze`: Procesar análisis completo
- `GET /results/<snapshot_id>`: Mostrar resultados
- `POST /refine/<snapshot_id>`: Refinar recomendaciones con respuestas del usuario
- `GET /history`: Listar todos los análisis
- `GET /help`: Página de ayuda
- `GET /download/<snapshot_id>/<type>`: Descargar TXT/MD/CSV

## Development Setup

```bash
# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Instalar dependencias
pip install -r requirements.txt

# Configurar (opcional)
cp .env.example .env
# Editar .env con ANTHROPIC_API_KEY o OPENAI_API_KEY

# Ejecutar
python app.py

# Abrir http://localhost:5000
```

## Code Conventions

### Naming
- **Archivos**: `snake_case.py`
- **Funciones**: `snake_case()`
- **Clases**: `PascalCase` (pocas usadas, proyecto funcional)
- **Constantes**: `UPPER_SNAKE_CASE`

### Imports
- Stdlib primero, luego third-party, luego `core/`
- `import logging` en todos los módulos
- Logger configurado en `app.py`

### Error Handling
- `try/except` en parsers y API calls
- Siempre devolver tupla `(result, warnings)` en parsers
- Flash messages para errores de usuario
- Logging para errores de sistema

### Data Flow
1. **Validación** → 2. **Parseo** → 3. **Eventos** → 4. **Cashflow** → 5. **KPIs** → 6. **Alertas** → 7. **IA** → 8. **Snapshot**

### Anti-Hallucination Rules (CRÍTICO)

En `prompts.py`, el prompt IA incluye reglas estrictas:
- NUNCA inventar números, fechas, nombres
- Cada recomendación debe citar evidencia (KPI/alerta/tabla)
- Si dato no disponible, decir "dato no disponible"
- NO recalcular, solo interpretar

En `postcheck.py`:
- Extraer números del informe IA
- Comparar con payload conocido
- Flagear números sospechosos con `*`
- Añadir warnings

## Key Workflows

### Añadir Nuevo Parser
1. Crear `core/nuevo_parser.py`
2. Implementar `parse_archivo(file) -> (DataFrame, List[warnings])`
3. Normalizar columnas con `.str.lower()`
4. Devolver DataFrame con columnas estándar
5. Integrar en `events.py` para generar eventos
6. Actualizar `app.py` para aceptar el archivo

### Añadir Nuevo KPI
1. Extender `_calculate_kpis()` en `cashflow.py`
2. O añadir en `kpis.py` si es de supervivencia
3. Incluir en payload de prompts.py
4. Documentar en templates/results.html

### Añadir Nueva Alerta
1. Extender `generate_alerts()` en `alerts.py`
2. Incluir: severity, title, message, evidence, recommended_action
3. Será automáticamente visible en results.html

### Ejecutar Tests
```bash
pip install pytest
pytest tests/
```

## Common Tasks

### Debugging Parser Issues
- Activar logging: `logging.basicConfig(level=logging.DEBUG)`
- Revisar warnings en UI
- Verificar columnas reconocidas en logs

### Cambiar Modelo IA
En `.env`:
```
ANTHROPIC_API_KEY=...  # Para Claude
# O
OPENAI_API_KEY=...  # Para GPT-4
```

En `llm_client.py`, ajustar modelo name si necesario.

### Añadir Nueva Descarga
En `app.py`, route `/download/<snapshot_id>/<file_type>`:
- Añadir case para nuevo tipo
- Generar contenido
- Usar `send_file()` con mimetype correcto

## Important Notes

### Principio de Fiabilidad
**Separar cálculo de interpretación** es la arquitectura clave:
- Python hace TODOS los cálculos (nunca IA)
- IA recibe resultados ya calculados (KPIs, alertas, tabla)
- IA solo interpreta, prioriza, explica (nunca inventa números)
- Verificación post-generación (`postcheck.py`)

### Memoria Persistente
- Cada análisis se guarda como JSON en `data/history/`
- Index en `data/history/index.json` para listado rápido
- Snapshots incluyen TODO: inputs, cashflow, KPIs, alertas, informes
- Revision tracking para updates (refinement)

### Calidad de Datos
- `quality.py` calcula coverage y confidence automáticamente
- Confidence: High/Medium/Low según cobertura, archivos adicionales, parsing success
- Coverage: meses de extracto bancario disponibles
- Ambos se muestran prominentemente en resultados

### Granularidad
- Daily: Para análisis detallados (muchos períodos)
- Weekly: **Recomendado** (balance detalle/usabilidad)
- Monthly: Para horizontes largos o datos limitados

### Escenarios
- **Base**: Datos tal cual
- **Conservador**: Cobros futuros retrasados +15 días (requiere facturas emitidas)
- **Optimista**: Cobros adelantados -7 días

Si no hay facturas futuras, escenarios limitados (flag `limited` en snapshot).

### Línea de Crédito
- Si user proporciona `credit_line_total`, se simula uso automático
- `finance_bridge.py` calcula max_usage, duración, coste interés estimado
- Se detecta "credit_gap" si crédito insuficiente

### Refine Questions
- Solo aparecen DESPUÉS del análisis inicial
- Respuestas NO cambian números (solo ajustan interpretación IA)
- Generan `report_v2` que reemplaza `report_v1` en resultados

---

**Última actualización: 2025-12-28 - Proyecto completo y ejecutable**
