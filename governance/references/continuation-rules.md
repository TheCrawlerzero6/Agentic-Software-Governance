# Continuation Rules

The review should continue through the full flow even when evidence is incomplete. Missing evidence is itself a finding.

## Continue After Documenting

Continue when:

- a source folder/file does not exist;
- git is unavailable or not a valid repository;
- docs, ADRs, tests, Docker, MCPs, or GitHub are unavailable;
- a decision is inferable but not confirmed;
- a contradiction exists between sources;
- a debt signal lacks enough evidence for formal debt.

Record the condition, where you looked, impact, confidence, and a pending question if useful.

## Block Only When

- initial inputs are missing: depth, audience, permissions, or scope;
- writing `governance/` is impossible;
- the user requests a tool/action that is outside permissions and denies authorization;
- the repo cannot be read at all.

## Missing Evidence Pattern

Use this wording pattern:

```md
**Estado de fuente:** no encontrado / parcial / revisado
**Buscado en:** rutas, comandos o documentos
**Efecto en la revision:** que limita o que no limita
**Confianza:** baja / media / alta
**Continuidad:** se continua con el siguiente paso porque ...
**Pregunta pendiente:** solo si una respuesta humana cambiaria la interpretacion
```

## Inference Pattern

```md
**Inferencia:** decision o interpretacion
**Evidencia:** rutas, commits, docs o comandos
**Por que se infiere:** razon breve
**Confianza:** baja / media / alta
**Necesita confirmacion:** si/no, pregunta concreta
```

