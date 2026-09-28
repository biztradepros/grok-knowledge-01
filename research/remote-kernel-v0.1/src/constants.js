// Remote Kernel v0.1 — protocol constants.
// Everything a site or HQ needs to agree on lives here; nothing site-specific.

export const PROTOCOL = 'remote.v0.1';
export const KERNEL_VERSION = '0.1.0';

// Closed verb set. Anything else must be a site-declared action (and v0.1 never executes those).
export const KERNEL_VERBS = Object.freeze(['IDENTIFY', 'INSPECT', 'STEP', 'RESULT']);

export const STATUS = Object.freeze({
  OK: 'OK',
  HOLD: 'HOLD',
  REJECTED: 'COMMAND_REJECTED',
  FAILED: 'FAILED',
  TIMEOUT: 'TIMEOUT',
});

// R0 = read only. R1 = digital twin mutation only. R2 = real state / external effect.
export const AUTHORITY_LEVELS = Object.freeze(['R0', 'R1', 'R2']);
export const KERNEL_MAX_AUTHORITY = 'R1'; // v0.1 never grants R2, whatever the site declares.

export const VERB_AUTHORITY = Object.freeze({
  IDENTIFY: 'R0',
  INSPECT: 'R0',
  RESULT: 'R0',
  STEP: 'R1',
});

export const REASON = Object.freeze({
  SCHEMA_INVALID: 'SCHEMA_INVALID',
  SITE_MISMATCH: 'SITE_MISMATCH',
  UNKNOWN_VERB: 'UNKNOWN_VERB',
  NO_SESSION: 'NO_SESSION',
  SESSION_EXPIRED: 'SESSION_EXPIRED',
  AUTHORITY_INSUFFICIENT: 'AUTHORITY_INSUFFICIENT',
  HUMAN_GATE_REQUIRED: 'HUMAN_GATE_REQUIRED',
  R2_DISABLED: 'R2_DISABLED',
  IDEMPOTENCY_CONFLICT: 'IDEMPOTENCY_CONFLICT',
  STALE_TWIN: 'STALE_TWIN',
  TERMINAL_STAGE: 'TERMINAL_STAGE',
  ILLEGAL_TRANSITION: 'ILLEGAL_TRANSITION',
  NOT_FOUND: 'NOT_FOUND',
  ACTION_NOT_EXECUTABLE: 'ACTION_NOT_EXECUTABLE',
  ADAPTER_ERROR: 'ADAPTER_ERROR',
  ADAPTER_TIMEOUT: 'ADAPTER_TIMEOUT',
  REAL_STATE_CHANGED: 'REAL_STATE_CHANGED',
  SIDE_EFFECT_ATTEMPTED: 'SIDE_EFFECT_ATTEMPTED',
  LEAK_BLOCKED: 'LEAK_BLOCKED',
  KERNEL_ERROR: 'KERNEL_ERROR',
});

// Keys that must never cross the site boundary in a result or a twin fact (9 SKILL/AI guard).
export const FORBIDDEN_KEYS = Object.freeze([
  'prompt', 'system_prompt', 'messages', 'model', 'model_id', 'temperature',
  'api_key', 'apikey', 'secret', 'token', 'password', 'credential', 'credentials',
]);

export const ID_PATTERN = /^[A-Za-z0-9._:-]{4,128}$/;
export const DEFAULT_TIMEOUT_MS = 5000;
export const MAX_TIMEOUT_MS = 30000;
export const DEFAULT_SESSION_TTL_MS = 15 * 60 * 1000;

export const authorityRank = (level) => AUTHORITY_LEVELS.indexOf(level);
export const minAuthority = (...levels) =>
  levels.reduce((a, b) => (authorityRank(a) <= authorityRank(b) ? a : b));
