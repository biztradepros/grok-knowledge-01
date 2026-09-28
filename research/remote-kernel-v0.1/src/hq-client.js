import { makeCommand } from './envelope.js';
import { STATUS } from './constants.js';

/**
 * HQ side. Knows envelopes and a transport per site, nothing else: no adapter, no engine,
 * no stage semantics. `transport(cmd)` may throw (disconnect); that is surfaced as
 * DELIVERY_UNKNOWN and never turned into a fresh execution.
 *
 * Retry rule: HQ may re-deliver the *identical* envelope (same idempotency_key) — the site
 * replays the stored result, so execution stays at-most-once. HQ must never mint a new key for
 * the same intent without `lineage.retry_of`; `reissue()` is the only way to do that.
 */
export function createHqClient({ transports, issued_by = 'hq.operator' }) {
  const sessions = new Map();   // site_id -> { session_id, granted, seq }
  const outbox = new Map();     // command_id -> envelope (for re-delivery)

  async function send(site_id, cmd) {
    outbox.set(cmd.command_id, cmd);
    const transport = transports[site_id];
    if (!transport) return { status: 'DELIVERY_UNKNOWN', command_id: cmd.command_id, error: 'no transport' };
    try {
      const res = await transport(cmd);
      const s = sessions.get(site_id);
      if (s && res.twin) s.seq = res.twin.seq_after;
      return res;
    } catch (e) {
      return { status: 'DELIVERY_UNKNOWN', command_id: cmd.command_id, error: String(e?.message ?? e) };
    }
  }

  const sessionOf = (site_id) => sessions.get(site_id)?.session_id;

  return {
    async identify(site_id, requested_authority = 'R1') {
      const res = await send(site_id, makeCommand({ site_id, verb: 'IDENTIFY', args: { requested_authority }, issued_by }));
      if (res.status === STATUS.OK) {
        sessions.set(site_id, {
          session_id: res.session_id,
          granted: res.data.session.granted_authority,
          seq: res.data.twin.seq,
          capabilities: res.data.capabilities,
        });
      }
      return res;
    },
    inspect: (site_id, view = 'twin') =>
      send(site_id, makeCommand({ site_id, session_id: sessionOf(site_id), verb: 'INSPECT', args: { view }, issued_by })),
    explainHold: (site_id) =>
      send(site_id, makeCommand({ site_id, session_id: sessionOf(site_id), verb: 'INSPECT', args: { view: 'hold' }, issued_by })),
    step: (site_id, { expect_seq, timeout_ms } = {}) =>
      send(site_id, makeCommand({
        site_id, session_id: sessionOf(site_id), verb: 'STEP', issued_by, timeout_ms,
        expect_seq: expect_seq ?? sessions.get(site_id)?.seq ?? 0,
      })),
    result: (site_id, command_id) =>
      send(site_id, makeCommand({ site_id, session_id: sessionOf(site_id), verb: 'RESULT', args: { command_id }, issued_by })),
    // Any verb, e.g. PUBLISH. The kernel decides; HQ does not pre-filter, so refusals are evidenced.
    command: (site_id, verb, args = {}) =>
      send(site_id, makeCommand({ site_id, session_id: sessionOf(site_id), verb, args, issued_by })),
    // Identical envelope, new session binding. Safe: same key => replay, never a second execution.
    redeliver(command_id) {
      const cmd = outbox.get(command_id);
      return send(cmd.site_id, { ...cmd, session_id: sessionOf(cmd.site_id) ?? cmd.session_id });
    },
    // Deliberate new attempt after TIMEOUT/FAILED: new key, lineage points at the old command.
    reissue(command_id, overrides = {}) {
      const old = outbox.get(command_id);
      const cmd = makeCommand({
        site_id: old.site_id, session_id: sessionOf(old.site_id), verb: old.verb, args: old.args, issued_by,
        expect_seq: old.verb === 'STEP' ? sessions.get(old.site_id)?.seq : undefined,
        lineage: { retry_of: old.command_id }, ...overrides,
      });
      return send(cmd.site_id, cmd);
    },
    // Fan-out with failure isolation: one site timing out or throwing never blocks the others.
    async broadcast(site_ids, fn) {
      const settled = await Promise.allSettled(site_ids.map((id) => fn(id)));
      return Object.fromEntries(site_ids.map((id, i) => [id, settled[i].status === 'fulfilled'
        ? settled[i].value
        : { status: 'DELIVERY_UNKNOWN', error: String(settled[i].reason) }]));
    },
    session: (site_id) => sessions.get(site_id) ?? null,
    forget(site_id) { sessions.delete(site_id); },
  };
}
