--
-- PostgreSQL database dump
--

\restrict Tbu95LEOWfbkdlRH6gc7LtiHbPsSRWbuT8Snvex2efzGPqaysIA2AD4PwDVJcXN

-- Dumped from database version 14.19 (Homebrew)
-- Dumped by pg_dump version 14.19 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: api_keys; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.api_keys (
    id uuid NOT NULL,
    key_hash character varying(255) NOT NULL,
    key_prefix character varying(10) NOT NULL,
    tier character varying(20) NOT NULL,
    rate_limit_per_day integer NOT NULL,
    is_active boolean NOT NULL,
    expires_at timestamp with time zone,
    last_used_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.api_keys OWNER TO brian;

--
-- Name: api_requests; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.api_requests (
    id uuid NOT NULL,
    endpoint character varying(500) NOT NULL,
    status character varying(20) NOT NULL,
    status_code integer,
    duration_ms integer NOT NULL,
    error_message text,
    requested_at timestamp with time zone NOT NULL
);


ALTER TABLE public.api_requests OWNER TO brian;

--
-- Name: cache_entries; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.cache_entries (
    id uuid NOT NULL,
    key character varying(500) NOT NULL,
    data jsonb NOT NULL,
    cached_at timestamp with time zone NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    data_type character varying(100) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.cache_entries OWNER TO brian;

--
-- Name: games; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.games (
    id uuid NOT NULL,
    game_id character varying(50) NOT NULL,
    season_id uuid NOT NULL,
    week integer NOT NULL,
    home_team_id uuid NOT NULL,
    away_team_id uuid NOT NULL,
    game_date timestamp with time zone NOT NULL,
    stadium character varying(200),
    channel character varying(50),
    status character varying(50),
    home_score integer,
    away_score integer,
    spread numeric(5,2),
    over_under numeric(5,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.games OWNER TO brian;

--
-- Name: injuries; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.injuries (
    id uuid NOT NULL,
    player_id uuid NOT NULL,
    season_id uuid NOT NULL,
    week integer NOT NULL,
    injury_status character varying(50) NOT NULL,
    body_part character varying(100),
    practice_status character varying(50),
    practice_description text,
    reported_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.injuries OWNER TO brian;

--
-- Name: judges_performance; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.judges_performance (
    id uuid NOT NULL,
    judge_id character varying(50) NOT NULL,
    week_number integer NOT NULL,
    ultra_lock_picks integer,
    ultra_lock_hits integer,
    ultra_lock_accuracy double precision,
    super_lock_picks integer,
    super_lock_hits integer,
    super_lock_accuracy double precision,
    standard_lock_picks integer,
    standard_lock_hits integer,
    standard_lock_accuracy double precision,
    lotto_picks integer,
    lotto_hits integer,
    lotto_accuracy double precision,
    mega_lotto_picks integer,
    mega_lotto_hits integer,
    mega_lotto_accuracy double precision,
    category_accuracy jsonb,
    five_pillars_validation_accuracy double precision,
    weight_multiplier numeric(5,4),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.judges_performance OWNER TO brian;

--
-- Name: player_game_stats; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.player_game_stats (
    id uuid NOT NULL,
    player_id uuid NOT NULL,
    game_id uuid NOT NULL,
    passing_attempts integer,
    passing_completions integer,
    passing_yards integer,
    passing_tds integer,
    interceptions integer,
    rushing_attempts integer,
    rushing_yards integer,
    rushing_tds integer,
    receptions integer,
    receiving_targets integer,
    receiving_yards integer,
    receiving_tds integer,
    fumbles integer,
    fumbles_lost integer,
    fantasy_points numeric(6,2),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.player_game_stats OWNER TO brian;

--
-- Name: player_props; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.player_props (
    id uuid NOT NULL,
    player_id uuid NOT NULL,
    game_id uuid NOT NULL,
    sportsbook character varying(100) NOT NULL,
    prop_type character varying(100) NOT NULL,
    line numeric(10,2) NOT NULL,
    over_odds integer,
    under_odds integer,
    posted_at timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.player_props OWNER TO brian;

--
-- Name: players; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.players (
    id uuid NOT NULL,
    player_id character varying(50) NOT NULL,
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    team_id uuid,
    "position" character varying(10) NOT NULL,
    jersey_number integer,
    status character varying(50),
    height character varying(10),
    weight integer,
    birth_date date,
    college character varying(200),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.players OWNER TO brian;

--
-- Name: seasons; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.seasons (
    id uuid NOT NULL,
    year integer NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.seasons OWNER TO brian;

--
-- Name: teams; Type: TABLE; Schema: public; Owner: brian
--

CREATE TABLE public.teams (
    id uuid NOT NULL,
    team_id character varying(10) NOT NULL,
    key character varying(10) NOT NULL,
    city character varying(100) NOT NULL,
    name character varying(100) NOT NULL,
    conference character varying(3),
    division character varying(10),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.teams OWNER TO brian;

--
-- Data for Name: api_keys; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.api_keys (id, key_hash, key_prefix, tier, rate_limit_per_day, is_active, expires_at, last_used_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: api_requests; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.api_requests (id, endpoint, status, status_code, duration_ms, error_message, requested_at) FROM stdin;
\.


--
-- Data for Name: cache_entries; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.cache_entries (id, key, data, cached_at, expires_at, data_type, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: games; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.games (id, game_id, season_id, week, home_team_id, away_team_id, game_date, stadium, channel, status, home_score, away_score, spread, over_under, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: injuries; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.injuries (id, player_id, season_id, week, injury_status, body_part, practice_status, practice_description, reported_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: judges_performance; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.judges_performance (id, judge_id, week_number, ultra_lock_picks, ultra_lock_hits, ultra_lock_accuracy, super_lock_picks, super_lock_hits, super_lock_accuracy, standard_lock_picks, standard_lock_hits, standard_lock_accuracy, lotto_picks, lotto_hits, lotto_accuracy, mega_lotto_picks, mega_lotto_hits, mega_lotto_accuracy, category_accuracy, five_pillars_validation_accuracy, weight_multiplier, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: player_game_stats; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.player_game_stats (id, player_id, game_id, passing_attempts, passing_completions, passing_yards, passing_tds, interceptions, rushing_attempts, rushing_yards, rushing_tds, receptions, receiving_targets, receiving_yards, receiving_tds, fumbles, fumbles_lost, fantasy_points, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: player_props; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.player_props (id, player_id, game_id, sportsbook, prop_type, line, over_odds, under_odds, posted_at, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: players; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.players (id, player_id, first_name, last_name, team_id, "position", jersey_number, status, height, weight, birth_date, college, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: seasons; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.seasons (id, year, start_date, end_date, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: teams; Type: TABLE DATA; Schema: public; Owner: brian
--

COPY public.teams (id, team_id, key, city, name, conference, division, created_at, updated_at) FROM stdin;
\.


--
-- Name: api_keys api_keys_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.api_keys
    ADD CONSTRAINT api_keys_pkey PRIMARY KEY (id);


--
-- Name: api_requests api_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.api_requests
    ADD CONSTRAINT api_requests_pkey PRIMARY KEY (id);


--
-- Name: cache_entries cache_entries_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.cache_entries
    ADD CONSTRAINT cache_entries_pkey PRIMARY KEY (id);


--
-- Name: games games_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_pkey PRIMARY KEY (id);


--
-- Name: injuries injuries_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.injuries
    ADD CONSTRAINT injuries_pkey PRIMARY KEY (id);


--
-- Name: judges_performance judges_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.judges_performance
    ADD CONSTRAINT judges_performance_pkey PRIMARY KEY (id);


--
-- Name: player_game_stats player_game_stats_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.player_game_stats
    ADD CONSTRAINT player_game_stats_pkey PRIMARY KEY (id);


--
-- Name: player_props player_props_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.player_props
    ADD CONSTRAINT player_props_pkey PRIMARY KEY (id);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (id);


--
-- Name: seasons seasons_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.seasons
    ADD CONSTRAINT seasons_pkey PRIMARY KEY (id);


--
-- Name: teams teams_pkey; Type: CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.teams
    ADD CONSTRAINT teams_pkey PRIMARY KEY (id);


--
-- Name: ix_api_keys_key_hash; Type: INDEX; Schema: public; Owner: brian
--

CREATE UNIQUE INDEX ix_api_keys_key_hash ON public.api_keys USING btree (key_hash);


--
-- Name: ix_api_keys_tier; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_api_keys_tier ON public.api_keys USING btree (tier);


--
-- Name: ix_api_requests_endpoint; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_api_requests_endpoint ON public.api_requests USING btree (endpoint);


--
-- Name: ix_api_requests_requested_at; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_api_requests_requested_at ON public.api_requests USING btree (requested_at);


--
-- Name: ix_api_requests_status; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_api_requests_status ON public.api_requests USING btree (status);


--
-- Name: ix_cache_entries_data_type; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_cache_entries_data_type ON public.cache_entries USING btree (data_type);


--
-- Name: ix_cache_entries_expires_at; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_cache_entries_expires_at ON public.cache_entries USING btree (expires_at);


--
-- Name: ix_cache_entries_key; Type: INDEX; Schema: public; Owner: brian
--

CREATE UNIQUE INDEX ix_cache_entries_key ON public.cache_entries USING btree (key);


--
-- Name: ix_games_game_date; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_games_game_date ON public.games USING btree (game_date);


--
-- Name: ix_games_game_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE UNIQUE INDEX ix_games_game_id ON public.games USING btree (game_id);


--
-- Name: ix_injuries_player_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_injuries_player_id ON public.injuries USING btree (player_id);


--
-- Name: ix_injuries_week; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_injuries_week ON public.injuries USING btree (week);


--
-- Name: ix_judges_performance_judge_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_judges_performance_judge_id ON public.judges_performance USING btree (judge_id);


--
-- Name: ix_judges_performance_week_number; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_judges_performance_week_number ON public.judges_performance USING btree (week_number);


--
-- Name: ix_player_game_stats_game_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_player_game_stats_game_id ON public.player_game_stats USING btree (game_id);


--
-- Name: ix_player_game_stats_player_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_player_game_stats_player_id ON public.player_game_stats USING btree (player_id);


--
-- Name: ix_player_props_game_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_player_props_game_id ON public.player_props USING btree (game_id);


--
-- Name: ix_player_props_player_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_player_props_player_id ON public.player_props USING btree (player_id);


--
-- Name: ix_player_props_prop_type; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_player_props_prop_type ON public.player_props USING btree (prop_type);


--
-- Name: ix_player_props_sportsbook; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_player_props_sportsbook ON public.player_props USING btree (sportsbook);


--
-- Name: ix_players_last_name; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_players_last_name ON public.players USING btree (last_name);


--
-- Name: ix_players_player_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE UNIQUE INDEX ix_players_player_id ON public.players USING btree (player_id);


--
-- Name: ix_players_position; Type: INDEX; Schema: public; Owner: brian
--

CREATE INDEX ix_players_position ON public.players USING btree ("position");


--
-- Name: ix_seasons_year; Type: INDEX; Schema: public; Owner: brian
--

CREATE UNIQUE INDEX ix_seasons_year ON public.seasons USING btree (year);


--
-- Name: ix_teams_team_id; Type: INDEX; Schema: public; Owner: brian
--

CREATE UNIQUE INDEX ix_teams_team_id ON public.teams USING btree (team_id);


--
-- Name: games games_away_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_away_team_id_fkey FOREIGN KEY (away_team_id) REFERENCES public.teams(id);


--
-- Name: games games_home_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_home_team_id_fkey FOREIGN KEY (home_team_id) REFERENCES public.teams(id);


--
-- Name: games games_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.games
    ADD CONSTRAINT games_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.seasons(id);


--
-- Name: injuries injuries_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.injuries
    ADD CONSTRAINT injuries_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: injuries injuries_season_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.injuries
    ADD CONSTRAINT injuries_season_id_fkey FOREIGN KEY (season_id) REFERENCES public.seasons(id);


--
-- Name: player_game_stats player_game_stats_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.player_game_stats
    ADD CONSTRAINT player_game_stats_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.games(id);


--
-- Name: player_game_stats player_game_stats_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.player_game_stats
    ADD CONSTRAINT player_game_stats_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: player_props player_props_game_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.player_props
    ADD CONSTRAINT player_props_game_id_fkey FOREIGN KEY (game_id) REFERENCES public.games(id);


--
-- Name: player_props player_props_player_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.player_props
    ADD CONSTRAINT player_props_player_id_fkey FOREIGN KEY (player_id) REFERENCES public.players(id);


--
-- Name: players players_team_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: brian
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_team_id_fkey FOREIGN KEY (team_id) REFERENCES public.teams(id);


--
-- PostgreSQL database dump complete
--

\unrestrict Tbu95LEOWfbkdlRH6gc7LtiHbPsSRWbuT8Snvex2efzGPqaysIA2AD4PwDVJcXN

