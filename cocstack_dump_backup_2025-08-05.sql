-- Backup of cocstack_dump.sql created on 2025-08-05
-- This is a direct copy of the original dump before any bonus history edits.
--
-- PostgreSQL database dump
--

-- Dumped from database version 15.13 (Debian 15.13-1.pgdg120+1)
-- Dumped by pg_dump version 15.13 (Debian 15.13-1.pgdg120+1)

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
-- Name: bonus_history; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.bonus_history (
    id integer NOT NULL,
    player_name text NOT NULL,
    player_tag text,
    awarded_date timestamp without time zone NOT NULL,
    awarded_by text NOT NULL,
    bonus_type text DEFAULT 'CWL'::text,
    notes text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.bonus_history OWNER TO racetracker;

--
-- Name: bonus_history_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.bonus_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bonus_history_id_seq OWNER TO racetracker;

--
-- Name: bonus_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.bonus_history_id_seq OWNED BY public.bonus_history.id;


--
-- Name: bonus_undo_log; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.bonus_undo_log (
    id integer NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    user_id text,
    player_name text,
    player_tag text,
    bonus_count integer,
    last_bonus_date text
);


ALTER TABLE public.bonus_undo_log OWNER TO racetracker;

--
-- Name: bonus_undo_log_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.bonus_undo_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.bonus_undo_log_id_seq OWNER TO racetracker;

--
-- Name: bonus_undo_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.bonus_undo_log_id_seq OWNED BY public.bonus_undo_log.id;


--
-- Name: cwl_history; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.cwl_history (
    id integer NOT NULL,
    season_year integer NOT NULL,
    season_month integer NOT NULL,
    reset_date timestamp without time zone NOT NULL,
    player_name text NOT NULL,
    player_tag text,
    missed_attacks integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cwl_history OWNER TO racetracker;

--
-- Name: cwl_history_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.cwl_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cwl_history_id_seq OWNER TO racetracker;

--
-- Name: cwl_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.cwl_history_id_seq OWNED BY public.cwl_history.id;


--
-- Name: cwl_stars_history; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.cwl_stars_history (
    id integer NOT NULL,
    player_name text NOT NULL,
    player_tag text,
    war_date timestamp without time zone NOT NULL,
    war_round integer NOT NULL,
    stars_earned integer NOT NULL,
    total_stars integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cwl_stars_history OWNER TO racetracker;

--
-- Name: cwl_stars_history_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.cwl_stars_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cwl_stars_history_id_seq OWNER TO racetracker;

--
-- Name: cwl_stars_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.cwl_stars_history_id_seq OWNED BY public.cwl_stars_history.id;


--
-- Name: discord_coc_links; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.discord_coc_links (
    discord_id text NOT NULL,
    coc_name_or_tag text NOT NULL,
    linked_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.discord_coc_links OWNER TO racetracker;

--
-- Name: missed_attacks_history; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.missed_attacks_history (
    id integer NOT NULL,
    player_tag text NOT NULL,
    player_name text NOT NULL,
    war_tag text NOT NULL,
    round_num integer NOT NULL,
    date_processed text NOT NULL
);


ALTER TABLE public.missed_attacks_history OWNER TO racetracker;

--
-- Name: missed_attacks_history_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.missed_attacks_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.missed_attacks_history_id_seq OWNER TO racetracker;

--
-- Name: missed_attacks_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.missed_attacks_history_id_seq OWNED BY public.missed_attacks_history.id;


--
-- Name: players; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.players (
    id integer NOT NULL,
    name text NOT NULL,
    tag text,
    join_date timestamp without time zone,
    bonus_eligibility boolean DEFAULT true,
    bonus_count integer DEFAULT 0,
    last_bonus_date timestamp without time zone,
    missed_attacks integer DEFAULT 0,
    notes text,
    role text DEFAULT ''::text,
    active boolean DEFAULT true,
    cwl_stars integer DEFAULT 0,
    inactive boolean DEFAULT false,
    location text DEFAULT 'Unknown'::text,
    latitude double precision,
    longitude double precision,
    favorite_troop text,
    location_updated timestamp without time zone
);


ALTER TABLE public.players OWNER TO racetracker;

--
-- Name: players_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.players_id_seq OWNER TO racetracker;

--
-- Name: players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.players_id_seq OWNED BY public.players.id;


--
-- Name: removed_players; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.removed_players (
    id integer NOT NULL,
    name text NOT NULL,
    tag text NOT NULL,
    removed_date timestamp without time zone NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.removed_players OWNER TO racetracker;

--
-- Name: removed_players_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.removed_players_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.removed_players_id_seq OWNER TO racetracker;

--
-- Name: removed_players_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.removed_players_id_seq OWNED BY public.removed_players.id;


--
-- Name: war_attacks; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.war_attacks (
    id integer NOT NULL,
    player_tag text NOT NULL,
    player_name text NOT NULL,
    war_tag text NOT NULL,
    attack_order integer,
    defender_tag text,
    stars integer,
    destruction_percentage double precision,
    attack_time timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.war_attacks OWNER TO racetracker;

--
-- Name: war_attacks_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.war_attacks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.war_attacks_id_seq OWNER TO racetracker;

--
-- Name: war_attacks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.war_attacks_id_seq OWNED BY public.war_attacks.id;


--
-- Name: bonus_history id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.bonus_history ALTER COLUMN id SET DEFAULT nextval('public.bonus_history_id_seq'::regclass);


--
-- Name: bonus_undo_log id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.bonus_undo_log ALTER COLUMN id SET DEFAULT nextval('public.bonus_undo_log_id_seq'::regclass);


--
-- Name: cwl_history id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.cwl_history ALTER COLUMN id SET DEFAULT nextval('public.cwl_history_id_seq'::regclass);


--
-- Name: cwl_stars_history id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.cwl_stars_history ALTER COLUMN id SET DEFAULT nextval('public.cwl_stars_history_id_seq'::regclass);


--
-- Name: missed_attacks_history id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.missed_attacks_history ALTER COLUMN id SET DEFAULT nextval('public.missed_attacks_history_id_seq'::regclass);


--
-- Name: players id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.players ALTER COLUMN id SET DEFAULT nextval('public.players_id_seq'::regclass);


--
-- Name: removed_players id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.removed_players ALTER COLUMN id SET DEFAULT nextval('public.removed_players_id_seq'::regclass);


--
-- Name: war_attacks id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.war_attacks ALTER COLUMN id SET DEFAULT nextval('public.war_attacks_id_seq'::regclass);


--
-- Data for Name: bonus_history; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.bonus_history (id, player_name, player_tag, awarded_date, awarded_by, bonus_type, notes, created_at) FROM stdin;
1	Death	#CCGRUL82	2025-01-09 21:05:00	Yancmo	CWL	CWL Bonuses Awarded	2025-01-09 21:05:00
2	Klee	#GCYG8LLP	2025-01-09 21:05:00	Yancmo	CWL	CWL Bonuses Awarded	2025-01-09 21:05:00
3	Amber	#9CQJ299Q	2025-01-09 21:05:00	Yancmo	CWL	CWL Bonuses Awarded	2025-01-09 21:05:00
4	dnp	#8GLLP9Q2	2025-01-09 21:05:00	Yancmo	CWL	CWL Bonuses Awarded	2025-01-09 21:05:00
5	Shade	\N	2025-01-09 21:05:00	Yancmo	CWL	CWL Bonuses Awarded	2025-01-09 21:05:00
6	U Turn	#GRRLR08R	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
7	Pirate	#QUJPYVJ0R	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
8	Mason	#R9YVQGR8	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
9	Foo Fighter	\N	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
10	wes	#YPJJG92Q	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
11	Mama Squirrel	#28C0JCPV0	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
12	J3N	#Q22GRG9CU	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
13	natey	#P8P8QY8J	2025-02-09 20:36:00	Yancmo	CWL	CWL Bonuses Awarded	2025-02-09 20:36:00
14	Paddington bear	#2990VUYCU	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
15	MachZero	#LYJY9PRU	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
16	Souls-On-Fire	#20JGQRRY	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
17	jo	#QGPRL2J0	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
18	noslos	#RPPU8Y00	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
19	cocmaster	#2VL8VCQYQ	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
20	Ivan Drago	#22PC8PUP	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
21	moose40	#G882J80Y	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
22	shz06	#99VYLCJ	2025-03-09 20:41:00	Yancmo	CWL	CWL Bonuses Awarded	2025-03-09 20:41:00
23	anarchy125	#R8VLCVQ9	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
24	jcollind	#QCYULVVQC	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
25	/tps	#RYQQR8VY	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
26	dad	#CQVJC9CV	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
27	knightress	#LCPJCQJGY	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
28	Yancmo	#2YUPQQ9L	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
29	Mini Me	#UCP9QPC9	2025-04-09 20:57:00	Yancmo	CWL	CWL Bonuses Awarded	2025-04-09 20:57:00
30	RMax	#VLRGJVRL	2025-05-09 19:42:00	MANIA	CWL	CWL Bonuses Awarded	2025-05-09 19:42:00
31	LtCol Dad	#29YCGQU2	2025-05-09 19:42:00	MANIA	CWL	CWL Bonuses Awarded	2025-05-09 19:42:00
32	Zeponomous	#2CVYY9J0J	2025-05-09 19:42:00	MANIA	CWL	CWL Bonuses Awarded	2025-05-09 19:42:00
33	ronnie	#8VQQQ8UP	2025-05-09 19:42:00	MANIA	CWL	CWL Bonuses Awarded	2025-05-09 19:42:00
34	Amber	#9CQJ299Q	2025-05-09 19:42:00	MANIA	CWL	CWL Bonuses Awarded	2025-05-09 19:42:00
35	Foo Fighter	\N	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
36	Rajan	#298Y228CG	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
37	wes	#YPJJG92Q	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
38	Ray	#GL2Q0UY	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
39	Mama Squirrel	#28C0JCPV0	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
40	J3N	#Q22GRG9CU	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
41	Pirate	#QUJPYVJ0R	2025-07-09 20:40:00	MANIA	CWL	CWL Bonuses Awarded	2025-07-09 20:40:00
42	Death	#CCGRUL82	2025-06-09 18:32:00	ClashCWLBot	CWL	CWL Bonuses Awarded	2025-06-09 18:32:00
43	dnp	#8GLLP9Q2	2025-06-09 18:32:00	ClashCWLBot	CWL	CWL Bonuses Awarded	2025-06-09 18:32:00
44	Klee	#GCYG8LLP	2025-06-09 18:32:00	ClashCWLBot	CWL	CWL Bonuses Awarded	2025-06-09 18:32:00
45	natey	#P8P8QY8J	2025-06-09 18:32:00	ClashCWLBot	CWL	CWL Bonuses Awarded	2025-06-09 18:32:00
46	U Turn	#GRRLR08R	2025-06-09 18:32:00	ClashCWLBot	CWL	CWL Bonuses Awarded	2025-06-09 18:32:00
\.


--
-- Data for Name: bonus_undo_log; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.bonus_undo_log (id, created_at, user_id, player_name, player_tag, bonus_count, last_bonus_date) FROM stdin;
\.


--
-- Data for Name: cwl_history; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.cwl_history (id, season_year, season_month, reset_date, player_name, player_tag, missed_attacks, created_at) FROM stdin;
\.


--
-- Data for Name: cwl_stars_history; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.cwl_stars_history (id, player_name, player_tag, war_date, war_round, stars_earned, total_stars, created_at) FROM stdin;
\.


--
-- Data for Name: discord_coc_links; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.discord_coc_links (discord_id, coc_name_or_tag, linked_at) FROM stdin;
\.


--
-- Data for Name: missed_attacks_history; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.missed_attacks_history (id, player_tag, player_name, war_tag, round_num, date_processed) FROM stdin;
\.


--
-- Data for Name: players; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.players (id, name, tag, join_date, bonus_eligibility, bonus_count, last_bonus_date, missed_attacks, notes, role, active, cwl_stars, inactive, location, latitude, longitude, favorite_troop, location_updated) FROM stdin;
8	MANIA	#J0900GPC	2018-03-14 00:00:00	f	0	\N	0	SELF OPTED OUT	Leader	t	18	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.52732
6	MachZero	#LYJY9PRU	2023-12-26 00:00:00	t	1	2025-01-01 00:00:00	0	\N	Elder	t	25	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.527549
4	Mason	#R9YVQGR8	2022-01-03 00:00:00	t	1	2025-01-01 00:00:00	0	\N	Co-Leader	t	25	f	Colorado Springs, CO	38.8339578	-104.825348	\N	2025-06-20 05:57:45.528008
5	LtCol Dad	#29YCGQU2	2020-07-12 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	21	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.527089
17	noslos	#RPPU8Y00	2018-10-02 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	20	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.533463
2	Zeponomous	#2CVYY9J0J	2020-07-17 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	25	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.53117
9	Klee	#GCYG8LLP	2023-12-01 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	5	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.526634
30	Pokeges	#GYV0CQLU	2016-04-27 00:00:00	f	0	\N	0	VACATION 4/1/25	Co-Leader	t	0	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.529376
40	:-(kridd77)-:	#Q9RPRRYR	2018-08-04 00:00:00	f	0	\N	0	\N	Co-Leader	t	0	f	Unknown	\N	\N	\N	2025-06-19 17:21:59.993311
41	Cmdr Shepard	#28GCQRC8J	2016-04-27 00:00:00	f	0	\N	0	\N	Elder	t	0	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.524857
42	Qbert	#QG22GQRP	2018-02-14 00:00:00	f	0	\N	0	Havent seen online in some time	Member	t	0	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.529602
10	wes	#YPJJG92Q	2023-05-10 00:00:00	t	1	2025-07-09 20:32:00	0	\N	Elder	t	26	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.53415
7	Rajan	#298Y228CG	2025-04-20 00:00:00	t	1	2025-07-09 20:32:00	0	\N	Member	t	20	f	Toronto, ON	43.6534817	-79.3839347	\N	2025-06-20 05:57:45.530059
20	Ray	#GL2Q0UY	2023-12-01 00:00:00	t	1	2025-07-09 20:32:00	0	\N	Elder	t	6	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.530277
24	J3N	#Q22GRG9CU	2023-12-28 00:00:00	t	1	2025-07-09 20:32:00	0	\N	Elder	t	10	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.526404
36	Pirate	#QUJPYVJ0R	2024-02-11 00:00:00	t	1	2025-07-09 20:32:00	0	\N	Elder	t	14	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.529146
37	Mama Squirrel	#28C0JCPV0	2024-02-22 00:00:00	t	1	2025-07-09 20:32:00	0	\N	Elder	t	12	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.527777
18	cocmaster	#2VL8VCQYQ	2022-09-10 00:00:00	t	1	2025-01-01 00:00:00	0	\N	Elder	t	22	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.531628
31	Ivan Drago	#22PC8PUP	2024-10-18 00:00:00	t	1	2025-01-01 00:00:00	0	\N	Elder	t	12	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.526171
34	jo	#QGPRL2J0	2023-07-21 00:00:00	t	1	2025-01-01 00:00:00	0	\N	Elder	t	16	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.532545
11	dad	#CQVJC9CV	2024-06-03 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	24	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.531856
12	natey	#P8P8QY8J	2018-01-16 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	16	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.533234
15	GuchiDconqueror	#2Q2QUJPYG	2025-06-20 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Member	t	0	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.525938
14	Death	#CCGRUL82	2021-10-21 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	16	f	Birmingham, AL	33.5206824	-86.8024326	\N	2025-06-20 05:57:45.525092
21	dnp	#8GLLP9Q2	2023-03-12 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	18	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.532086
16	jcollind	#QCYULVVQC	2025-02-03 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	26	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.532315
1	U Turn	#GRRLR08R	2018-10-08 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	26	f	Chicopee, MA	42.1487691	-72.6071119	\N	2025-06-20 05:57:45.53074
3	RMax	#VLRGJVRL	2018-11-30 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	24	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.529831
23	Amber	#9CQJ299Q	2021-01-20 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	22	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.524615
19	Souls-On-Fire	#20JGQRRY	2023-12-25 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	20	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.530509
13	Pharaoh	#J0G02YRR	2025-07-18 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Member	t	0	f	Unknown	\N	\N	\N	\N
22	knightress	#LCPJCQJGY	2022-02-22 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Co-Leader	t	18	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.532775
25	anarchy125	#R8VLCVQ9	2023-02-21 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	20	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.531398
26	/tps	#RYQQR8VY	2024-03-23 00:00:00	t	1	2025-03-01 00:00:00	0	Restoring to active status	Elder	t	22	f	Unknown	\N	\N	\N	2025-06-19 17:21:59.985481
27	Yancmo	#2YUPQQ9L	2016-04-27 00:00:00	t	1	2025-03-01 00:00:00	0	Using active status commands	Co-Leader	t	22	f	Moore, OK	35.3383254	-97.4867045	Wall Breaker	2025-06-20 05:57:45.51876
28	Mini Me	#UCP9QPC9	2023-12-25 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	12	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.528457
29	Paddington bear	#2990VUYCU	2024-02-10 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	29	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.528917
32	Tony	#2YUY0RVJ	2025-07-18 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Member	t	0	f	Unknown	\N	\N	\N	\N
33	MikeyG	#UCYQYJQ2	2025-05-31 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Member	t	18	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.528226
35	moose40	#G882J80Y	2024-10-03 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	12	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.533004
38	ronnie	#8VQQQ8UP	2025-03-08 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Member	t	18	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.533691
39	shz06	#99VYLCJ	2024-02-19 00:00:00	t	1	2025-03-01 00:00:00	0	\N	Elder	t	6	f	Unknown	\N	\N	\N	2025-06-20 05:57:45.533922
\.


--
-- Data for Name: removed_players; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.removed_players (id, name, tag, removed_date, created_at) FROM stdin;
\.


--
-- Data for Name: war_attacks; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.war_attacks (id, player_tag, player_name, war_tag, attack_order, defender_tag, stars, destruction_percentage, attack_time, created_at) FROM stdin;
\.


--
-- Name: bonus_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.bonus_history_id_seq', 22, true);


--
-- Name: bonus_undo_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.bonus_undo_log_id_seq', 9, true);


--
-- Name: cwl_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.cwl_history_id_seq', 1, false);


--
-- Name: cwl_stars_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.cwl_stars_history_id_seq', 1, false);


--
-- Name: missed_attacks_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.missed_attacks_history_id_seq', 1, false);


--
-- Name: players_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.players_id_seq', 84, true);


--
-- Name: removed_players_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.removed_players_id_seq', 1, false);


--
-- Name: war_attacks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.war_attacks_id_seq', 1, false);


--
-- Name: bonus_history bonus_history_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.bonus_history
    ADD CONSTRAINT bonus_history_pkey PRIMARY KEY (id);


--
-- Name: bonus_undo_log bonus_undo_log_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.bonus_undo_log
    ADD CONSTRAINT bonus_undo_log_pkey PRIMARY KEY (id);


--
-- Name: cwl_history cwl_history_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.cwl_history
    ADD CONSTRAINT cwl_history_pkey PRIMARY KEY (id);


--
-- Name: cwl_stars_history cwl_stars_history_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.cwl_stars_history
    ADD CONSTRAINT cwl_stars_history_pkey PRIMARY KEY (id);


--
-- Name: discord_coc_links discord_coc_links_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.discord_coc_links
    ADD CONSTRAINT discord_coc_links_pkey PRIMARY KEY (discord_id);


--
-- Name: missed_attacks_history missed_attacks_history_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.missed_attacks_history
    ADD CONSTRAINT missed_attacks_history_pkey PRIMARY KEY (id);


--
-- Name: missed_attacks_history missed_attacks_history_player_tag_war_tag_key; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.missed_attacks_history
    ADD CONSTRAINT missed_attacks_history_player_tag_war_tag_key UNIQUE (player_tag, war_tag);


--
-- Name: players players_name_key; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_name_key UNIQUE (name);


--
-- Name: players players_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_pkey PRIMARY KEY (id);


--
-- Name: players players_tag_key; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.players
    ADD CONSTRAINT players_tag_key UNIQUE (tag);


--
-- Name: removed_players removed_players_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.removed_players
    ADD CONSTRAINT removed_players_pkey PRIMARY KEY (id);


--
-- Name: war_attacks war_attacks_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.war_attacks
    ADD CONSTRAINT war_attacks_pkey PRIMARY KEY (id);


--
-- Name: idx_bonus_history_awarded_date; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_bonus_history_awarded_date ON public.bonus_history USING btree (awarded_date);


--
-- Name: idx_bonus_history_player_name; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_bonus_history_player_name ON public.bonus_history USING btree (player_name);


--
-- Name: idx_cwl_history_player_name; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_cwl_history_player_name ON public.cwl_history USING btree (player_name);


--
-- Name: idx_cwl_stars_history_player_name; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_cwl_stars_history_player_name ON public.cwl_stars_history USING btree (player_name);


--
-- Name: idx_cwl_stars_history_war_date; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_cwl_stars_history_war_date ON public.cwl_stars_history USING btree (war_date);


--
-- Name: idx_discord_links_discord_id; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_discord_links_discord_id ON public.discord_coc_links USING btree (discord_id);


--
-- Name: idx_missed_attacks_history_player_tag; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_missed_attacks_history_player_tag ON public.missed_attacks_history USING btree (player_tag);


--
-- Name: idx_missed_attacks_history_war_tag; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_missed_attacks_history_war_tag ON public.missed_attacks_history USING btree (war_tag);


--
-- Name: idx_players_bonus_eligibility; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_players_bonus_eligibility ON public.players USING btree (bonus_eligibility);


--
-- Name: idx_players_coordinates; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_players_coordinates ON public.players USING btree (latitude, longitude);


--
-- Name: idx_players_inactive; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_players_inactive ON public.players USING btree (inactive);


--
-- Name: idx_players_location; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_players_location ON public.players USING btree (location);


--
-- Name: idx_players_name; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_players_name ON public.players USING btree (name);


--
-- Name: idx_players_tag; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_players_tag ON public.players USING btree (tag);


--
-- Name: idx_removed_players_removed_date; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_removed_players_removed_date ON public.removed_players USING btree (removed_date);


--
-- Name: idx_removed_players_tag; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_removed_players_tag ON public.removed_players USING btree (tag);


--
-- Name: idx_war_attacks_player_tag; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_war_attacks_player_tag ON public.war_attacks USING btree (player_tag);


--
-- Name: idx_war_attacks_war_tag; Type: INDEX; Schema: public; Owner: racetracker
--

CREATE INDEX idx_war_attacks_war_tag ON public.war_attacks USING btree (war_tag);


--
-- Name: cwl_history cwl_history_player_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.cwl_history
    ADD CONSTRAINT cwl_history_player_name_fkey FOREIGN KEY (player_name) REFERENCES public.players(name) ON DELETE CASCADE;


--
-- Name: cwl_stars_history cwl_stars_history_player_name_fkey; Type: FK CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.cwl_stars_history
    ADD CONSTRAINT cwl_stars_history_player_name_fkey FOREIGN KEY (player_name) REFERENCES public.players(name) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

