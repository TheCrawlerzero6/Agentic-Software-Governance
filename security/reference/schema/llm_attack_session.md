# Schema: LlmAttackSession — Plugin para Desarrolladores

> **Fuente de verdad para la coleccion `llm_attack_sessions`.**
> Solo se usa cuando el activo auditado es un **chatbot/LLM** (`targets.chatbot`).
> Registra la ejecucion del corpus de ataques OWASP LLM Top 10 contra el bot.
> Leer este archivo ANTES de insertar o actualizar una sesion.
>
> ⚠️ **Validacion en el gateway:** se valida con `$jsonSchema` (`init-mongo-schema.js`):
> `session_id`, `audit_id`, `owner`, `created_at` obligatorios. Se escribe con la tool
> `submit_llm_session`. Como construir los argumentos: `@reference/gateway-persistence.md`.

---

## Tipos base

```typescript
type SessionChannel = "web_widget" | "http_api" | "whatsapp" | "telegram" | "messenger" | "slack" | "other";
type SessionMode    = "automated" | "manual";
type SessionLang    = "es" | "en" | "multilingual";
type SessionStatus  = "IN_PROGRESS" | "COMPLETED" | "PAUSED" | "CANCELLED";
type EndedReason     = "completed" | "rate_limited" | "user_paused" | "user_aborted" | "error" | null;
```

---

## Interfaz principal

```typescript
interface ReconSignals {
  persona_declared:    string | null;
  model_revealed:      string | null;        // "openai:gpt-4o-mini" si el bot lo revela
  tools_auto_declared: string[];             // herramientas que el bot dice tener
  memory_type:         "none" | "intra_session" | "cross_session" | "cross_user";
  blocked_keywords:    string[];
  evasive_channels:    string[];             // ["summarization", "language_switch", ...]
  alignment:           "firm" | "fragile" | null;
}

interface RateLimitConfig {
  delay_seconds:            number;   // default 2
  cap_messages:             number;   // default 100 (recon + corpus)
  response_timeout_seconds: number;   // default 15
}

interface LlmAttackSession {
  _id?:        string;
  session_id:  string;        // "plugin_<slug>_session_001"
  audit_id:    string;
  owner:       string;        // resuelto por el gateway

  channel:     SessionChannel;
  mode:        SessionMode;
  language:    SessionLang;

  status:      SessionStatus;
  started_at:  string;        // ISO 8601 (-05:00)
  ended_at:    string | null;
  ended_reason: EndedReason;

  // Progreso del corpus
  prompts_total:      number;       // N del corpus tras filtrar por prerequisitos
  prompts_executed:   number;       // contador incremental
  checks_passed:      string[];     // IDs OWASP LLM donde el ataque tuvo exito (vulnerable)
  checks_failed:      string[];     // el bot se defendio
  checks_inconclusive: string[];
  checks_skipped:     string[];     // prerequisitos no cumplidos

  // Recon
  recon_probes_executed: number;    // normalmente 25
  recon_completed_at:    string | null;
  recon_signals:         ReconSignals;

  // Config
  rate_limit_config: RateLimitConfig;

  // Rutas locales
  evidence_dir:      string;        // "audits/{dir}/evidence/llm/"
  manual_state_path?: string | null;

  created_at: string;
  updated_at: string;
}
```

---

## Documento inicial (al iniciar el corpus)

```json
{
  "session_id":  "plugin_<slug>_session_001",
  "audit_id":    "plugin_YYYY-MM-DD_<slug>",
  "channel":     "web_widget",
  "mode":        "automated",
  "language":    "es",

  "status":      "IN_PROGRESS",
  "started_at":  "2026-01-01T00:00:00-05:00",
  "ended_at":    null,
  "ended_reason": null,

  "prompts_total":    75,
  "prompts_executed": 0,
  "checks_passed":    [],
  "checks_failed":    [],
  "checks_inconclusive": [],
  "checks_skipped":   [],

  "recon_probes_executed": 0,
  "recon_completed_at":    null,
  "recon_signals": {
    "persona_declared": null, "model_revealed": null, "tools_auto_declared": [],
    "memory_type": "none", "blocked_keywords": [], "evasive_channels": [], "alignment": null
  },

  "rate_limit_config": { "delay_seconds": 2, "cap_messages": 100, "response_timeout_seconds": 15 },

  "evidence_dir": "audits/{dir}/evidence/llm/",
  "manual_state_path": null,

  "created_at": "2026-01-01T00:00:00-05:00",
  "updated_at": "2026-01-01T00:00:00-05:00"
}
```

---

## Ciclo de vida

- **Iniciar**: insertar con `status="IN_PROGRESS"`, `prompts_executed=0`.
- **Recon**: tras las 4 fases (A/B/C/D) actualizar `recon_signals`, `recon_probes_executed`, `recon_completed_at`. Si `memory_type="cross_user"` → registrar un finding HIGH inmediato antes de lanzar el corpus.
- **Durante el corpus**: cada N prompts actualizar `prompts_executed`, `checks_passed/failed/...`, `updated_at`.
- **Pausar**: `status="PAUSED"`, `ended_reason="user_paused"`.
- **Completar**: `status="COMPLETED"`, `ended_at=now`, `ended_reason="completed"`.
- **Abortar**: `status="CANCELLED"`, `ended_reason="user_aborted"`.

> Cada finding LLM debe llevar en `evidence.conversation_log[]` la conversacion COMPLETA
> (todos los turnos, con `timestamp` ISO 8601, `prompt_id` y `latency_ms`). Ver `finding.md`.
