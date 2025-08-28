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
-- Name: race; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.race (
    id integer NOT NULL,
    user_id integer NOT NULL,
    race_name character varying(200) NOT NULL,
    race_type character varying(50) NOT NULL,
    race_date date NOT NULL,
    race_time character varying(8),
    finish_time character varying(20) NOT NULL,
    location character varying(200),
    weather character varying(100),
    notes text,
    created_at timestamp without time zone,
    start_weather character varying(100),
    finish_weather character varying(100)
);


ALTER TABLE public.race OWNER TO racetracker;

--
-- Name: race_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.race_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.race_id_seq OWNER TO racetracker;

--
-- Name: race_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.race_id_seq OWNED BY public.race.id;


--
-- Name: race_photo; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.race_photo (
    id integer NOT NULL,
    race_id integer NOT NULL,
    filename character varying(255) NOT NULL,
    original_filename character varying(255) NOT NULL,
    photo_type character varying(50) NOT NULL,
    caption character varying(500),
    uploaded_at timestamp without time zone
);


ALTER TABLE public.race_photo OWNER TO racetracker;

--
-- Name: race_photo_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.race_photo_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.race_photo_id_seq OWNER TO racetracker;

--
-- Name: race_photo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.race_photo_id_seq OWNED BY public.race_photo.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public."user" (
    id integer NOT NULL,
    username character varying(80),
    email character varying(120) NOT NULL,
    password_hash character varying(128),
    first_name character varying(50),
    last_name character varying(50),
    created_at timestamp without time zone,
    is_active boolean,
    is_admin boolean DEFAULT false,
    reset_token character varying(100),
    reset_token_expiry timestamp without time zone
);


ALTER TABLE public."user" OWNER TO racetracker;

--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_id_seq OWNER TO racetracker;

--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.user_id_seq OWNED BY public."user".id;


--
-- Name: workout; Type: TABLE; Schema: public; Owner: racetracker
--

CREATE TABLE public.workout (
    id integer NOT NULL,
    user_id integer NOT NULL,
    workout_type character varying(50) NOT NULL,
    duration character varying(20) NOT NULL,
    distance double precision,
    pace character varying(10),
    calories integer,
    heart_rate_avg integer,
    heart_rate_max integer,
    notes text,
    location character varying(200),
    weather character varying(100),
    workout_date date NOT NULL,
    created_at timestamp without time zone
);


ALTER TABLE public.workout OWNER TO racetracker;

--
-- Name: workout_id_seq; Type: SEQUENCE; Schema: public; Owner: racetracker
--

CREATE SEQUENCE public.workout_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.workout_id_seq OWNER TO racetracker;

--
-- Name: workout_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: racetracker
--

ALTER SEQUENCE public.workout_id_seq OWNED BY public.workout.id;


--
-- Name: race id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.race ALTER COLUMN id SET DEFAULT nextval('public.race_id_seq'::regclass);


--
-- Name: race_photo id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.race_photo ALTER COLUMN id SET DEFAULT nextval('public.race_photo_id_seq'::regclass);


--
-- Name: user id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public."user" ALTER COLUMN id SET DEFAULT nextval('public.user_id_seq'::regclass);


--
-- Name: workout id; Type: DEFAULT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.workout ALTER COLUMN id SET DEFAULT nextval('public.workout_id_seq'::regclass);


--
-- Data for Name: race; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.race (id, user_id, race_name, race_type, race_date, race_time, finish_time, location, weather, notes, created_at, start_weather, finish_weather) FROM stdin;
19	4	Pecan Creek Wine Run	5K	2024-09-22	09:30	59:15:92	Muskogee, OK	79.1°F, humidity 73%, wind 3.9 mph	https://runsignup.com/Race/Results/143189/IndividualResult/zZdk?resultSetId=491046#U88888065\r\n\r\nHOT AS HAITI! 	2025-08-06 23:14:53.64366	Clear sky: 72°F, wind 5 mph, humidity 60%	Clear sky: 74°F, wind 5 mph, humidity 60%
15	4	MHS Splash & Dash	5K	2025-07-26	07:00	48:15:00	McAlester, OK 	77.3°F, humidity 94%, wind 10.3 mph	https://www.onlineraceresults.com/race/view_race.php?race_id=79262&re_NO=178&submit_action=select_result#racetop	2025-08-06 23:04:01.035974	Clear sky: 68°F, wind 5 mph, humidity 60%	Clear sky: 68°F, wind 5 mph, humidity 60%
11	3	MHS Splash & Dash	5K	2025-07-26	07:00	48:16:00	McAlester, OK	77.3°F, humidity 94%, wind 10.3 mph	https://www.onlineraceresults.com/race/view_individual.php?make_printable=1&bib_num=179&race_id=79262&type=result	2025-08-01 22:25:24.20136	Clear sky: 68°F, wind 5 mph, humidity 60%	Clear sky: 68°F, wind 5 mph, humidity 60%
13	3	Shared Blessings	5K	2025-03-29	09:00	51:05:00	McAlester, OK	64.8°F, humidity 89%, wind 23 mph	https://runsignup.com/Race/Results/125938#resultSetId-537825;perpage:100	2025-08-06 22:56:24.875608	Clear sky: 72°F, wind 5 mph, humidity 60%	Clear sky: 72°F, wind 5 mph, humidity 60%
12	3	Veteren's Run	5K	2024-11-02	10:00	52:42:20	Talihina, OK	68.5°F, humidity 84%, wind 9.2 mph	First 5K with the Friends\r\nhttps://m1.onlineraceresults.com/race/view_plain_text.php?race_id=78757	2025-08-06 22:48:53.600739	Clear sky: 74°F, wind 5 mph, humidity 60%	Clear sky: 74°F, wind 5 mph, humidity 60%
14	3	Unicorns and Rainbows Color Run	5K	2025-04-25	18:30	47:28	McAlester, OK	77.1°F, humidity 59%, wind 5.4 mph	https://runsignup.com/Race/Results/161550/IndividualResult/TKTd?resultSetId=544115#U101940288	2025-08-06 22:59:04.447741	Clear sky: 78°F, wind 5 mph, humidity 60%	Clear sky: 68°F, wind 5 mph, humidity 60%
16	4	Unicorns and Rainbows Color Run	5K	2025-04-25	18:30	47:30:00	McAlester, OK	77.1°F, humidity 59%, wind 5.4 mph	https://runsignup.com/Race/Results/161550/IndividualResult/TKTd?resultSetId=544115#U101940290	2025-08-06 23:05:50.612973	Clear sky: 78°F, wind 5 mph, humidity 60%	Clear sky: 68°F, wind 5 mph, humidity 60%
17	4	Shared Blessings 5k	5K	2025-03-29	09:00	51:06:00	McAlester, OK	64.8°F, humidity 89%, wind 23 mph	https://runsignup.com/Race/Results/125938/IndividualResult/TFqK?resultSetId=537825#U100026820	2025-08-06 23:07:27.222737	Clear sky: 72°F, wind 5 mph, humidity 60%	Clear sky: 72°F, wind 5 mph, humidity 60%
18	4	Veteran's Run	5K	2024-11-02	10:00	52:41:30	Talihina, OK	68.5°F, humidity 84%, wind 9.2 mph	https://m1.onlineraceresults.com/race/view_plain_text.php?race_id=78758	2025-08-06 23:10:10.099386	Clear sky: 74°F, wind 5 mph, humidity 60%	Clear sky: 74°F, wind 5 mph, humidity 60%
\.


--
-- Data for Name: race_photo; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.race_photo (id, race_id, filename, original_filename, photo_type, caption, uploaded_at) FROM stdin;
1	19	2c3cbc8a-a1d3-4f91-89c9-97ff06fe9432.jpg	Ambee Wine Run.jpg	finish	And we're off	2025-08-06 23:14:53.673868
3	14	623af1a1-ee26-4f10-b59a-7166e774b468.png	pasted.png	other		2025-08-12 11:52:38.953577
4	13	efddb423-ca20-4f85-92e5-15e57933e641.png	pasted.png	other		2025-08-12 11:53:38.348673
5	11	d1b594f6-77ad-4f6e-b476-b1154b129fcd.jpg	pasted.jpg	other		2025-08-12 15:26:23.75856
6	11	8feb160f-314b-4aa9-ab90-51e2dd65482b.jpeg	IMG_9110.jpeg	other		2025-08-15 02:01:46.016556
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public."user" (id, username, email, password_hash, first_name, last_name, created_at, is_active, is_admin, reset_token, reset_token_expiry) FROM stdin;
3	yancmo	yancmo@gmail.com	pbkdf2:sha256:600000$xrArN3t1eGy072Wl$9606eeb9e4575cfc8813484fd543d4c8a34291fc79245b054d0550fe94e7dac9	Yancy	Shepherd	2025-08-01 22:21:50.948866	t	t	\N	\N
4	\N	ambeees@yahoo.com	pbkdf2:sha256:600000$AjCrPSY2oetE8xTG$8b3fb41fd7f549c65cb1073634e9851916b364619536254442e479615a4009e3	Amber	Shepherd	2025-08-04 20:07:27.252617	t	f	\N	\N
5	test999@example.com	test999@example.com	pbkdf2:sha256:600000$Cw2mnn5jvpvcmUVb$92fe251b5f3dcee4e934286b803c6bb1e59b8358d04b46179972249f18d3eb14	Test	User	2025-08-07 23:50:45.287215	\N	f	\N	\N
\.


--
-- Data for Name: workout; Type: TABLE DATA; Schema: public; Owner: racetracker
--

COPY public.workout (id, user_id, workout_type, duration, distance, pace, calories, heart_rate_avg, heart_rate_max, notes, location, weather, workout_date, created_at) FROM stdin;
\.


--
-- Name: race_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.race_id_seq', 20, true);


--
-- Name: race_photo_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.race_photo_id_seq', 6, true);


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.user_id_seq', 5, true);


--
-- Name: workout_id_seq; Type: SEQUENCE SET; Schema: public; Owner: racetracker
--

SELECT pg_catalog.setval('public.workout_id_seq', 1, false);


--
-- Name: race_photo race_photo_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.race_photo
    ADD CONSTRAINT race_photo_pkey PRIMARY KEY (id);


--
-- Name: race race_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.race
    ADD CONSTRAINT race_pkey PRIMARY KEY (id);


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: user user_username_key; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_username_key UNIQUE (username);


--
-- Name: workout workout_pkey; Type: CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.workout
    ADD CONSTRAINT workout_pkey PRIMARY KEY (id);


--
-- Name: race_photo race_photo_race_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.race_photo
    ADD CONSTRAINT race_photo_race_id_fkey FOREIGN KEY (race_id) REFERENCES public.race(id);


--
-- Name: race race_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.race
    ADD CONSTRAINT race_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- Name: workout workout_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: racetracker
--

ALTER TABLE ONLY public.workout
    ADD CONSTRAINT workout_user_id_fkey FOREIGN KEY (user_id) REFERENCES public."user"(id);


--
-- PostgreSQL database dump complete
--

