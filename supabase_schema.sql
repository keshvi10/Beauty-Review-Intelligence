-- Anonymous usage analytics schema for Beauty Review Intelligence.
-- No personal data, IP addresses, or identity-linked fields are stored.
-- session_id is a random, client-generated, per-browser-tab token.

create table if not exists search_events (
  id bigint generated always as identity primary key,
  product_query text not null,
  session_id text not null,
  created_at timestamptz not null default now()
);

create table if not exists platform_views (
  id bigint generated always as identity primary key,
  platform text not null,
  session_id text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_search_events_created_at on search_events (created_at);
create index if not exists idx_platform_views_platform on platform_views (platform);

-- Example aggregate queries (no personal data is ever exposed):
--   total searches:           select count(*) from search_events;
--   most searched products:   select product_query, count(*) from search_events group by 1 order by 2 desc;
--   most viewed platforms:    select platform, count(*) from platform_views group by 1 order by 2 desc;
--   unique sessions:          select count(distinct session_id) from search_events;
