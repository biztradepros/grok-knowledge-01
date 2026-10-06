-- DREAM DATA FACTORY KERNEL — Message Ledger + Job + Outbox + Wait (LOT-002 prototype)
-- Target: PostgreSQL 15+ / Supabase. Vertical-free. No Make/n8n/Inngest specifics.
--
-- Contract every runtime adapter (Make, n8n, Durable engine, Code worker) must obey:
--   R1  Adapters never write tables. They call k_append_message / k_ack_event only.
--   R2  Every inbound call carries an idempotency_key. Same key => same message, no side effect.
--   R3  Every resume/answer carries the job version it was issued against (fencing token).
--       A stale answer is STORED (never lost) but never ACTS.
--   R4  Adapters hold no business state. Anything they "remember" must be rebuildable
--       from k_job + k_message + k_event + k_wait.
--   R5  Outbound work is an outbox row. Unacked rows are re-driven by k_sweep (kernel owns retry).

create table k_project (
  id   text primary key,                         -- 'DAEHEUNG', 'RADAR', 'PRODUCT-OPS'
  vertical text not null check (vertical in ('CONTENT','PRODUCT_OPS','DEVELOPMENT','KERNEL'))
);

create table k_context (                        -- a conversation/research context, survives room/AI changes
  id   text primary key,                         -- 'CTX-LOT002'
  project_id text not null references k_project(id),
  title text not null
);

create type k_job_state as enum ('OPEN','WAITING_AI','WAITING_HUMAN','STALLED','DONE','FAILED','CANCELLED');

create table k_job (
  id         text primary key,                   -- 'LOT-002'
  context_id text not null references k_context(id),
  kind       text not null,                      -- 'RESEARCH','SCENARIO_REVIEW','SOURCING','MAG_ISSUE'
  room       text not null,                      -- 'ROOM-21' (attribute, not identity)
  state      k_job_state not null default 'OPEN',
  version    int not null default 1,             -- bumps on every state change = fencing token
  updated_at timestamptz not null default now()
);

create table k_message (                         -- canonical conversation memory, append-only
  id              bigserial primary key,
  code            text unique,                   -- 'LOT002-M004' (human-readable)
  job_id          text not null references k_job(id),
  parent_id       bigint references k_message(id),
  sender          text not null,                 -- 'HQ','ROOM21','GEMINI','CLAUDE','GROK','HUMAN:<id>'
  recipient       text not null,
  type            text not null check (type in ('REQUEST','CLAIM','CHALLENGE','RESPONSE','EVIDENCE_REQUEST',
                                                'VERIFY','RESULT','COACH','STOP','APPROVAL_REQUEST','HUMAN_ANSWER','SYNTHESIS','NOTE')),
  body            text not null,
  artifact_ptr    text,                          -- 'git:drafts/dream-lot-002/REPORT.md@<sha>'
  provider_ref    text,                          -- provider response/message id, if any
  idempotency_key text not null unique,          -- R2
  job_version_seen int,                          -- R3 fencing token presented by sender
  disposition     text not null default 'APPLIED' check (disposition in ('APPLIED','STALE','LATE')),
  created_at      timestamptz not null default now()
);
create unique index k_message_provider_once on k_message(job_id, provider_ref) where provider_ref is not null;

create table k_event (                           -- event log + transactional outbox in one table
  id          bigserial primary key,
  job_id      text references k_job(id),
  type        text not null,                     -- 'dispatch.ai','notify.human','room.changed','job.state'
  payload     jsonb not null default '{}',
  needs_dispatch boolean not null default false, -- true = outbox row
  attempts    int not null default 0,
  claimed_at  timestamptz,
  claimed_by  text,                              -- 'make:scenario-123','n8n:exec-9','worker:1'
  acked_at    timestamptz,
  runtime_ref text,                              -- external execution id for tracing
  created_at  timestamptz not null default now()
);

create table k_provider_session (               -- provider threads are CACHE, not memory
  id         bigserial primary key,
  job_id     text not null references k_job(id),
  provider   text not null,                      -- 'gemini','claude','grok','gpt'
  thread_ref text not null,
  status     text not null default 'ALIVE' check (status in ('ALIVE','LOST','CLOSED')),
  opened_at  timestamptz not null default now()
);

create table k_wait (
  job_id      text primary key references k_job(id),
  kind        text not null check (kind in ('AI','HUMAN')),
  deadline    timestamptz not null,
  fence       int not null,                      -- job.version when the wait was opened
  expired_at  timestamptz
);

-- Calc runs and decisions (envelope only; engines are vertical-specific)
create table k_engine (version text primary key, active boolean not null default false);
create table k_calc_run (
  id text primary key, engine_version text not null references k_engine(version),
  input_hash char(64) not null, scenario_id text not null
);
create table k_scenario (id text primary key, project_id text not null references k_project(id), superseded_by text references k_scenario(id));
create table k_decision (id text primary key, job_id text references k_job(id), calc_run_id text not null references k_calc_run(id));

create view k_stale_decisions as
  select d.id as decision_id, r.engine_version as decided_on, e.version as active_engine
  from k_decision d join k_calc_run r on r.id = d.calc_run_id
  join k_engine e on e.active
  where r.engine_version <> e.version;

-- ---------------------------------------------------------------------------
-- k_append_message: the ONLY write path for adapters (R1-R3).
create or replace function k_append_message(
  p_idem text, p_job text, p_parent bigint, p_sender text, p_recipient text,
  p_type text, p_body text, p_fence int default null, p_provider_ref text default null,
  p_code text default null, p_artifact text default null
) returns bigint language plpgsql as $$
declare
  v_id bigint; v_job k_job; v_disp text := 'APPLIED'; v_next k_job_state;
begin
  select id into v_id from k_message where idempotency_key = p_idem;
  if found then return v_id; end if;                                  -- R2: duplicate delivery
  if p_provider_ref is not null then
    select id into v_id from k_message where job_id = p_job and provider_ref = p_provider_ref;
    if found then return v_id; end if;                                -- same provider result, new key
  end if;

  select * into v_job from k_job where id = p_job for update;
  if not found then raise exception 'unknown job %', p_job; end if;

  if p_fence is not null and p_fence <> v_job.version then
    v_disp := case when v_job.state = 'STALLED' then 'LATE' else 'STALE' end;   -- R3: store, do not act
  end if;

  insert into k_message(code, job_id, parent_id, sender, recipient, type, body, artifact_ptr,
                        provider_ref, idempotency_key, job_version_seen, disposition)
  values (p_code, p_job, p_parent, p_sender, p_recipient, p_type, p_body, p_artifact,
          p_provider_ref, p_idem, p_fence, v_disp)
  returning id into v_id;

  if v_disp = 'APPLIED' then
    v_next := case p_type
      when 'REQUEST'          then 'WAITING_AI'
      when 'CHALLENGE'        then 'WAITING_AI'
      when 'VERIFY'           then 'WAITING_AI'
      when 'APPROVAL_REQUEST' then 'WAITING_HUMAN'
      when 'RESULT'           then 'OPEN'
      when 'RESPONSE'         then 'OPEN'
      when 'HUMAN_ANSWER'     then 'OPEN'
      when 'STOP'             then 'DONE'
      else null end;
    if v_next is not null and v_next <> v_job.state then
      update k_job set state = v_next, version = version + 1, updated_at = now() where id = p_job;
      insert into k_event(job_id, type, payload) values (p_job, 'job.state',
        jsonb_build_object('from', v_job.state, 'to', v_next, 'message_id', v_id));
    end if;
    if p_type in ('REQUEST','CHALLENGE','VERIFY') then                 -- outbox: same transaction
      insert into k_event(job_id, type, payload, needs_dispatch)
      values (p_job, 'dispatch.ai', jsonb_build_object('message_id', v_id, 'to', p_recipient), true);
    elsif p_type = 'APPROVAL_REQUEST' then
      insert into k_event(job_id, type, payload, needs_dispatch)
      values (p_job, 'notify.human', jsonb_build_object('message_id', v_id), true);
    end if;
    if p_type in ('RESULT','RESPONSE','HUMAN_ANSWER') then
      delete from k_wait where job_id = p_job;
    end if;
  else
    insert into k_event(job_id, type, payload) values (p_job, 'message.'||lower(v_disp),
      jsonb_build_object('message_id', v_id, 'fence', p_fence, 'job_version', v_job.version));
  end if;
  return v_id;
end $$;

-- Adapters claim outbox rows by event type (an AI dispatcher never grabs a human notification).
-- SKIP LOCKED => several adapters (Make, n8n, code worker) can drain side by side without double claims.
create or replace function k_claim(p_worker text, p_types text[], p_limit int default 10)
returns setof k_event language sql as $$
  update k_event set claimed_at = now(), claimed_by = p_worker, attempts = attempts + 1
  where id in (select id from k_event
               where needs_dispatch and acked_at is null and claimed_at is null and type = any(p_types)
               order by id for update skip locked limit p_limit)
  returning *;
$$;

create or replace function k_ack(p_event bigint, p_runtime_ref text) returns void language sql as $$
  update k_event set acked_at = now(), runtime_ref = p_runtime_ref where id = p_event and acked_at is null;
$$;

create or replace function k_open_wait(p_job text, p_kind text, p_deadline timestamptz) returns void language sql as $$
  insert into k_wait(job_id, kind, deadline, fence)
  select id, p_kind, p_deadline, version from k_job where id = p_job
  on conflict (job_id) do update set kind = excluded.kind, deadline = excluded.deadline, fence = excluded.fence, expired_at = null;
$$;

-- Kernel-owned retry + timeout sweeper (R5). Run every minute (pg_cron / scheduler / n8n cron — any).
create or replace function k_sweep(p_now timestamptz, p_claim_timeout interval, p_max_attempts int default 3)
returns jsonb language plpgsql as $$
declare v_requeued int; v_dead int; v_expired int;
begin
  update k_event set claimed_at = null, claimed_by = null
  where needs_dispatch and acked_at is null and claimed_at < p_now - p_claim_timeout and attempts < p_max_attempts;
  get diagnostics v_requeued = row_count;

  with dead as (
    update k_event set needs_dispatch = false
    where needs_dispatch and acked_at is null and claimed_at < p_now - p_claim_timeout and attempts >= p_max_attempts
    returning job_id)
  insert into k_event(job_id, type, payload, needs_dispatch)
  select job_id, 'escalate.dispatch_failed', '{}', true from dead;
  get diagnostics v_dead = row_count;

  with exp as (
    update k_wait set expired_at = p_now where expired_at is null and deadline < p_now returning job_id)
  , st as (
    update k_job j set state = 'STALLED', version = version + 1, updated_at = p_now
    from exp where j.id = exp.job_id returning j.id)
  insert into k_event(job_id, type, payload, needs_dispatch)
  select id, 'escalate.wait_expired', '{}', true from st;
  get diagnostics v_expired = row_count;

  return jsonb_build_object('requeued', v_requeued, 'dead', v_dead, 'expired', v_expired);
end $$;

-- ROOM change: identity (job id) is stable, room is an attribute with history.
create or replace function k_move_room(p_job text, p_room text) returns void language sql as $$
  insert into k_event(job_id, type, payload)
    select id, 'room.changed', jsonb_build_object('from', room, 'to', p_room) from k_job where id = p_job;
  update k_job set room = p_room, updated_at = now() where id = p_job;
$$;

-- SAME JOB recovery: mark the provider thread lost, return a Context Capsule compiled from the ledger.
create or replace function k_rehydrate(p_job text, p_provider text, p_last int default 6) returns jsonb language plpgsql as $$
declare v jsonb;
begin
  update k_provider_session set status = 'LOST' where job_id = p_job and provider = p_provider and status = 'ALIVE';
  select jsonb_build_object(
    'job', to_jsonb(j) - 'updated_at',
    'capsule_built_from_message_ids', (select jsonb_agg(id order by id) from (select id from k_message where job_id = p_job and disposition = 'APPLIED' order by id desc limit p_last) t),
    'recent', (select jsonb_agg(jsonb_build_object('id', id, 'from', sender, 'to', recipient, 'type', type, 'body', left(body, 400)) order by id)
               from (select * from k_message where job_id = p_job and disposition = 'APPLIED' order by id desc limit p_last) t),
    'open_challenges', (select coalesce(jsonb_agg(m.id), '[]') from k_message m where m.job_id = p_job and m.type = 'CHALLENGE'
                        and not exists (select 1 from k_message r where r.parent_id = m.id and r.type in ('RESPONSE','RESULT'))),
    'calc_runs', (select coalesce(jsonb_agg(d.calc_run_id), '[]') from k_decision d where d.job_id = p_job))
  into v from k_job j where j.id = p_job;
  return v;
end $$;

-- Opening work on a superseded scenario requires an explicit fork.
create or replace function k_start_scenario_job(p_job text, p_ctx text, p_scenario text, p_fork boolean default false)
returns text language plpgsql as $$
declare v_sup text;
begin
  select superseded_by into v_sup from k_scenario where id = p_scenario;
  if v_sup is not null and not p_fork then
    raise exception 'scenario % is superseded by %; open read-only or fork explicitly', p_scenario, v_sup;
  end if;
  insert into k_job(id, context_id, kind, room) values (p_job, p_ctx, 'SCENARIO_REVIEW', 'ROOM-DEV');
  return p_job;
end $$;
