-- LOT-002 §14 failure simulations against kernel/ledger.sql.
-- "Make" and "n8n" below are SIMULATED adapter names calling the kernel contract.
-- This proves kernel semantics, NOT Make/n8n behaviour (that is ROOM-22's LIVE TEST).
\set ON_ERROR_STOP 1
set client_min_messages = notice;

insert into k_project values ('DAEHEUNG','DEVELOPMENT'), ('KERNEL','KERNEL');
insert into k_context values ('CTX-LOT002','KERNEL','LOT-002 runtime research');
insert into k_job(id, context_id, kind, room) values ('LOT-002','CTX-LOT002','RESEARCH','ROOM-21');

-- F01 AI provider timeout -------------------------------------------------------
do $$
declare e k_event; r jsonb; n int;
begin
  perform k_append_message('lot002-m003','LOT-002',null,'HQ','CLAUDE','REQUEST','LOT-002 work order', p_code => 'LOT002-M003');
  select * into e from k_claim('make:dispatcher', array['dispatch.ai'], 1);
  assert e.type = 'dispatch.ai' and e.payload->>'to' = 'CLAUDE', 'outbox row created with the REQUEST';
  -- Make sent it, provider never answered, no ack.
  r := k_sweep(now() + interval '10 min', interval '5 min');
  assert (r->>'requeued')::int = 1, 'kernel re-queues the unacked dispatch';
  select * into e from k_claim('n8n:fallback', array['dispatch.ai'], 1);           -- a DIFFERENT adapter may pick it up
  assert e.attempts = 2 and e.claimed_by = 'n8n:fallback', 'second attempt by another adapter';
  perform k_sweep(now() + interval '20 min', interval '5 min');
  perform k_claim('make:dispatcher', array['dispatch.ai'], 1);
  r := k_sweep(now() + interval '30 min', interval '5 min', 3);
  assert (r->>'dead')::int = 1, 'after 3 attempts the dispatch is escalated, not retried forever';
  select count(*) into n from k_event where type = 'escalate.dispatch_failed';
  assert n = 1;
  select count(*) into n from k_claim('make:notifier', array['escalate.dispatch_failed','notify.human'], 5);
  assert n = 1, 'escalation is drained by the notify adapter, not the AI dispatcher';
  raise notice 'F01 PASS provider timeout -> kernel retry x3 -> escalate (owner: k_sweep)';
end $$;

-- F02 Duplicate webhook -----------------------------------------------------------
do $$
declare a bigint; b bigint; n int;
begin
  a := k_append_message('hook:gemini:777','LOT-002',null,'GEMINI','ROOM21','RESULT','GEMINI-002 report', p_code => 'LOT002-M002');
  b := k_append_message('hook:gemini:777','LOT-002',null,'GEMINI','ROOM21','RESULT','GEMINI-002 report');
  select count(*) into n from k_message where idempotency_key = 'hook:gemini:777';
  assert a = b and n = 1, 'same idempotency key -> same message';
  raise notice 'F02 PASS duplicate webhook -> 1 message (owner: ledger unique key)';
end $$;

-- F03 Make succeeds but Ledger write fails ----------------------------------------
do $$
declare ev bigint; e k_event; n int;
begin
  perform k_append_message('lot002-m005','LOT-002',null,'HQ','GROK','REQUEST','LOT-002 work order', p_code => 'LOT002-M005');
  select * into e from k_claim('make:dispatcher', array['dispatch.ai'], 1); ev := e.id;
  -- Make delivered to Grok and got an answer, but its k_append_message(RESULT) call failed. No ack either.
  perform k_sweep(now() + interval '10 min', interval '5 min');
  select * into e from k_claim('n8n:fallback', array['dispatch.ai'], 1);
  assert e.id = ev, 'the same outbox row is re-driven';
  assert e.payload->>'to' = 'GROK', 'it is the GROK dispatch, not some other outbox row';
  -- Retry produces a result; then Make's delayed write ALSO lands. Both use key result:<event_id>.
  perform k_append_message('result:'||ev,'LOT-002',null,'GROK','ROOM21','RESULT','GROK-002 (retry)', p_provider_ref => 'grok-resp-B');
  perform k_append_message('result:'||ev,'LOT-002',null,'GROK','ROOM21','RESULT','GROK-002 (late original)', p_provider_ref => 'grok-resp-A');
  perform k_ack(ev, 'n8n-exec-41');
  select count(*) into n from k_message where idempotency_key = 'result:'||ev;
  assert n = 1, 'exactly one RESULT despite two deliveries';
  raise notice 'F03 PASS adapter success + ledger write failure -> re-drive, first result wins (owner: k_sweep + idempotency key)';
end $$;

-- F04 Ledger succeeds but AI dispatch fails --------------------------------------
do $$
declare n int; e k_event;
begin
  perform k_append_message('lot002-m001','LOT-002',null,'HQ','GEMINI','REQUEST','LOT-002 work order', p_code => 'LOT002-M001');
  -- Every adapter is down. Nothing claims. Nothing is lost:
  select count(*) into n from k_event where needs_dispatch and acked_at is null and claimed_at is null and type = 'dispatch.ai';
  assert n >= 1, 'pending dispatch is visible in the outbox';
  select * into e from k_claim('worker:code', array['dispatch.ai'], 5);             -- adapter recovers later
  assert e.id is not null;
  raise notice 'F04 PASS ledger ok + dispatch down -> outbox row waits, any adapter drains later (owner: outbox)';
end $$;

-- F05 AI returns RESULT twice (different delivery keys, same provider response) ---
do $$
declare a bigint; b bigint; n int;
begin
  a := k_append_message('make-run-1','LOT-002',null,'GEMINI','ROOM21','RESULT','r', p_provider_ref => 'gem-resp-9');
  b := k_append_message('make-run-2','LOT-002',null,'GEMINI','ROOM21','RESULT','r', p_provider_ref => 'gem-resp-9');
  select count(*) into n from k_message where provider_ref = 'gem-resp-9';
  assert a = b and n = 1;
  raise notice 'F05 PASS RESULT twice -> deduped by (job, provider_ref)';
end $$;

-- F06 ROOM changes -----------------------------------------------------------------
do $$
declare n int; r text;
begin
  perform k_move_room('LOT-002','ROOM-22');
  perform k_append_message('room22-note-1','LOT-002',null,'ROOM22','HQ','NOTE','live test plan accepted');
  select room into r from k_job where id = 'LOT-002';
  select count(*) into n from k_event where job_id = 'LOT-002' and type = 'room.changed';
  assert r = 'ROOM-22' and n = 1;
  select count(*) into n from k_message where job_id = 'LOT-002';
  assert n >= 6, 'history stays on the same job id across rooms';
  perform k_move_room('LOT-002','ROOM-21');
  raise notice 'F06 PASS room change -> same JOB id, room is an attribute + event';
end $$;

-- F07 AI Thread lost -> SAME JOB recovery ------------------------------------------
do $$
declare cap jsonb; ch bigint; n int;
begin
  insert into k_provider_session(job_id, provider, thread_ref) values ('LOT-002','claude','thread-abc');
  ch := k_append_message('lot002-chal-1','LOT-002',null,'ROOM21','CLAUDE','CHALLENGE','Is Make+n8n split-brain under ledger ownership?');
  cap := k_rehydrate('LOT-002','claude');
  select count(*) into n from k_provider_session where thread_ref = 'thread-abc' and status = 'LOST';
  assert n = 1, 'old thread marked LOST';
  assert cap->'open_challenges' @> to_jsonb(ch), 'capsule carries the unanswered challenge';
  assert jsonb_array_length(cap->'recent') > 0;
  insert into k_provider_session(job_id, provider, thread_ref) values ('LOT-002','claude','thread-new');
  perform k_append_message('lot002-resp-1','LOT-002',ch,'CLAUDE','ROOM21','RESPONSE','answer in new thread', p_provider_ref => 'claude-resp-1');
  select count(*) into n from k_message where parent_id = ch;
  assert n = 1, 'answer threads under the original challenge in the SAME job';
  raise notice 'F07 PASS thread lost -> capsule from ledger -> new thread, same JOB/parent chain';
end $$;

-- F08 Human answers after 3 days -----------------------------------------------------
do $$
declare v0 int; m bigint; s k_job_state; d text;
begin
  perform k_append_message('lot002-appr-1','LOT-002',null,'ROOM21','HQ','APPROVAL_REQUEST','Approve TEST LOT-003 for ROOM-22?');
  select version into v0 from k_job where id = 'LOT-002';
  perform k_open_wait('LOT-002','HUMAN', now() + interval '2 days');
  perform k_sweep(now() + interval '2 days 1 hour', interval '5 min');
  select state into s from k_job where id = 'LOT-002';
  assert s = 'STALLED', 'wait expired -> STALLED + escalation';
  m := k_append_message('hq-answer-1','LOT-002',null,'HQ','ROOM21','HUMAN_ANSWER','APPROVED', p_fence => v0);
  select disposition into d from k_message where id = m;
  select state into s from k_job where id = 'LOT-002';
  assert d = 'LATE' and s = 'STALLED', 'late answer is STORED but does not auto-resume';
  -- Operator re-asks against the current version; HQ re-confirms -> applies.
  perform k_append_message('lot002-appr-2','LOT-002',null,'ROOM21','HQ','APPROVAL_REQUEST','Re-confirm (prior answer was late)');
  select version into v0 from k_job where id = 'LOT-002';
  perform k_append_message('hq-answer-2','LOT-002',null,'HQ','ROOM21','HUMAN_ANSWER','APPROVED', p_fence => v0);
  select state into s from k_job where id = 'LOT-002';
  assert s = 'OPEN';
  raise notice 'F08 PASS 3-day-late human answer -> kept as LATE, re-confirm required (owner: fencing token)';
end $$;

-- F09 Calc Engine version changes ------------------------------------------------------
do $$
declare n int;
begin
  insert into k_engine values ('daeheung-calc@0.1.0', true);
  insert into k_scenario values ('KM36-3F','DAEHEUNG',null);
  insert into k_calc_run values ('run-1','daeheung-calc@0.1.0', repeat('a',64), 'KM36-3F');
  insert into k_decision values ('dec-1','LOT-002','run-1');
  select count(*) into n from k_stale_decisions; assert n = 0;
  update k_engine set active = false;
  insert into k_engine values ('daeheung-calc@0.2.0', true);
  select count(*) into n from k_stale_decisions where decision_id = 'dec-1';
  assert n = 1, 'decision made on old engine is surfaced for re-run';
  raise notice 'F09 PASS engine change -> old runs immutable, decisions flagged stale';
end $$;

-- F10 Old Scenario accidentally reopened -----------------------------------------------
do $$
begin
  insert into k_scenario values ('BASE-132-v2','DAEHEUNG',null), ('BASE-132-v1','DAEHEUNG','BASE-132-v2');
  begin
    perform k_start_scenario_job('JOB-OLD','CTX-LOT002','BASE-132-v1');
    assert false, 'must not reach';
  exception when raise_exception then null;
  end;
  perform k_start_scenario_job('JOB-FORK','CTX-LOT002','BASE-132-v1', true);
  raise notice 'F10 PASS superseded scenario -> blocked unless explicit fork';
end $$;

-- Timeline for DREAM CONTROL: one query, whole job (conversation + runtime + calc)
select 'MSG' as kind, created_at, coalesce(code, '#'||id) as ref, sender||'→'||recipient as who, type as what, disposition as note
  from k_message where job_id = 'LOT-002'
union all
select 'EVT', created_at, '#'||id, coalesce(claimed_by, '-'), type, coalesce(runtime_ref, '')
  from k_event where job_id = 'LOT-002'
order by created_at, ref
limit 12;
