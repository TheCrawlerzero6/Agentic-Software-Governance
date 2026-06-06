// Aplica JSON Schema validators a las colecciones de pentest_audits.
// Se ejecuta automáticamente al inicializar el contenedor MongoDB
// (montado en /docker-entrypoint-initdb.d/). También puede correrse a mano con mongosh.
//
// - validationLevel: "moderate"  -> NO rompe documentos existentes (solo valida inserts y
//                                   updates de documentos que ya cumplen el schema)
// - validationAction: "error"    -> rechaza inserts/updates invalidos
//
// IMPORTANTE (notas del validador):
//   * Las FECHAS son strings ISO-8601 (el gateway de devs usa _iso_now()), NO BSON date.
//     => bsonType: "string" en todos los campos de fecha. Copiar "date" rechazaria TODO.
//   * NUNCA se usa additionalProperties:false -> se permiten campos extra; solo se
//     restringen tipo/enum/required de los campos conocidos.
//   * events.event_type es "string" SIN enum (la canonicidad la maneja el gateway marcando
//     deprecated_schema) para no rechazar telemetria inesperada.
//   * Todo lo opcional es nullable; required = exactamente lo que el gateway escribe siempre.
//
// Colecciones: audit_runs, findings, events, llm_attack_sessions

const DB = db.getSiblingDB("pentest_audits");

// --- helper -----------------------------------------------------------------

function applyValidator(collName, schema) {
  try { DB.createCollection(collName); } catch (e) { /* ya existe */ }

  const result = DB.runCommand({
    collMod: collName,
    validator: { $jsonSchema: schema },
    validationLevel: "moderate",
    validationAction: "error"
  });

  if (result.ok === 1) {
    print("[OK] " + collName);
  } else {
    print("[ERROR] " + collName + ": " + JSON.stringify(result));
  }
}

// --- audit_runs -------------------------------------------------------------

const auditRunSchema = {
  bsonType: "object",
  required: [
    "audit_id", "source", "owner", "project_name", "asset_name", "asset_type",
    "target_url", "audit_type", "modality", "status",
    "created_at", "started_at",
    "tier_1_approved", "tier_2_approved",
    "parent_audit_id", "retest_number",
    "findings_count", "severities"
  ],
  properties: {
    _id:            { bsonType: "objectId" },
    audit_id:       { bsonType: "string" },
    source:         { bsonType: "string" },
    executed_by:    { bsonType: "string" },
    owner:          { bsonType: "string" },
    client_ip:      { bsonType: ["string", "null"] },
    project_name:   { bsonType: "string" },
    asset_name:     { bsonType: "string" },
    asset_type:     { bsonType: "string", enum: ["api", "web", "web_api", "chatbot", "n8n_flujo", "node_n8n"] },
    target_url:     { bsonType: "string" },
    audit_type:     { bsonType: "string", enum: ["APROBACION_ACTIVOS", "RETEST_APROBACION"] },
    modality:       { bsonType: "string", enum: ["WHITE_BOX", "GRAY_BOX", "BLACK_BOX", "MIXED"] },
    repository_url: { bsonType: ["string", "null"] },
    docker_container: { bsonType: ["string", "null"] },
    docker_image:   { bsonType: ["string", "null"] },
    source_code_path: { bsonType: ["string", "null"] },
    language:       { bsonType: ["string", "null"] },
    framework:      { bsonType: ["string", "null"] },
    has_auth:       { bsonType: "bool" },
    plugin_version: { bsonType: ["string", "null"] },
    client_os:      { bsonType: ["string", "null"] },   // "win32"/"darwin"/"Linux" — NO enum
    skill_name:     { bsonType: ["string", "null"] },
    tier_1_approved: { bsonType: "bool" },
    tier_2_approved: { bsonType: "bool" },
    // Retest
    parent_audit_id:    { bsonType: ["string", "null"] },
    retest_number:      { bsonType: "number", minimum: 0 },
    findings_to_retest: { bsonType: ["array", "null"], items: { bsonType: "string" } },
    retest_comparison:  { bsonType: ["object", "null"] },
    // Estado y fechas (STRINGS ISO-8601)
    status:       { bsonType: "string", enum: ["PENDING", "IN_PROGRESS", "PAUSED", "COMPLETED", "CANCELLED"] },
    created_at:   { bsonType: "string" },
    updated_at:   { bsonType: ["string", "null"] },
    started_at:   { bsonType: ["string", "null"] },
    completed_at: { bsonType: ["string", "null"] },
    duration_seconds: { bsonType: ["number", "null"] },
    // Resultados
    findings_count: { bsonType: "number", minimum: 0 },
    severities: {
      bsonType: "object",
      properties: {
        critical: { bsonType: "number", minimum: 0 },
        high:     { bsonType: "number", minimum: 0 },
        medium:   { bsonType: "number", minimum: 0 },
        low:      { bsonType: "number", minimum: 0 },
        info:     { bsonType: "number", minimum: 0 }
      }
    },
    triage_summary: { bsonType: ["object", "null"] },
    // Dictamen
    dictamen:               { bsonType: ["string", "null"] },
    dictamen_conditions:    { bsonType: ["string", "null"] },
    dictamen_confirmed_by:  { bsonType: ["string", "null"] },
    dictamen_confirmed_at:  { bsonType: ["string", "null"] },
    // Reporte + verificacion CI
    report_path:   { bsonType: ["string", "null"] },
    report_sha256: { bsonType: ["string", "null"] },
    // Checkpoint
    checkpoint:    { bsonType: ["object", "null"] },
    objective:     { bsonType: ["string", "null"] },
    deprecated_schema: { bsonType: "bool" }
  }
};

// --- findings ---------------------------------------------------------------

const findingSchema = {
  bsonType: "object",
  required: [
    "finding_id", "display_id", "audit_id", "owner", "source",
    "title", "severity", "evidence", "status", "analyst_review", "created_at"
  ],
  properties: {
    _id:               { bsonType: "objectId" },
    finding_id:        { bsonType: "string" },
    display_id:        { bsonType: "string" },
    audit_id:          { bsonType: "string" },
    owner:             { bsonType: "string" },
    source:            { bsonType: "string" },
    check_id:          { bsonType: ["string", "null"] },
    title:             { bsonType: "string" },
    description:       { bsonType: ["string", "null"] },
    severity:          { bsonType: "string", enum: ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] },
    category:          { bsonType: ["string", "null"] },
    owasp_id:          { bsonType: ["string", "null"] },
    owasp_category:    { bsonType: ["string", "null"] },
    affected_resource: { bsonType: ["string", "null"] },
    endpoint:          { bsonType: ["string", "null"] },
    source_file:       { bsonType: ["string", "null"] },
    evidence:          { bsonType: "object" },
    cvss_score:        { bsonType: ["number", "null"], minimum: 0, maximum: 10 },
    cvss_vector:       { bsonType: ["string", "null"] },
    cwe_id:            { bsonType: ["string", "null"] },
    detection_tool:    { bsonType: ["string", "null"] },
    confidence:        { bsonType: ["string", "null"], enum: ["confirmed", "high", "medium", "low", "suspected", null] },
    triage:            { bsonType: ["object", "null"] },
    dynamic_validation: { bsonType: ["object", "null"] },
    status:            { bsonType: "string", enum: ["OPEN", "POTENTIAL", "INFORMATIONAL", "IN_REVIEW", "ACCEPTED_RISK", "FIXED", "PARTIAL_FIX", "WONT_FIX", "FALSE_POSITIVE", "REOPENED"] },
    analyst_review: {
      bsonType: "object",
      properties: {
        decision:    { bsonType: ["string", "null"], enum: ["CONFIRMED", "OUT_OF_SCOPE", "FALSE_POSITIVE", "DOWNGRADE", "PENDING", null] },
        comment:     { bsonType: ["string", "null"] },
        reviewed_by: { bsonType: ["string", "null"] },
        reviewed_at: { bsonType: ["string", "null"] }
      }
    },
    parent_finding_id:  { bsonType: ["string", "null"] },
    retest_status:      { bsonType: ["string", "null"], enum: ["FIXED", "PARTIAL", "UNFIXED", "REGRESSED", null] },
    retest_notes:       { bsonType: ["string", "null"] },
    created_at:         { bsonType: "string" },
    updated_at:         { bsonType: ["string", "null"] },
    deprecated_schema:  { bsonType: "bool" }
  }
};

// --- events -----------------------------------------------------------------
// event_type SIN enum a proposito (ver cabecera). level_log SI restringido.

const eventSchema = {
  bsonType: "object",
  required: ["event_type", "timestamp", "level_log"],
  properties: {
    _id:          { bsonType: "objectId" },
    audit_id:     { bsonType: ["string", "null"] },
    owner:        { bsonType: ["string", "null"] },
    project_name: { bsonType: ["string", "null"] },
    event_type:   { bsonType: "string" },
    level_log:    { bsonType: "string", enum: ["INFO", "WARNING", "ERROR"] },
    timestamp:    { bsonType: "string" },
    message:      { bsonType: ["string", "null"] },
    context:      { bsonType: ["object", "null"] },
    deprecated_schema: { bsonType: "bool" }
  }
};

// --- llm_attack_sessions ----------------------------------------------------

const llmSessionSchema = {
  bsonType: "object",
  required: ["session_id", "audit_id", "owner", "created_at"],
  properties: {
    _id:        { bsonType: "objectId" },
    session_id: { bsonType: "string" },
    audit_id:   { bsonType: "string" },
    owner:      { bsonType: "string" },
    channel:    { bsonType: ["string", "null"] },
    mode:       { bsonType: ["string", "null"] },
    language:   { bsonType: ["string", "null"] },
    status:     { bsonType: ["string", "null"], enum: ["IN_PROGRESS", "COMPLETED", "PAUSED", "CANCELLED", null] },
    started_at: { bsonType: ["string", "null"] },
    ended_at:   { bsonType: ["string", "null"] },
    created_at: { bsonType: "string" },
    updated_at: { bsonType: ["string", "null"] },
    deprecated_schema: { bsonType: "bool" }
  }
};

// --- aplicar ----------------------------------------------------------------

print("\nAplicando validators en: " + DB.getName());
print("---------------------------------------------");
applyValidator("audit_runs",          auditRunSchema);
applyValidator("findings",            findingSchema);
applyValidator("events",              eventSchema);
applyValidator("llm_attack_sessions", llmSessionSchema);
print("---------------------------------------------");
print("Listo. validationLevel=moderate, validationAction=error\n");
