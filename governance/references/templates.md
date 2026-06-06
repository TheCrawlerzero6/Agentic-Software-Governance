# Templates

These are the canonical `governance/` output shapes. The init script creates minimal versions of these templates; update this reference and the script together when changing required sections.

## Structure

```text
governance/
  README.md
  governance-config.md
  system-context.md
  evidence/
    code.md
    documentation.md
    versioning.md
    agents.md
    specialized/
      index.md
      security.md
      qa.md
      data.md
      performance.md
      compliance.md
  decisions.md
  change-log.md
  technical-debt.md
  action-register.md
  reports/
    governance-report.md
    generated/
  assets/
    architecture.dot
    architecture.png
  interventions/
    ACT-000-template.md
```

## governance-config.md

```md
# Governance Config

## Alcance
- Tipo:
- Ruta revisada:
- Exclusiones:

## Profundidad
- normal / profundo

## Audiencia
- tecnico / jefatura

## Permisos
- seguro / herramientas

## Recursos disponibles
- Repositorio local:
- Historial local:
- Repositorio remoto:
- Documentacion externa:
- Verificacion local:
- Entorno local:
- Reportes existentes:
- Revision especializada:

## Checklist de revision
- [ ] Preparar revision
- [ ] Explorar base
- [ ] Entender sistema
- [ ] Revisar evidencia
- [ ] Reconstruir decisiones
- [ ] Evaluar deuda si aplica
- [ ] Cerrar revision

## Reglas operativas
- No modificar codigo fuente durante la revision base.
- No tocar produccion.
- No usar sudo.
- No ejecutar comandos destructivos.
- Registrar comandos relevantes.
- Guardar evidencia en `governance/`.
- Credenciales: no pedir, imprimir ni guardar tokens o secretos.

## Estado de revision
- Iniciada:
- Ultima actualizacion:
- Pendiente:
```

## system-context.md

```md
# System Context

## 1. Proposito del sistema
## 2. Alcance de revision
## 3. Stakeholders o audiencias inferidas
## 4. Restricciones detectadas
## 5. Contexto del sistema
## 6. Building blocks principales
| ID | Bloque | Ubicacion | Responsabilidad | Evidencia | Confianza |
|---|---|---|---|---|---|
## 7. Flujos principales
| ID | Flujo | Entrada | Salida | Modulos | Regla de negocio | Evidencia | Confianza | Preguntas |
|---|---|---|---|---|---|---|---|---|
## 8. Vista de despliegue/configuracion
## 9. Conceptos transversales
## 10. Decisiones existentes encontradas
## 11. Calidad, riesgos y deuda declarada
## 12. Glosario minimo
## 13. Limitaciones
| ID | Limitacion | Buscado en | Efecto | Continuidad |
|---|---|---|---|---|
## 14. Historial de actualizacion
```

## evidence/*.md

```md
# Evidence: <fuente>

## 1. Estado de fuente
**Estado:** pendiente / revisado / parcial / no encontrado
**Buscado en:**
**Cobertura:**
**Efecto en la revision:**
**Continuidad:**

## 2. Resumen util
- 3 a 7 bullets maximo. Solo registrar lo que cambia la comprension, decision, riesgo, deuda o accion.

## 3. Hallazgos
| ID | Afirmacion | Evidencia | Confianza | Impacto | Destino |
|---|---|---|---|---|---|

## 4. Flujos detectados
| ID | Flujo | Evidencia | Confianza | Destino |
|---|---|---|---|---|

## 5. Decisiones detectadas o inferidas
| ID | Decision | Tipo | Evidencia | Confianza | Pregunta |
|---|---|---|---|---|---|

## 6. Contradicciones y ausencias relevantes
| ID | Tipo | Descripcion | Evidencia | Efecto | Continuidad |
|---|---|---|---|---|---|

## 7. Preguntas utiles
- Solo preguntas que cambian una decision, deuda, riesgo, flujo o accion.

## 8. Comandos relevantes
| Comando | Proposito | Resultado resumido |
|---|---|---|
Registrar detalles relevantes aqui. En chat, usar resumen compacto y preferir `--quiet` cuando el script lo soporte.

## 9. Actualizaciones
```

## evidence/specialized/*.md

```md
# Specialized Evidence: <tipo>

## Estado
**Estado:** pendiente / parcial / no encontrado / revisado
**Buscado en:**
**Efecto en la revision:**
**Continuidad:**

## Senales potenciales

### SEC-POT-001 / QA-POT-001 / DATA-POT-001 / PERF-POT-001 / COMP-POT-001: Titulo corto
**Estado:** potencial / descartado / requiere especialista / confirmado por evidencia directa
**Tipo:** security / qa / data / performance / compliance
**Senal observada:**
**Evidencia:**
**Fuente relacionada:**
**Impacto potencial:** bajo / medio / alto
**Confianza:** baja / media / alta
**Por que requiere revision especializada:**
**No afirmar:** amenaza, explotabilidad, fallo o incumplimiento confirmado sin evidencia directa.
**Puede convertirse en deuda tecnica:** si / no / pendiente
**Accion sugerida:** para SEC-POT usar solo revision especializada o skill/plugin disponible; no correccion directa desde esta skill.
```

## decisions.md

```md
# Decisions

## 1. Criterio usado
## 2. Decisiones documentadas
| ID | Decision | Categoria | Fuente | Evidencia | Estado | Confianza |
|---|---|---|---|---|---|---|
## 3. Decisiones inferidas
| ID | Decision inferida | Categoria | Evidencia | Por que se infiere | Confianza | Pregunta pendiente |
|---|---|---|---|---|---|---|
Usar `Pregunta pendiente: no necesaria` cuando la evidencia escrita sea suficiente. Preguntar solo si la respuesta humana puede cambiar interpretacion, prioridad, alcance, deuda, handoff especializado o accion.
## 4. Decisiones faltantes
| ID | Decision faltante | Por que deberia documentarse | Evidencia | Accion sugerida |
|---|---|---|---|---|
## 5. Decisiones contradictorias
| ID | Contradiccion | Fuente A | Fuente B | Impacto | Accion sugerida |
|---|---|---|---|---|---|
## 6. ADRs retrospectivos sugeridos
| ID | Titulo sugerido | Decision relacionada | Prioridad | Estado |
|---|---|---|---|---|
## 7. Preguntas de validacion humana
## 8. Fichas MADR retrospectivas sugeridas
```

## change-log.md

```md
# Change Log

## Decisiones tomadas durante intervenciones
| ID | Fecha | Cambio/intervencion | Decision tomada | Motivo | Evidencia usada | Impacto documental | Archivos actualizados |
|---|---|---|---|---|---|---|---|
```

## technical-debt.md

```md
# Technical Debt

## 1. Criterio usado
## 2. Resumen
- Total de deudas confirmadas:
- Total de deudas probables:
- Total de deudas aceptadas temporalmente:
- Casos con evidencia insuficiente:
- Zonas mas afectadas:
## 3. Deudas
### TD-001: Titulo corto
**Estado:** candidata / probable / confirmada / aceptada / planificada / en pago / pagada / rechazada
**Tipo:** requisitos / arquitectura / diseno / codigo / pruebas / build / dependencias / documentacion / datos
**Origen:** deliberada / inadvertida / contingente / desconocida
**Artefacto afectado:**
**Decision relacionada:**
**Flujo afectado:** FLW- / no identificado
**Escenario de cambio:**
**Constructo que encarece el cambio:**
**Interes actual:** bajo / medio / alto
**Interes esperado:** bajo / medio / alto
**Probabilidad de interes:** baja / media / alta
**Costo de pago / principal:** bajo / medio / alto
**Beneficio de pago:** bajo / medio / alto
**Costo de no pagar:** bajo / medio / alto
**Impacto en evolucion:** bajo / medio / alto
**Impacto en mantenibilidad:** bajo / medio / alto
**Confianza de evidencia:** baja / media / alta
**Impacto de deuda:**
**Viabilidad de pago:**
**Prioridad estimada:** baja / media / alta / critica
**Evidencia:**
**Evidencia especializada relacionada:** SEC-POT / QA-POT / DATA-POT / PERF-POT / COMP-POT / ninguna
**Contexto faltante:**
**Pregunta al usuario:**
**Decision critica:** si
**Metodo requerido:** request_user_input
**Opciones permitidas:** pagar ahora / pagar con feature / planificar / aceptar temporalmente / monitorear / rechazar
**Decision de gestion:** pagar ahora / pagar con feature / planificar / aceptar temporalmente / monitorear / rechazar
**Fecha de revision:**
```

Los campos con listas de valores deben contener solo un valor permitido. No escribir `alto (explicacion)` ni `datos / seguridad`; poner la explicacion en campos narrativos.

## action-register.md

```md
# Action Register

## Proposito

Registrar insights accionables para seleccion del usuario antes del reporte final.

## Acciones

| ID | Insight | Tipo | Criticidad | Flujo afectado | Contexto faltante | Pregunta al usuario | Evidencia actual | Siguiente paso | Decision critica | Metodo requerido | Opciones permitidas | Decision usuario | Resultado | Intervencion | Estado final |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Opciones de decision
- Corregir seguro
- Posponer
- Descartar
- Requiere especialista

Para acciones de seguridad o `SEC-POT-*`, no usar `Corregir seguro`; opciones validas: `Requiere especialista`, `Posponer`, `Descartar`.

## Metodo requerido
- Para decisiones criticas: `request_user_input`
- Para detalles no decisionales: texto libre despues de una seleccion

## Estados finales
- pendiente de decision
- corregido
- pospuesto
- descartado
- handoff especialista
```

## interventions/ACT-000-template.md

```md
# Intervention ACT-XXX

## Insight seleccionado
- ID:
- Insight:
- Decision usuario: Corregir seguro / Posponer / Descartar / Requiere especialista
- Metodo de decision: request_user_input
- Opciones presentadas:
- Alcance autorizado:

## Evidencia usada

## Cambio aplicado o razon de no aplicar

## Archivos tocados

## Validacion ejecutada

## Impacto documental

## Actualizaciones requeridas
- action-register.md:
- change-log.md:
- evidence:
- report:
```

## reports/governance-report.md

```md
# Informe de Gobernanza por Evidencia

## 0. Configuracion del informe
- Audiencia: tecnico / jefatura
- Nota: la audiencia adapta solo la presentacion del informe; no cambia el proceso, la evidencia ni las conclusiones.

## 1. Lectura rapida
| Item | Estado | Evidencia | Por que importa |
|---|---|---|---|
## 2. Semaforo de gobernanza
| Area | Estado | Confianza | Evidencia | Accion |
|---|---|---|---|---|
## 3. Decisiones o preguntas que requieren atencion
| ID | Tema | Pregunta o decision | Impacto | Evidencia |
|---|---|---|---|---|
## 4. Mapa actual del sistema
## 5. Fuentes revisadas
## 6. Decisiones relevantes
## 7. Hallazgos confirmados
## 8. Evidencia especializada potencial
## 9. Deuda tecnica
## 10. Preguntas abiertas
## 11. Acciones recomendadas
## 12. Evidencia usada
```
