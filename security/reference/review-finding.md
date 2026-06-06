# Skill: Revisar Finding (marcar uno suelto)

## Cuando activar
El dev menciona: "marca el finding X como", "este finding es falso positivo", "ya arreglé
el finding", "confirmo la vulnerabilidad", "no voy a arreglar esto", "marca como corregida".

Para revisar TODOS los findings de una auditoría en secuencia, usar `review-loop.md`.

## Flujo

### PASO 1 — Identificar el finding
Si el dev da un `finding_id` (formato `plugin_YYYY-MM-DD_<slug>_F00N`), usarlo.
Si da un número o título, listar y preguntar:
```
mcp__gateway__get_audit_findings({"audit_id": "<ultimo_audit_id>"})
```
Mostrar lista numerada con título + severidad + estado actual (nombre amigable).

### PASO 2 — Determinar el nuevo estado
Usar la **tabla de traducción** de `review-loop.md`. El dev nunca ve los enums; ve nombres
amigables y el plugin mapea a `status` + `decision` antes de llamar al servidor.

Si no se puede normalizar por sinónimos, mostrar el menú:
```
¿Cómo quieres marcar este finding?
1. Confirmada — es real, falta corregirla
2. Corregida — ya la arreglaste
3. Falso positivo — es comportamiento esperado de la app
4. Aceptación de riesgo — es real, tu área asume el riesgo de no mitigarla
5. Fuera de alcance — corresponde a otro componente que no administras
6. Conversar — tengo dudas, quiero entender mejor o no estoy de acuerdo
```

**Opción 6 — Conversar:** conversación libre sobre este finding. El dev puede preguntar
sobre la vulnerabilidad, el escenario de ataque, la sugerencia de mitigación, o argumentar
que no es vulnerable. El plugin evalúa contra la evidencia: si el argumento es válido →
sugiere Falso positivo; si no se sostiene → explica con la evidencia concreta por qué sí es
vulnerable. Sin límite de turnos. Al terminar, re-presenta el menú. Ver lógica completa en
`@reference/review-loop.md` (Opción 5 — Conversar).

Mapeo opción → modelo (no mostrar al dev):

| Opción | `status` | `decision` | ¿Comentario ≥10? |
|---|---|---|---|
| 1. Confirmada | `OPEN` | `CONFIRMED` | no |
| 2. Corregida | `FIXED` | `CONFIRMED` | **sí** |
| 3. Falso positivo | `FALSE_POSITIVE` | `FALSE_POSITIVE` | **sí** |
| 4. Aceptación de riesgo | `ACCEPTED_RISK` | `CONFIRMED` | **sí** |
| 5. Fuera de alcance | `WONT_FIX` | `OUT_OF_SCOPE` | **sí** |
| 6. Conversar | *(no persiste nada)* | *(vuelve al menú)* | no |

### PASO 2.5 — Coherencia y bloqueo (escenario 4)
Antes de cerrar con Falso positivo / Aceptación de riesgo / Fuera de alcance, aplicar el
**Asistente de coherencia** y el **Bloqueo escenario 4** de `@reference/review-loop.md`:
- CRÍTICO/ALTO con impacto demostrado NO se puede marcar Falso positivo, ni Fuera de alcance
  si es código/dependencia propia → bloquear y ofrecer corregir / aceptar riesgo / correo a
  `tu equipo de seguridad`. "Fuera de alcance" sí vale para servidor/protocolo/certificado.
- Si el motivo de "Aceptación de riesgo" suena a "lo arreglo luego/en producción", sugerir
  **Confirmada**; si suena a componente externo, sugerir **Fuera de alcance**.

### PASO 3 — Pedir comentario (obligatorio ≥10 chars al cerrar)
El servidor exige `review_note` ≥10 para `FIXED`, `FALSE_POSITIVE`, `ACCEPTED_RISK`, `WONT_FIX`. Pedirlo:
- **Corregida:** "¿Cómo lo arreglaste? (commit/PR, función, sanitización aplicada)"
- **Falso positivo:** "¿Por qué es comportamiento esperado de la app?"
- **Aceptación de riesgo:** "¿Qué área asume el riesgo y por qué?"
- **Fuera de alcance:** "¿A qué componente o equipo corresponde?"

Insistir si <10 chars. Para **Confirmada** el comentario es opcional (es estado intermedio; el
cierre real ocurre en `review-loop.md` FASE 2).

### PASO 4 — Actualizar
```
mcp__gateway__update_finding_review({
  "finding_id": "<finding_id>",
  "status": "<OPEN|FIXED|FALSE_POSITIVE|ACCEPTED_RISK|WONT_FIX>",
  "decision": "<CONFIRMED|FALSE_POSITIVE|OUT_OF_SCOPE>",
  "review_note": "<comentario o vacío si Confirmada>"
})
```
Si la respuesta es `{success:false, error_code:"review_note_required"}` → volver al PASO 3.
Otros errores ("finding no encontrado") → informar.

### PASO 5 — Confirmar (nombre amigable)
```
✓ Finding <display_id> marcado como: <nombre amigable>
   Título: <title>
   Antes: <amigable del old_status> → Ahora: <amigable del new_status>
   <Si hay nota>: Nota: <review_note>
```

## Reglas
- Solo findings **propios** (el gateway valida ownership).
- El estado es reversible (Confirmada → Corregida, etc.).
- Comentario obligatorio ≥10 chars al cerrar (FIXED/FALSE_POSITIVE/ACCEPTED_RISK/WONT_FIX) — lo exige el servidor.
- Nunca exponer enums crudos; usar la tabla de traducción de `review-loop.md`.
- Si el dev no da finding_id, listar primero para que confirme.
