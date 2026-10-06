-- DREAM Computable Building — Postgres / Supabase schema (prototype)
-- Principles encoded at the data level:
--   1. Inputs live ONLY in `parameter_version`. Outputs live ONLY in `calc_run`.
--   2. status FIXED requires evidence + approval (trigger), DERIVED is never an input.
--   3. Everything is append-only + versioned. "Current" is a view, not an UPDATE.
--   4. AI writes only to ai_* tables and `change_request`; never to parameter_version.
-- Core tables (shared with Vertical A) are prefixed core_; domain pack tables dev_.

create extension if not exists pgcrypto;
create extension if not exists vector;        -- evidence chunk embeddings (pgvector)

create type param_status   as enum ('FIXED','ASSUMPTION','OPTION');   -- DERIVED deliberately absent
create type approval_state as enum ('PENDING','APPROVED','REJECTED');
create type job_state      as enum ('QUEUED','RUNNING','WAITING_HUMAN','DONE','FAILED','CANCELLED');

-- ===================== CORE (Vertical A + B) =====================
create table core_project (
  id uuid primary key default gen_random_uuid(),
  code text unique not null,                 -- 'DAEHEUNG'
  vertical text not null check (vertical in ('PRODUCT','DEVELOPMENT')),
  name text not null,
  created_at timestamptz not null default now()
);

create table core_model_version (            -- immutable snapshot ("v12 approved base")
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  label text not null,                       -- 'SLIM-132 v3'
  parent_id uuid references core_model_version(id),
  frozen boolean not null default false,     -- frozen versions accept no new parameter rows
  created_by uuid, created_at timestamptz not null default now(),
  unique (project_id, label)
);

create table core_evidence (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  kind text not null check (kind in ('DOCUMENT','QUOTE','LAW','EXPERT_OPINION','MARKET_DATA','CALC_RUN','AI_RESEARCH')),
  title text not null,
  storage_path text,                         -- Supabase Storage object (PDF/XLSX/IFC)
  source_url text,
  issued_on date,
  reliability smallint not null check (reliability between 1 and 5),
  verified_by uuid,                          -- human who checked it; null = unverified
  created_at timestamptz not null default now()
);

create table core_evidence_chunk (           -- RAG over evidence; AI must cite chunk ids
  id bigserial primary key,
  evidence_id uuid not null references core_evidence(id) on delete cascade,
  locator text,                              -- 'p.3', 'Sheet2!B41'
  content text not null,
  embedding vector(1536)
);

create table core_approval (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  subject_type text not null,                -- 'PARAMETER','SCENARIO_PROMOTION','ENGINE_VERSION','EXTERNAL_RELEASE'
  subject_id text not null,
  state approval_state not null default 'PENDING',
  requested_by uuid, decided_by uuid,
  reason text,
  decided_at timestamptz,
  created_at timestamptz not null default now(),
  check (state = 'PENDING' or decided_by is not null)
);

-- The ONLY home of input numbers.
create table core_parameter_version (
  id bigserial primary key,
  model_version_id uuid not null references core_model_version(id),
  key text not null,                         -- 'cost.above_per_m2', 'floor.3F.area'
  value numeric not null,
  unit text not null,
  status param_status not null,
  confidence numeric(3,2) not null check (confidence between 0 and 1),
  approval_id uuid references core_approval(id),
  note text,
  created_by uuid, created_at timestamptz not null default now(),
  superseded_by bigint references core_parameter_version(id)
);
create unique index one_live_param on core_parameter_version (model_version_id, key) where superseded_by is null;

create table core_parameter_evidence (
  parameter_version_id bigint references core_parameter_version(id),
  evidence_id uuid references core_evidence(id),
  locator text,
  primary key (parameter_version_id, evidence_id)
);

-- FIXED needs an APPROVED approval and >=1 evidence. Checked at commit time
-- (deferred) so the parameter and its evidence links can be inserted in one tx.
create or replace function core_check_fixed() returns trigger language plpgsql as $$
begin
  if new.status = 'FIXED' then
    if not exists (select 1 from core_approval a where a.id = new.approval_id and a.state = 'APPROVED') then
      raise exception 'FIXED parameter % requires an APPROVED approval', new.key;
    end if;
    if not exists (select 1 from core_parameter_evidence e where e.parameter_version_id = new.id) then
      raise exception 'FIXED parameter % requires evidence', new.key;
    end if;
  end if;
  return new;
end $$;
create constraint trigger fixed_needs_approval_and_evidence
  after insert or update on core_parameter_version
  deferrable initially deferred for each row execute function core_check_fixed();

create table core_scenario (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  code text not null,                        -- 'BASE-132','KM36-3F','B3'
  model_version_id uuid not null references core_model_version(id),
  selections jsonb not null default '{}',    -- {"3F":"KM36"}
  overrides jsonb not null default '{}',     -- {key:{value,unit,status:'OPTION'|'ASSUMPTION',...}}
  is_base boolean not null default false,    -- promotion to base = human approval
  created_at timestamptz not null default now(),
  unique (project_id, code),
  check (not (overrides::text ~ '"status"\s*:\s*"FIXED"'))
);

create table core_calc_run (                 -- the ONLY home of output numbers
  id uuid primary key default gen_random_uuid(),
  scenario_id uuid not null references core_scenario(id),
  engine_version text not null,
  input_hash char(64) not null,
  inputs jsonb not null,                     -- resolved leaf inputs (+ provenance)
  outputs jsonb not null,
  flags jsonb not null default '[]',
  created_at timestamptz not null default now(),
  unique (engine_version, input_hash)        -- same input+engine => one row (cache + proof)
);

create table core_decision (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  title text not null,
  chosen_scenario_id uuid references core_scenario(id),
  calc_run_id uuid references core_calc_run(id),   -- the numbers the decision was made on
  approval_id uuid references core_approval(id),
  rationale text,
  created_at timestamptz not null default now()
);

create table core_change_request (           -- how AI (or anyone) proposes a number
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  key text not null,
  proposed_value numeric not null,
  proposed_status param_status not null check (proposed_status <> 'FIXED'),
  evidence_ids uuid[] not null default '{}',
  proposed_by text not null,                 -- 'human:<uuid>' | 'ai:<role>:<ai_job_id>'
  approval_id uuid references core_approval(id),
  created_at timestamptz not null default now()
);

-- ===================== AI + WORKFLOW =====================
create table ai_job (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  role text not null,                        -- 'MEDICAL_RESEARCHER' — never a vendor name
  trigger text not null,                     -- 'IMPACT:KM36-3F', 'COACH', 'MANUAL'
  calc_run_id uuid references core_calc_run(id),
  input jsonb not null,                      -- context packet (see contracts/ai-job.schema.json)
  state job_state not null default 'QUEUED',
  workflow_run_id text,                      -- durable engine run id
  parent_job_id uuid references ai_job(id),  -- AI TALK threading
  created_at timestamptz not null default now()
);

create table ai_message (                    -- AI TALK transcript
  id bigserial primary key,
  job_id uuid not null references ai_job(id),
  speaker_role text not null,
  model_used text not null,                  -- resolved by the router, recorded for audit
  content text not null,                     -- may contain [[node_id]] placeholders only
  cited_evidence uuid[] not null default '{}',
  tokens_in int, tokens_out int, cost_usd numeric(10,4),
  guard_ok boolean not null,                 -- number guard result
  created_at timestamptz not null default now()
);

create table ai_result (
  job_id uuid primary key references ai_job(id),
  verdict text not null check (verdict in ('SUPPORT','CONCERN','BLOCKER','INSUFFICIENT_EVIDENCE')),
  summary text not null,
  findings jsonb not null,                   -- [{claim, type: FACT|SOURCE|INFERENCE|ASSUMPTION, evidence_ids[]}]
  proposed_change_ids uuid[] not null default '{}',
  coach_next text check (coach_next in ('CONTINUE','DEEPEN','CHALLENGE','VERIFY','REFRAME','STOP'))
);

create table wf_run (                        -- mirror of durable-engine runs for the OPERATIONS VIEW
  id text primary key,
  project_id uuid not null references core_project(id),
  kind text not null,                        -- 'SCENARIO_REVIEW','EVIDENCE_INGEST','EXTERNAL_RELEASE'
  state job_state not null,
  waiting_for text,                          -- 'approval:<id>' | 'expert:<id>'
  updated_at timestamptz not null default now()
);

-- ===================== DOMAIN PACK: DEVELOPMENT =====================
create table dev_floor (
  id uuid primary key default gen_random_uuid(),
  model_version_id uuid not null references core_model_version(id),
  level text not null,                       -- 'B3'..'15F'
  sort_order int not null,
  area_param_key text not null,              -- -> core_parameter_version.key
  current_use text not null,
  use_status param_status not null,
  allowed_options text[] not null,
  unique (model_version_id, level)
);

create table dev_md_option (
  code text primary key,                     -- 'KM36'
  label text not null,
  category text not null,                    -- 'MEDICAL','RETAIL','ANCHOR','RESIDENTIAL','PARKING'
  review_roles text[] not null
);

create table dev_md_option_param (           -- option-supplied slot inputs, versioned like everything else
  model_version_id uuid not null references core_model_version(id),
  option_code text not null references dev_md_option(code),
  key text not null,                         -- 'required_area_m2'
  parameter_version_id bigint not null references core_parameter_version(id),
  primary key (model_version_id, option_code, key)
);

create table dev_party (                     -- contractor / expert / LH / lender / tenant
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references core_project(id),
  kind text not null check (kind in ('ARCHITECT','STRUCTURE','CIVIL','MEP','FIRE','CONTRACTOR','SUPERVISOR','LENDER','LH','TENANT','LEGAL','TAX','OTHER')),
  name text not null,
  contact_note text                          -- no personal identifiers
);

-- Qualitative impact graph (not arithmetic): "B3 → 지하수 대책 → 인허가 리스크"
create table dev_impact_edge (
  project_id uuid not null references core_project(id),
  source text not null,                      -- calc node id, option code, or domain concept
  target text not null,
  relation text not null check (relation in ('COMPUTES','CONSTRAINS','REQUIRES_REVIEW','REQUIRES_PERMIT','SCHEDULES')),
  review_role text,
  primary key (project_id, source, target, relation)
);

-- Convenience: live parameters for a model version
create view core_parameter_live as
  select * from core_parameter_version where superseded_by is null;

-- RLS: enable on every table; the AI service role gets INSERT only on ai_*, core_change_request,
-- core_evidence(kind='AI_RESEARCH'); it has no UPDATE/INSERT on core_parameter_version.
alter table core_parameter_version enable row level security;
alter table core_calc_run          enable row level security;
alter table ai_job                 enable row level security;
alter table ai_message             enable row level security;
alter table ai_result              enable row level security;
