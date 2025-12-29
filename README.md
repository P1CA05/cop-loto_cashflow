# Copiloto de Supervivencia Financiera para PYMEs

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Análisis de cashflow fiable con interpretación IA para PYMEs**

## 🎯 ¿Qué es esto?

El Copiloto de Supervivencia Financiera es una aplicación web que permite a pequeñas y medianas empresas:

1. **Proyectar su cashflow** de forma determinista (cálculos en Python, no IA)
2. **Calcular cuánto capital necesitan** para sobrevivir X meses (3, 6, 9 o 12)
3. **Distinguir entre capital propio y financiación puente** (línea de crédito)
4. **Evaluar suficiencia de su línea de crédito** y detectar brechas de financiación
5. **Generar escenarios** "qué pasa si..." (base, conservador, optimista)
6. **Recibir alertas accionables** y un plan de acción priorizado
7. **Obtener informe ejecutivo** interpretado por IA (con anti-alucinación)
8. **Persistir análisis** para reabrir y comparar históricos

### Principio de Fiabilidad

**Separación estricta: Cálculo vs Interpretación**

- ✅ Python calcula todos los números (cashflow, KPIs, alertas, capital necesario)
- ✅ La IA SOLO interpreta resultados ya calculados
- ✅ La IA NUNCA inventa números ni recalcula
- ✅ Cada recomendación debe citar evidencia del análisis
- ✅ Post-verificación automática para detectar alucinaciones

---

## 🚀 Instalación Rápida

### Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno

### Pasos

1. **Clonar o descargar el repositorio**

```bash
cd copiloto-cashflow
```

2. **Crear entorno virtual (recomendado)**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Instalar dependencias**

```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno (opcional pero recomendado)**

```bash
# Copiar plantilla
cp .env.example .env

# Editar .env y añadir tu API key
# Para Claude (recomendado):
ANTHROPIC_API_KEY=tu-clave-aqui

# O para OpenAI:
# OPENAI_API_KEY=tu-clave-aqui
```

**Nota:** Si no configuras API key, la app funcionará en modo "rules-based" (sin IA, pero completamente funcional).

5. **Ejecutar la aplicación**

```bash
python app.py
```

6. **Abrir en navegador**

```
http://localhost:5000
```

---

## 📊 ¿Qué Archivos Necesito Subir?

### 1. Extracto Bancario (OBLIGATORIO)

Movimientos de tu cuenta bancaria en **CSV o Excel**.

**Columnas necesarias:**
- `Fecha` o `Date`: fecha de transacción
- `Importe` o `Amount`: importe (positivo=ingreso, negativo=pago)
- `Concepto` o `Description`: descripción (opcional)

Alternativamente:
- `Débito` y `Crédito` en columnas separadas

**Ejemplo CSV:**
```csv
Fecha,Importe,Concepto
15/01/2025,1500.00,Cobro cliente ABC
18/01/2025,-850.50,Pago proveedor XYZ
20/01/2025,3200.00,Transferencia
```

### 2. Facturas Emitidas (OPCIONAL pero recomendado)

Facturas pendientes de cobro en **CSV o Excel**.

**Columnas:**
- `ID` o `Número`: identificador
- `Cliente` o `Customer`: nombre del cliente
- `Fecha emisión` o `Issue Date`
- `Fecha vencimiento` o `Due Date`
- `Importe` o `Amount`
- `Estado` o `Status`: paid/unpaid/overdue (opcional)

### 3. Facturas Recibidas (OPCIONAL)

Facturas pendientes de pago. Formato similar a emitidas, con `Proveedor` en lugar de Cliente.

### 4. Gastos Fijos Mensuales (OPCIONAL)

Un único importe mensual (nóminas, alquiler, suscripciones).

### 📥 Plantillas

Encuentra plantillas CSV de ejemplo en `exports/templates/`.

---

## 🎛️ Parámetros de Configuración

### En el formulario web:

- **Saldo Actual**: Tu saldo disponible hoy (€)
- **Horizonte**: 3, 6, 9 o 12 meses (recomendado: 6)
- **Línea de Crédito Total**: Importe total de tu línea de crédito
- **Crédito Usado**: Cuánto has usado ya
- **Interés Anual %**: Para estimar coste de uso
- **Umbral de Seguridad**: Saldo mínimo que quieres mantener
- **Granularidad**: Diaria, Semanal (recomendado) o Mensual
- **Modo Conservador**: Retrasa cobros previstos +15 días

---

## 📈 ¿Qué Resultados Obtendré?

### 1. Resumen Ejecutivo

- **Saldo Mínimo Proyectado**: Punto más bajo de tu caja
- **Nivel de Riesgo**: High/Medium/Low
- **Runway**: Cuántas semanas antes de problemas
- **Capital Total Necesario**: Para sobrevivir X meses

### 2. Desglose de Capital

- **Capital Propio Recomendado**: Buffer estructural (colchón mínimo)
- **Financiación Puente Necesaria**: Crédito temporal para picos
- **Brecha de Financiación**: Si tu línea de crédito no alcanza

### 3. Proyección de Cashflow

Tabla detallada por períodos con:
- Ingresos
- Pagos
- Neto
- Balance acumulado

### 4. Escenarios

- **Base**: Proyección con datos actuales
- **Conservador**: Cobros retrasados +15 días
- **Optimista**: Cobros adelantados parcialmente

### 5. Alertas Accionables

Detección automática de:
- Riesgo de saldo negativo
- Dependencia excesiva de crédito
- Concentración de pagos
- Runway corto
- Brecha de financiación

Cada alerta incluye:
- Severidad (High/Medium/Low)
- Evidencia (KPI o dato específico)
- Acción recomendada

### 6. Plan de Acción Priorizado

- **Inmediato (48h)**: Acciones críticas
- **Corto plazo (7-14 días)**: Optimizaciones tácticas
- **Mediano plazo (30-90 días)**: Mejoras estratégicas

### 7. Informe Ejecutivo

Interpretación en lenguaje natural de los resultados, generada por:
- **IA (Claude 4.5 o GPT-4)** si tienes API key
- **Rules-based** si no hay API key (igualmente útil)

**Anti-alucinación garantizada:**
- La IA NO inventa números
- Verificación automática post-generación
- Todos los números citados deben existir en el análisis

### 8. Descargas

- **TXT**: Informe en texto plano
- **MD**: Informe en Markdown
- **CSV Cashflow**: Proyección completa
- **CSV Escenarios**: Comparativa

### 9. Preguntas Guiadas (Post-Análisis)

Después del primer análisis, puedes refinar las recomendaciones respondiendo:
- Prioridades de negocio
- Timing de cobros
- Control percibido sobre flujos
- Cobros/Pagos grandes no reflejados
- Capacidad de renegociar pagos

**Importante:** Estas respuestas NO cambian números, solo ajustan prioridades y recomendaciones.

---

## 💾 Memoria e Historial

Cada análisis se guarda automáticamente en `data/history/`.

Puedes:
- **Reabrir** análisis anteriores desde el Historial
- **Comparar** resultados entre fechas
- **Exportar** cualquier análisis guardado

---

## 🎓 Cómo Mejorar la Precisión

### Nivel de Confianza

El sistema calcula automáticamente el nivel de confianza:

**Alta:**
- Extracto bancario de 6+ meses
- Facturas emitidas y recibidas incluidas
- Pocos errores de parsing

**Media:**
- Extracto de 3-6 meses
- Facturas emitidas O recibidas (no ambas)
- Calidad de datos aceptable

**Baja:**
- Extracto < 3 meses
- Sin facturas futuras
- Muchas filas inválidas

### Consejos:

✅ **Sube el extracto más completo posible** (mínimo 3 meses, ideal 6+)  
✅ **Incluye facturas pendientes** para proyecciones futuras fiables  
✅ **Proporciona gastos fijos** para capturar costes recurrentes  
✅ **Configura línea de crédito** para análisis de suficiencia  
✅ **Activa modo conservador** si tus clientes suelen pagar tarde

---

## 🔒 Privacidad y Seguridad

- ✅ **Procesamiento local**: Tus datos se procesan en tu servidor
- ✅ **Sin envío de datos bancarios**: Solo se envían a la API de IA los resultados agregados (KPIs, alertas)
- ✅ **Modo rules-based disponible**: Úsalo sin API key para máxima privacidad
- ✅ **Almacenamiento local**: Los análisis se guardan en JSON en tu disco
- ⚠️ **Configura HTTPS en producción**: Si usas esto en entorno real

---

## 🛠️ Arquitectura Técnica

### Stack

- **Backend**: Python 3.10+ con Flask
- **Frontend**: HTML5 + CSS3 + JavaScript (vanilla)
- **Data**: Pandas + openpyxl para procesamiento
- **Persistencia**: JSON (sin base de datos)
- **IA**: Claude 4.5 (Anthropic) o GPT-4 (OpenAI) - opcional

### Módulos Core

```
core/
  validators.py       # Validación de inputs
  bank_import.py      # Parser de extractos bancarios
  invoices_import.py  # Parser de facturas
  events.py           # Constructor de eventos de caja
  cashflow.py         # Proyector de cashflow
  kpis.py             # Calculador de KPIs y supervivencia
  finance_bridge.py   # Análisis de línea de crédito
  scenarios.py        # Generador de escenarios
  alerts.py           # Generador de alertas
  reporting.py        # Plan de acción
  quality.py          # Evaluación de calidad de datos
  prompts.py          # Constructor de prompts IA
  llm_client.py       # Cliente API LLM
  postcheck.py        # Verificador anti-alucinación
  snapshot_tools.py   # Persistencia de análisis
```

### Flujo de Análisis

1. **Validación de inputs** (validators.py)
2. **Parseo de archivos** (bank_import, invoices_import)
3. **Construcción de eventos** (events.py)
4. **Evaluación de calidad** (quality.py)
5. **Proyección de cashflow** (cashflow.py)
6. **Cálculo de KPIs y supervivencia** (kpis.py, finance_bridge.py)
7. **Generación de escenarios** (scenarios.py)
8. **Detección de alertas** (alerts.py)
9. **Plan de acción** (reporting.py)
10. **Informe IA** (prompts.py, llm_client.py, postcheck.py)
11. **Persistencia** (snapshot_tools.py)

---

## 🧪 Testing

Ejecutar tests:

```bash
# Instalar pytest
pip install pytest

# Ejecutar todos los tests
pytest tests/

# Test específico
pytest tests/test_cashflow.py
```

Tests disponibles:
- `test_bank_import.py`: Parsing de extractos
- `test_cashflow.py`: Proyección de caja
- `test_snapshot_tools.py`: Persistencia

---

## 🐛 Solución de Problemas

### Error: "Columna de fecha no encontrada"

Tu CSV debe tener una columna `Fecha`, `Date`, `fecha` o similar. Revisa el formato.

### Error: "Sin transacciones válidas"

Todas las filas tienen fechas o importes inválidos. Verifica formato de fechas (DD/MM/YYYY o YYYY-MM-DD).

### Informe rules-based en lugar de IA

No se encontró API key. Configura `ANTHROPIC_API_KEY` o `OPENAI_API_KEY` en `.env`.

### Muchas filas eliminadas

El parser detecta filas con datos faltantes. Es normal perder algunas filas. Si pierdes >50%, revisa la estructura de tu archivo.

### "Escenario conservador limitado"

No hay datos de cobros futuros (facturas emitidas). El escenario conservador necesita proyecciones futuras.

### Puerto 5000 ya en uso

Cambia el puerto en `.env`:
```
PORT=8000
```
O ejecuta:
```bash
python app.py
# Y abre http://localhost:8000
```

---

## 📚 Limitaciones y Mejoras Futuras

### Limitaciones Actuales

- No soporta múltiples cuentas bancarias simultáneas
- No considera estacionalidad automática (requiere datos de 12+ meses)
- No integra directamente con APIs bancarias (requiere exportación manual)
- Sin gráficos visuales (solo tablas)
- PDF no implementado (solo TXT, MD, CSV)

### Roadmap (posibles mejoras)

- [ ] Gráficos interactivos (Chart.js)
- [ ] Exportación a PDF
- [ ] Integración con Open Banking APIs
- [ ] Detección automática de estacionalidad
- [ ] Comparación entre análisis (diff)
- [ ] Alertas por email
- [ ] Modo multi-usuario con autenticación
- [ ] Base de datos (PostgreSQL) para producción

---

## 🤝 Contribuciones

Contribuciones bienvenidas! Por favor:

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/amazing-feature`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

---

## 📄 Licencia

MIT License - Ver archivo `LICENSE` para detalles.

---

## 🙏 Agradecimientos

- **Flask**: Framework web minimalista y potente
- **Pandas**: Biblioteca indispensable para análisis de datos
- **Anthropic Claude**: IA de última generación con excelente razonamiento
- **Comunidad Python**: Por crear un ecosistema increíble

---

## 📧 Soporte

Para bugs, sugerencias o preguntas:
- Abre un Issue en GitHub
- Revisa la sección de Ayuda en la app (`/help`)

---

**Hecho con ❤️ para PYMEs que quieren sobrevivir y prosperar**

---

## 🎬 Quick Start (TL;DR)

```bash
# Instalar
pip install -r requirements.txt

# Configurar (opcional)
cp .env.example .env
# Editar .env con tu API key

# Ejecutar
python app.py

# Abrir
http://localhost:5000
```

**Sube tu extracto bancario → Obtén análisis de supervivencia en 30 segundos** 🚀
