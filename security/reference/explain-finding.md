# Skill: Explicar Vulnerabilidad

## Cuando activar

El desarrollador menciona: "explícame esta vulnerabilidad", "no entiendo este problema",
"qué significa esto", "cómo funciona este ataque", "por qué es peligroso",
"qué es inyección SQL", "qué es XSS", "qué es IDOR".

## Flujo

### PASO 1 — Identificar qué explicar

Si el dev menciona un hallazgo específico del reporte: enfocarse en ese.
Si es una pregunta general (ej: "qué es XSS"): explicar el concepto.

### PASO 2 — Explicar en lenguaje developer

Estructura de la explicación:

```
## {Nombre de la vulnerabilidad}

### ¿Qué es?
{Explicación en 2-3 oraciones simples, sin jerga}

### ¿Por qué es peligroso?
{Escenario real de lo que un atacante podría hacer}

### ¿Cómo se ve en tu código?
{código vulnerable}

### ¿Cómo se arregla?
{código corregido}

### ¿Cómo se prueba?
1. {paso para reproducir}
2. {paso 2}
3. {resultado esperado si es vulnerable}

### Más información
- {link OWASP}
- {link con ejemplos}
```

### PASO 3 — Ofrecer corrección

```
¿Quieres que aplique la corrección directamente en tu código? (sí/no)
```

## Reglas

- Explicar como si el dev nunca hubiera oído hablar de seguridad
- Usar analogías del mundo real cuando sea posible
- Siempre incluir código vulnerable vs corregido en el lenguaje del proyecto
- Si el dev tiene más preguntas, seguir explicando
