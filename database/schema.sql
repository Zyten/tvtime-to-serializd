-- database/schema.sql

-- Enable trigram extension for text search
create extension if not exists pg_trgm;

-- TV Shows table
create table if not exists tv_shows (
    id bigint primary key,
    original_name text not null,
    popularity real,
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create search index for TV shows
create index if not exists tv_shows_name_search on tv_shows using gin (original_name gin_trgm_ops);

-- Cache table for TMDB API responses
create table if not exists tmdb_cache (
    tvdb_id text primary key,
    tmdb_data jsonb not null,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    expires_at timestamp with time zone not null
);
