# Diseño de la Ontología para el Asistente de Trading Semántico

## 1. Introducción
Este documento describe el diseño de la ontología (ontologia_trading.ttl) para el Asistente Semántico de Decisiones de Trading. La ontología define los conceptos clave, sus atributos y relaciones en el dominio del análisis técnico y la toma de decisiones de trading para criptomonedas. Se utiliza el prefijo trade: para http://www.example.org/trading#.

## 2. Clases Principales

### trade:ActivoDigital
- Clase base para activos digitales.

### trade:Criptomoneda
- Subclase de trade:ActivoDigital. Representa una criptomoneda (ej. Worldcoin).
- **Propiedades de Datos:**
  - trade:simboloCripto (xsd:string, ej. "WLD")
  - trade:nombreCompleto (xsd:string)
  - trade:descripcionActivo (xsd:string, opcional)

### trade:ParMercado
- Representa un par de trading (ej. WLD/USDT).
- **Propiedades de Objeto:**
  - trade:tieneActivoBase (rango: trade:Criptomoneda)
  - trade:tieneActivoCotizacion (rango: trade:Criptomoneda o trade:MonedaFiat)
- **Propiedades de Datos:**
  - trade:precioActual (xsd:decimal)
  - trade:volumen24h (xsd:decimal, opcional)

### trade:TipoIndicadorTecnico
- Clase que representa los tipos base de indicadores (ej. SMA, RSI). Sus instancias serían :TipoSMA, :TipoRSI, etc.
- **Propiedades de Datos:**
  - rdfs:label (para un nombre legible como "Simple Moving Average")

### trade:IndicadorTecnicoConfig
- Representa una configuración específica de un indicador (ej. SMA de 20 días).
- **Propiedades de Objeto:**
  - trade:tieneTipoBase (rango: trade:TipoIndicadorTecnico)
- **Propiedades de Datos:**
  - trade:nombreConfigIndicador (xsd:string)
  - trade:periodoIndicador (xsd:integer)
  - trade:periodoCorto (xsd:integer, para MACD)
  - trade:periodoLargo (xsd:integer, para MACD)
  - trade:periodoSenal (xsd:integer, para MACD)
  - trade:desviacionEstandar (xsd:decimal, para Bandas Bollinger)

### trade:ValorIndicador
- Representa el valor calculado de un indicador técnico en un momento específico para un trade:ParMercado, basado en una trade:IndicadorTecnicoConfig.
- **Propiedades de Objeto:**
  - trade:esValorDe (rango: trade:IndicadorTecnicoConfig)
  - trade:seAplicaA (rango: trade:ParMercado)
- **Propiedades de Datos:**
  - trade:timestampValor (xsd:dateTime)
  - trade:valorNumerico (xsd:decimal, para RSI, SMA)
  - trade:valorMACD (xsd:decimal)
  - trade:valorSenalMACD (xsd:decimal)
  - trade:valorHistogramaMACD (xsd:decimal)
  - trade:valorBandaSuperior (xsd:decimal)
  - trade:valorBandaMedia (xsd:decimal)
  - trade:valorBandaInferior (xsd:decimal)

### trade:SenalTecnica
- Representa una señal interpretada a partir de uno o más trade:ValorIndicador.
- **Propiedades de Objeto:**
  - trade:generadaPorIndicador (rango: trade:ValorIndicador)
  - trade:referenteA (rango: trade:ParMercado)
- **Propiedades de Datos:**
  - trade:tipoSENAL (xsd:string, ej. "PRECIO_SOBRE_SMA20")
  - trade:descripcionSenal (xsd:string)
  - trade:fechaSenal (xsd:dateTime)

### trade:RecomendacionTrading
- La recomendación generada por el sistema.
- **Propiedades de Objeto:**
  - trade:paraActivo (rango: trade:ParMercado)
  - trade:basadaEnEstrategia (rango: trade:Estrategia)
  - trade:basadaEnSenal (rango: trade:SenalTecnica, múltiple)
  - trade:generadaPorAgente (rango: trade:AgenteSenalesTrading)
- **Propiedades de Datos:**
  - trade:accionSugerida (xsd:string: "COMPRAR", "VENDER", "MANTENER")
  - trade:justificacionDecision (xsd:string)
  - trade:nivelConfianza (xsd:float)
  - trade:timestampRecomendacion (xsd:dateTime)

### trade:Estrategia
- Define la configuración y preferencias del sistema.
- **Propiedades de Objeto:**
  - trade:monitoreaPar (rango: trade:ParMercado)
  - trade:utilizaConfigIndicador (rango: trade:IndicadorTecnicoConfig, múltiple)
- **Propiedades de Datos:**
  - trade:nombreEstrategia (xsd:string)
  - trade:nivelRiesgoPreferido (xsd:string: "BAJO", "MEDIO", "ALTO")
  - trade:horizonteTemporal (xsd:string, opcional)

### trade:Agente
- Clase base para los agentes.

### trade:AgentePerfilEstrategia
- Subclase de trade:Agente.

### trade:AgenteSenalesTrading
- Subclase de trade:Agente.

## 3. Propiedades de Objeto y Datos Clave
Las propiedades ya han sido listadas dentro de la descripción de cada clase. Es importante destacar el uso de:
- xsd:dateTime para todos los timestamps
- xsd:decimal para valores financieros y de indicadores
- xsd:string para nombres, descripciones, símbolos, etc.
- xsd:integer para periodos de indicadores
- rdfs:label para nombres legibles de instancias de trade:TipoIndicadorTecnico

## 4. Consideraciones
- **Lógica de Decisión:** Las reglas para pasar de trade:SenalTecnica a trade:RecomendacionTrading residen en el AgenteSenalesTrading. La ontología provee los bloques de construcción, y el agente las combina.
- **Extensibilidad:** La ontología puede expandirse.

Esta ontología proporciona el vocabulario y la estructura semántica para que los agentes representen, consulten y (potencialmente) razonen sobre la información del mercado.