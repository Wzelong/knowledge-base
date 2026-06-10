create extension if not exists vector;

create table if not exists sources (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  source_type text not null,
  origin text,
  summary text not null,
  metadata jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists concepts (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  description text not null,
  embedding vector(1536) not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists concept_sources (
  concept_id uuid not null references concepts(id) on delete cascade,
  source_id uuid not null references sources(id) on delete cascade,
  description text not null,
  created_at timestamptz not null default now(),
  primary key (concept_id, source_id)
);

create index if not exists concepts_embedding_idx
  on concepts using hnsw (embedding vector_cosine_ops);

create or replace function match_concepts(
  query_embedding vector(1536),
  match_count int default 5
)
returns table (id uuid, name text, description text, similarity double precision)
language sql stable as $$
  select c.id, c.name, c.description,
         1 - (c.embedding <=> query_embedding) as similarity
  from concepts c
  order by c.embedding <=> query_embedding
  limit match_count;
$$;

create or replace function set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger concepts_updated_at
  before update on concepts
  for each row execute function set_updated_at();

alter table sources enable row level security;
alter table concepts enable row level security;
alter table concept_sources enable row level security;
