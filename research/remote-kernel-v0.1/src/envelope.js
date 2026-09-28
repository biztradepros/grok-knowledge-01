import { PROTOCOL, ID_PATTERN, AUTHORITY_LEVELS, MAX_TIMEOUT_MS } from './constants.js';
import { hashOf } from './canonical.js';

/**
 * Command envelope (remote.v0.1). See schema/command.v0.1.schema.json.
 * @typedef {object} RemoteCommand
 * @property {'remote.command'} kind
 * @property {'remote.v0.1'} protocol
 * @property {string} command_id        unique per send attempt chain; RESULT looks results up by it
 * @property {string} idempotency_key   same key + same payload => stored result replayed
 * @property {string} site_id           target site; a mismatch is rejected, never forwarded
 * @property {string} [session_id]      required for every verb except IDENTIFY
 * @property {string} verb
 * @property {object} [args]
 * @property {number} [expect_seq]      required for STEP: optimistic lock on the twin
 * @property {number} [timeout_ms]
 * @property {string} issued_by         HQ operator or agent id, kept in lineage
 * @property {{retry_of?: string, parent_result_hash?: string}} [lineage]
 * @property {string} [sent_at]         transport metadata, excluded from the command hash
 */

export function validateCommand(cmd) {
  const errors = [];
  if (!cmd || typeof cmd !== 'object' || Array.isArray(cmd)) return ['command must be an object'];
  if (cmd.kind !== 'remote.command') errors.push('kind must be "remote.command"');
  if (cmd.protocol !== PROTOCOL) errors.push(`protocol must be "${PROTOCOL}"`);
  for (const f of ['command_id', 'idempotency_key', 'site_id', 'issued_by']) {
    if (typeof cmd[f] !== 'string' || !ID_PATTERN.test(cmd[f])) errors.push(`${f} must match ${ID_PATTERN}`);
  }
  if (typeof cmd.verb !== 'string' || !/^[A-Z][A-Z0-9_]{1,40}$/.test(cmd.verb)) errors.push('verb must be UPPER_SNAKE');
  if (cmd.verb !== 'IDENTIFY' && (typeof cmd.session_id !== 'string' || !ID_PATTERN.test(cmd.session_id))) {
    errors.push('session_id is required after IDENTIFY');
  }
  if (cmd.args !== undefined && (typeof cmd.args !== 'object' || cmd.args === null || Array.isArray(cmd.args))) {
    errors.push('args must be an object');
  }
  if (cmd.verb === 'STEP' && !Number.isInteger(cmd.expect_seq)) errors.push('STEP requires integer expect_seq');
  if (cmd.timeout_ms !== undefined && !(Number.isInteger(cmd.timeout_ms) && cmd.timeout_ms > 0 && cmd.timeout_ms <= MAX_TIMEOUT_MS)) {
    errors.push(`timeout_ms must be 1..${MAX_TIMEOUT_MS}`);
  }
  if (cmd.verb === 'IDENTIFY' && cmd.args?.requested_authority !== undefined &&
      !AUTHORITY_LEVELS.includes(cmd.args.requested_authority)) {
    errors.push('requested_authority must be R0, R1 or R2');
  }
  try { hashOf(cmd); } catch (e) { errors.push(`not canonical JSON: ${e.message}`); }
  return errors;
}

// What makes two sends "the same request". Session and transport fields are excluded so a
// command re-sent after a reconnect (new session) still replays instead of re-executing.
export const commandHash = (cmd) => hashOf({
  site_id: cmd.site_id,
  verb: cmd.verb,
  args: cmd.args ?? {},
  expect_seq: cmd.expect_seq ?? null,
  issued_by: cmd.issued_by,
});

// Result hash excludes wall-clock timing and the replay marker, so a replayed or re-exported
// result verifies against the hash recorded when it was first produced.
export function resultHash(result) {
  const { result_hash, timing, replayed, ...hashed } = result;
  return hashOf(hashed);
}

let hqCounter = 0;
// HQ-side convenience. HQ builds envelopes; it never imports site engines or adapters.
export function makeCommand({ site_id, session_id, verb, args = {}, expect_seq, issued_by = 'hq.operator',
  idempotency_key, command_id, timeout_ms, lineage }) {
  hqCounter += 1;
  const id = command_id ?? `cmd.${Date.now().toString(36)}.${hqCounter}`;
  return {
    kind: 'remote.command',
    protocol: PROTOCOL,
    command_id: id,
    idempotency_key: idempotency_key ?? `idem.${id}`,
    site_id,
    ...(session_id ? { session_id } : {}),
    verb,
    args,
    ...(expect_seq !== undefined ? { expect_seq } : {}),
    ...(timeout_ms !== undefined ? { timeout_ms } : {}),
    issued_by,
    ...(lineage ? { lineage } : {}),
  };
}
