--
-- PostgreSQL database dump
--

\restrict buH5pBc1yRWFGJvvUG4HLWQFruHzdV4lZHfNU6Xhnpikq6ZKi6swlK6KuClMgek

-- Dumped from database version 16.10 (Ubuntu 16.10-1.pgdg24.04+1)
-- Dumped by pg_dump version 16.10 (Ubuntu 16.10-1.pgdg24.04+1)

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

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: infrawatch
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO infrawatch;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: infrawatch
--

COMMENT ON SCHEMA public IS '';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alert_logs; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.alert_logs (
    id integer NOT NULL,
    id_alert integer NOT NULL,
    id_user integer NOT NULL,
    action character varying(100) NOT NULL,
    comment text,
    created_at timestamp without time zone NOT NULL
);


ALTER TABLE public.alert_logs OWNER TO infrawatch;

--
-- Name: alert_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.alert_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alert_logs_id_seq OWNER TO infrawatch;

--
-- Name: alert_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.alert_logs_id_seq OWNED BY public.alert_logs.id;


--
-- Name: alerts; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.alerts (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    severity character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    category character varying(50) NOT NULL,
    impact character varying(50) NOT NULL,
    system character varying(255) NOT NULL,
    assignee character varying(255),
    id_endpoint integer,
    id_user_created integer NOT NULL,
    id_user_assigned integer,
    created_at timestamp without time zone NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    acknowledged_at timestamp without time zone,
    resolved_at timestamp without time zone
);


ALTER TABLE public.alerts OWNER TO infrawatch;

--
-- Name: alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alerts_id_seq OWNER TO infrawatch;

--
-- Name: alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.alerts_id_seq OWNED BY public.alerts.id;


--
-- Name: email_config; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.email_config (
    id integer NOT NULL,
    email character varying NOT NULL,
    password character varying NOT NULL,
    port integer NOT NULL,
    server character varying NOT NULL,
    active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.email_config OWNER TO infrawatch;

--
-- Name: email_config_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.email_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.email_config_id_seq OWNER TO infrawatch;

--
-- Name: email_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.email_config_id_seq OWNED BY public.email_config.id;


--
-- Name: endpoints; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.endpoints (
    id integer NOT NULL,
    ip character varying,
    nickname character varying,
    "interval" integer,
    version character varying,
    community character varying,
    port integer,
    "user" character varying,
    active boolean,
    "authKey" character varying,
    "privKey" character varying,
    id_usuario integer
);


ALTER TABLE public.endpoints OWNER TO infrawatch;

--
-- Name: endpoints_data; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.endpoints_data (
    id integer NOT NULL,
    id_end_point integer,
    status boolean,
    "sysDescr" text,
    "sysName" character varying,
    "sysUpTime" character varying,
    "hrProcessorLoad" character varying,
    "memTotalReal" character varying,
    "memAvailReal" character varying,
    "hrStorageSize" character varying,
    "hrStorageUsed" character varying,
    "hrStorageDescr" character varying,
    "ifOperStatus" character varying,
    "ifInOctets" character varying,
    "ifOutOctets" character varying,
    ping_rtt character varying,
    snmp_rtt character varying,
    last_updated timestamp without time zone
);


ALTER TABLE public.endpoints_data OWNER TO infrawatch;

--
-- Name: endpoints_data_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.endpoints_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.endpoints_data_id_seq OWNER TO infrawatch;

--
-- Name: endpoints_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.endpoints_data_id_seq OWNED BY public.endpoints_data.id;


--
-- Name: endpoints_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.endpoints_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.endpoints_id_seq OWNER TO infrawatch;

--
-- Name: endpoints_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.endpoints_id_seq OWNED BY public.endpoints.id;


--
-- Name: endpoints_oids; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.endpoints_oids (
    id integer NOT NULL,
    id_end_point integer,
    "sysDescr" text,
    "sysName" character varying,
    "sysUpTime" character varying,
    "hrProcessorLoad" character varying,
    "memTotalReal" character varying,
    "memAvailReal" character varying,
    "hrStorageSize" character varying,
    "hrStorageUsed" character varying,
    "hrStorageDescr" character varying,
    "ifOperStatus" character varying,
    "ifInOctets" character varying,
    "ifOutOctets" character varying
);


ALTER TABLE public.endpoints_oids OWNER TO infrawatch;

--
-- Name: endpoints_oids_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.endpoints_oids_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.endpoints_oids_id_seq OWNER TO infrawatch;

--
-- Name: endpoints_oids_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.endpoints_oids_id_seq OWNED BY public.endpoints_oids.id;


--
-- Name: failure_threshold_config; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.failure_threshold_config (
    id integer NOT NULL,
    consecutive_snmp_failures integer,
    consecutive_ping_failures integer,
    active boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.failure_threshold_config OWNER TO infrawatch;

--
-- Name: failure_threshold_config_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.failure_threshold_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.failure_threshold_config_id_seq OWNER TO infrawatch;

--
-- Name: failure_threshold_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.failure_threshold_config_id_seq OWNED BY public.failure_threshold_config.id;


--
-- Name: incidents; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.incidents (
    id integer NOT NULL,
    endpoint_id integer NOT NULL,
    alert_id integer,
    incident_type character varying(50) NOT NULL,
    severity character varying(50),
    status character varying(50),
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone,
    duration_seconds integer,
    root_cause text,
    impact_description text,
    resolution_notes text,
    detected_by character varying(100),
    resolved_by integer,
    response_time_minutes double precision,
    resolution_time_minutes double precision
);


ALTER TABLE public.incidents OWNER TO infrawatch;

--
-- Name: incidents_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.incidents_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.incidents_id_seq OWNER TO infrawatch;

--
-- Name: incidents_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.incidents_id_seq OWNED BY public.incidents.id;


--
-- Name: performance_metrics; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.performance_metrics (
    id integer NOT NULL,
    endpoint_id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    response_time_p50 double precision,
    response_time_p90 double precision,
    response_time_p95 double precision,
    response_time_p99 double precision,
    response_time_p99_9 double precision,
    response_time_avg double precision,
    response_time_max double precision,
    response_time_min double precision,
    error_rate_percentage double precision,
    total_requests integer,
    failed_requests integer,
    requests_per_second double precision,
    throughput_mbps double precision,
    jitter_ms double precision,
    packet_loss_rate double precision,
    measurement_period_minutes integer,
    sample_count integer
);


ALTER TABLE public.performance_metrics OWNER TO infrawatch;

--
-- Name: performance_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.performance_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.performance_metrics_id_seq OWNER TO infrawatch;

--
-- Name: performance_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.performance_metrics_id_seq OWNED BY public.performance_metrics.id;


--
-- Name: performance_thresholds; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.performance_thresholds (
    id integer NOT NULL,
    metric_type character varying(50) NOT NULL,
    warning_threshold integer NOT NULL,
    critical_threshold integer NOT NULL,
    enabled boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.performance_thresholds OWNER TO infrawatch;

--
-- Name: performance_thresholds_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.performance_thresholds_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.performance_thresholds_id_seq OWNER TO infrawatch;

--
-- Name: performance_thresholds_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.performance_thresholds_id_seq OWNED BY public.performance_thresholds.id;


--
-- Name: sla_metrics; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.sla_metrics (
    id integer NOT NULL,
    endpoint_id integer NOT NULL,
    "timestamp" timestamp without time zone NOT NULL,
    availability_percentage double precision NOT NULL,
    uptime_seconds integer,
    downtime_seconds integer,
    mttr_minutes double precision,
    mtbf_hours double precision,
    incidents_count integer,
    sla_target double precision,
    sla_compliance boolean NOT NULL,
    sla_breach_minutes double precision,
    avg_response_time double precision,
    max_response_time double precision,
    min_response_time double precision,
    measurement_period_hours integer
);


ALTER TABLE public.sla_metrics OWNER TO infrawatch;

--
-- Name: sla_metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.sla_metrics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sla_metrics_id_seq OWNER TO infrawatch;

--
-- Name: sla_metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.sla_metrics_id_seq OWNED BY public.sla_metrics.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying,
    email character varying,
    password character varying,
    state boolean,
    last_login timestamp without time zone,
    access_level character varying,
    url character varying,
    alert boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.users OWNER TO infrawatch;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO infrawatch;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: webhook_config; Type: TABLE; Schema: public; Owner: infrawatch
--

CREATE TABLE public.webhook_config (
    id integer NOT NULL,
    url character varying NOT NULL,
    active boolean,
    timeout integer,
    access_token character varying,
    created_at timestamp without time zone,
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.webhook_config OWNER TO infrawatch;

--
-- Name: webhook_config_id_seq; Type: SEQUENCE; Schema: public; Owner: infrawatch
--

CREATE SEQUENCE public.webhook_config_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.webhook_config_id_seq OWNER TO infrawatch;

--
-- Name: webhook_config_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: infrawatch
--

ALTER SEQUENCE public.webhook_config_id_seq OWNED BY public.webhook_config.id;


--
-- Name: alert_logs id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alert_logs ALTER COLUMN id SET DEFAULT nextval('public.alert_logs_id_seq'::regclass);


--
-- Name: alerts id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alerts ALTER COLUMN id SET DEFAULT nextval('public.alerts_id_seq'::regclass);


--
-- Name: email_config id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.email_config ALTER COLUMN id SET DEFAULT nextval('public.email_config_id_seq'::regclass);


--
-- Name: endpoints id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints ALTER COLUMN id SET DEFAULT nextval('public.endpoints_id_seq'::regclass);


--
-- Name: endpoints_data id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints_data ALTER COLUMN id SET DEFAULT nextval('public.endpoints_data_id_seq'::regclass);


--
-- Name: endpoints_oids id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints_oids ALTER COLUMN id SET DEFAULT nextval('public.endpoints_oids_id_seq'::regclass);


--
-- Name: failure_threshold_config id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.failure_threshold_config ALTER COLUMN id SET DEFAULT nextval('public.failure_threshold_config_id_seq'::regclass);


--
-- Name: incidents id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.incidents ALTER COLUMN id SET DEFAULT nextval('public.incidents_id_seq'::regclass);


--
-- Name: performance_metrics id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.performance_metrics ALTER COLUMN id SET DEFAULT nextval('public.performance_metrics_id_seq'::regclass);


--
-- Name: performance_thresholds id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.performance_thresholds ALTER COLUMN id SET DEFAULT nextval('public.performance_thresholds_id_seq'::regclass);


--
-- Name: sla_metrics id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.sla_metrics ALTER COLUMN id SET DEFAULT nextval('public.sla_metrics_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: webhook_config id; Type: DEFAULT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.webhook_config ALTER COLUMN id SET DEFAULT nextval('public.webhook_config_id_seq'::regclass);


--
-- Data for Name: alert_logs; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.alert_logs (id, id_alert, id_user, action, comment, created_at) FROM stdin;
\.


--
-- Data for Name: alerts; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.alerts (id, title, description, severity, status, category, impact, system, assignee, id_endpoint, id_user_created, id_user_assigned, created_at, updated_at, acknowledged_at, resolved_at) FROM stdin;
\.


--
-- Data for Name: email_config; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.email_config (id, email, password, port, server, active, created_at, updated_at) FROM stdin;
1	ndondadaniel2020@gmail.com	nidh rxcq khsy lepx	587	smtp.gmail.com	t	2025-09-03 02:43:44	2025-09-03 02:43:44
\.


--
-- Data for Name: endpoints; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.endpoints (id, ip, nickname, "interval", version, community, port, "user", active, "authKey", "privKey", id_usuario) FROM stdin;
2	127.0.0.1	Endpoint-127.0.0.1	30	2c	public	161	\N	t	\N	\N	1
3	127.0.0.2	Endpoint-127.0.0.2	30	2c	public	161	\N	t	\N	\N	1
4	127.0.0.3	Endpoint-127.0.0.3	30	2c	public	161	\N	t	\N	\N	1
5	192.168.8.146	Endpoint-192.168.8.146	30			0	\N	t	\N	\N	1
6	127.0.0.4	Endpoint-127.0.0.4	30	2c	public	161	\N	t	\N	\N	1
7	127.0.0.5	Endpoint-127.0.0.5	30			0	\N	t	\N	\N	1
8	8.8.8.8	Endpoint-8.8.8.8	30			0	\N	t	\N	\N	1
9	dgg.gg	Endpoint-dgg.gg	30			0	\N	t	\N	\N	1
10	127.0.0.11	Endpoint-127.0.0.11	30	1	public	161	\N	t	\N	\N	1
11	127.0.0.12	Endpoint-127.0.0.12	30	2c	public	161	\N	t	\N	\N	1
12	127.0.0.13	Endpoint-127.0.0.13	30	3		161	\N	t	\N	\N	1
13	192.168.0.3	Endpoint-192.168.0.3	40			0	\N	t	\N	\N	1
14	1.1.1.1	Endpoint-1.1.1.1	30			0	\N	t	\N	\N	1
15	2.1.1.1	Endpoint-2.1.1.1	30			0	\N	f	\N	\N	1
16	3.1.1.1	Endpoint-3.1.1.1	30			0	\N	t	\N	\N	1
17	192.168.1.100	Test Endpoint	30	2c	public	161	\N	t	\N	\N	1
\.


--
-- Data for Name: endpoints_data; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.endpoints_data (id, id_end_point, status, "sysDescr", "sysName", "sysUpTime", "hrProcessorLoad", "memTotalReal", "memAvailReal", "hrStorageSize", "hrStorageUsed", "hrStorageDescr", "ifOperStatus", "ifInOctets", "ifOutOctets", ping_rtt, snmp_rtt, last_updated) FROM stdin;
\.


--
-- Data for Name: endpoints_oids; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.endpoints_oids (id, id_end_point, "sysDescr", "sysName", "sysUpTime", "hrProcessorLoad", "memTotalReal", "memAvailReal", "hrStorageSize", "hrStorageUsed", "hrStorageDescr", "ifOperStatus", "ifInOctets", "ifOutOctets") FROM stdin;
2	2	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
3	3	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
4	4	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
7	7	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
11	11	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
12	12	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
13	13	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
14	14	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
15	15										1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
16	16										1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
17	17	1.3.6.1.2.1.1.1.0	1.3.6.1.2.1.1.5.0	1.3.6.1.2.1.1.3.0	1.3.6.1.2.1.25.3.3.1.2	1.3.6.1.4.1.2021.4.5.0	1.3.6.1.4.1.2021.4.6.0	1.3.6.1.2.1.25.2.3.1.5	1.3.6.1.2.1.25.2.3.1.6	1.3.6.1.2.1.25.2.3.1.3	1.3.6.1.2.1.2.2.1.8	1.3.6.1.2.1.2.2.1.10	1.3.6.1.2.1.2.2.1.16
\.


--
-- Data for Name: failure_threshold_config; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.failure_threshold_config (id, consecutive_snmp_failures, consecutive_ping_failures, active, created_at, updated_at) FROM stdin;
1	10	5	t	2025-09-04 15:00:02	2025-09-04 15:00:02
\.


--
-- Data for Name: incidents; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.incidents (id, endpoint_id, alert_id, incident_type, severity, status, start_time, end_time, duration_seconds, root_cause, impact_description, resolution_notes, detected_by, resolved_by, response_time_minutes, resolution_time_minutes) FROM stdin;
\.


--
-- Data for Name: performance_metrics; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.performance_metrics (id, endpoint_id, "timestamp", response_time_p50, response_time_p90, response_time_p95, response_time_p99, response_time_p99_9, response_time_avg, response_time_max, response_time_min, error_rate_percentage, total_requests, failed_requests, requests_per_second, throughput_mbps, jitter_ms, packet_loss_rate, measurement_period_minutes, sample_count) FROM stdin;
\.


--
-- Data for Name: performance_thresholds; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.performance_thresholds (id, metric_type, warning_threshold, critical_threshold, enabled, created_at, updated_at) FROM stdin;
1	cpu	80	90	t	2025-09-08 21:42:33.022197	2025-09-08 21:42:33.022197
2	memory	85	95	t	2025-09-08 21:42:33.022197	2025-09-08 21:42:33.022197
3	storage	85	95	t	2025-09-08 21:42:33.022197	2025-09-08 21:42:33.022197
4	network	80	95	t	2025-09-08 21:42:33.022197	2025-09-08 21:42:33.022197
\.


--
-- Data for Name: sla_metrics; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.sla_metrics (id, endpoint_id, "timestamp", availability_percentage, uptime_seconds, downtime_seconds, mttr_minutes, mtbf_hours, incidents_count, sla_target, sla_compliance, sla_breach_minutes, avg_response_time, max_response_time, min_response_time, measurement_period_hours) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.users (id, name, email, password, state, last_login, access_level, url, alert, created_at, updated_at) FROM stdin;
1	Teste PostgreSQL	teste@postgres.com	senha123	t	\N	ADMIN	http://test.com	t	2025-09-08 21:38:51.386715	2025-09-08 21:38:51.386715
8	admin	admin@infrawatch.com	$2b$12$iqh4SwW8d70OH7p9zjkTMuVIJMyQycDORsmhQEHvdZatjjXW0DRgG	t	\N	ADMIN	\N	t	2025-09-08 21:45:52.592308	2025-09-08 21:45:52.592308
9	NdDaniel	ndondadaniel2020@gmail.com	$2b$12$GfnVOLU.AN/0dKPEPoNd4eBi494SFcnklUH5oX4XHanM7W3Bl13nq	t	2025-08-27 13:38:49.956089	ADMIN	\N	t	2025-09-08 21:45:52.592308	2025-09-08 21:45:52.592308
10	Emanuel Malungo	emalungo@admin.com	$2b$12$DtMmJ32weoq.I1m/bVP72e.9bk6qf.zOhvi9uRmT8pfFClyzw6dFC	t	\N	ADMIN	2025-08-27 12:14:09.799835	t	2025-09-08 21:45:52.592308	2025-09-08 21:45:52.592308
0	Sistema	sistema@infrawatch.com	sistema123	t	\N	ADMIN	\N	t	2025-09-08 22:07:45.286996	2025-09-08 22:07:45.286996
\.


--
-- Data for Name: webhook_config; Type: TABLE DATA; Schema: public; Owner: infrawatch
--

COPY public.webhook_config (id, url, active, timeout, access_token, created_at, updated_at) FROM stdin;
1	https://discord.com/api/webhooks/1412595075099136141/WP7CfeZ4saW39XoaDb17WrgLwhNw49r3_ufGg-wOj6dTWYmSE4A019AXLyRLtRCp5jjX	t	30	\N	2025-09-03 17:52:03	2025-09-03 20:23:53
\.


--
-- Name: alert_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.alert_logs_id_seq', 41, true);


--
-- Name: alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.alerts_id_seq', 51, true);


--
-- Name: email_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.email_config_id_seq', 1, false);


--
-- Name: endpoints_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.endpoints_data_id_seq', 2180, true);


--
-- Name: endpoints_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.endpoints_id_seq', 49, true);


--
-- Name: endpoints_oids_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.endpoints_oids_id_seq', 1, false);


--
-- Name: failure_threshold_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.failure_threshold_config_id_seq', 1, false);


--
-- Name: incidents_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.incidents_id_seq', 16, true);


--
-- Name: performance_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.performance_metrics_id_seq', 22, true);


--
-- Name: performance_thresholds_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.performance_thresholds_id_seq', 4, true);


--
-- Name: sla_metrics_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.sla_metrics_id_seq', 22, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.users_id_seq', 22, true);


--
-- Name: webhook_config_id_seq; Type: SEQUENCE SET; Schema: public; Owner: infrawatch
--

SELECT pg_catalog.setval('public.webhook_config_id_seq', 1, false);


--
-- Name: alert_logs alert_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alert_logs
    ADD CONSTRAINT alert_logs_pkey PRIMARY KEY (id);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (id);


--
-- Name: email_config email_config_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.email_config
    ADD CONSTRAINT email_config_pkey PRIMARY KEY (id);


--
-- Name: endpoints_data endpoints_data_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints_data
    ADD CONSTRAINT endpoints_data_pkey PRIMARY KEY (id);


--
-- Name: endpoints_oids endpoints_oids_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints_oids
    ADD CONSTRAINT endpoints_oids_pkey PRIMARY KEY (id);


--
-- Name: endpoints endpoints_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints
    ADD CONSTRAINT endpoints_pkey PRIMARY KEY (id);


--
-- Name: failure_threshold_config failure_threshold_config_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.failure_threshold_config
    ADD CONSTRAINT failure_threshold_config_pkey PRIMARY KEY (id);


--
-- Name: incidents incidents_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_pkey PRIMARY KEY (id);


--
-- Name: performance_metrics performance_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.performance_metrics
    ADD CONSTRAINT performance_metrics_pkey PRIMARY KEY (id);


--
-- Name: performance_thresholds performance_thresholds_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.performance_thresholds
    ADD CONSTRAINT performance_thresholds_pkey PRIMARY KEY (id);


--
-- Name: sla_metrics sla_metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.sla_metrics
    ADD CONSTRAINT sla_metrics_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: webhook_config webhook_config_pkey; Type: CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.webhook_config
    ADD CONSTRAINT webhook_config_pkey PRIMARY KEY (id);


--
-- Name: alert_logs alert_logs_id_alert_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alert_logs
    ADD CONSTRAINT alert_logs_id_alert_fkey FOREIGN KEY (id_alert) REFERENCES public.alerts(id);


--
-- Name: alert_logs alert_logs_id_user_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alert_logs
    ADD CONSTRAINT alert_logs_id_user_fkey FOREIGN KEY (id_user) REFERENCES public.users(id);


--
-- Name: alerts alerts_id_endpoint_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_id_endpoint_fkey FOREIGN KEY (id_endpoint) REFERENCES public.endpoints(id);


--
-- Name: alerts alerts_id_user_assigned_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_id_user_assigned_fkey FOREIGN KEY (id_user_assigned) REFERENCES public.users(id);


--
-- Name: alerts alerts_id_user_created_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_id_user_created_fkey FOREIGN KEY (id_user_created) REFERENCES public.users(id);


--
-- Name: endpoints_data endpoints_data_id_end_point_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints_data
    ADD CONSTRAINT endpoints_data_id_end_point_fkey FOREIGN KEY (id_end_point) REFERENCES public.endpoints(id);


--
-- Name: endpoints endpoints_id_usuario_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints
    ADD CONSTRAINT endpoints_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES public.users(id);


--
-- Name: endpoints_oids endpoints_oids_id_end_point_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.endpoints_oids
    ADD CONSTRAINT endpoints_oids_id_end_point_fkey FOREIGN KEY (id_end_point) REFERENCES public.endpoints(id);


--
-- Name: incidents incidents_alert_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_alert_id_fkey FOREIGN KEY (alert_id) REFERENCES public.alerts(id);


--
-- Name: incidents incidents_endpoint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_endpoint_id_fkey FOREIGN KEY (endpoint_id) REFERENCES public.endpoints(id);


--
-- Name: incidents incidents_resolved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.incidents
    ADD CONSTRAINT incidents_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES public.users(id);


--
-- Name: performance_metrics performance_metrics_endpoint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.performance_metrics
    ADD CONSTRAINT performance_metrics_endpoint_id_fkey FOREIGN KEY (endpoint_id) REFERENCES public.endpoints(id);


--
-- Name: sla_metrics sla_metrics_endpoint_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: infrawatch
--

ALTER TABLE ONLY public.sla_metrics
    ADD CONSTRAINT sla_metrics_endpoint_id_fkey FOREIGN KEY (endpoint_id) REFERENCES public.endpoints(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: infrawatch
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;


--
-- PostgreSQL database dump complete
--

\unrestrict buH5pBc1yRWFGJvvUG4HLWQFruHzdV4lZHfNU6Xhnpikq6ZKi6swlK6KuClMgek

