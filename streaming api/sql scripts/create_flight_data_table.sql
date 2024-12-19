-- Table: public.schiphol_traffic

-- DROP TABLE IF EXISTS public.schiphol_traffic;

CREATE TABLE IF NOT EXISTS public.schiphol_traffic
(
    addr character varying(10) COLLATE pg_catalog."default",
    lat double precision,
    lon double precision,
    track integer,
    alt integer,
    speed integer,
    squawk character varying(10) COLLATE pg_catalog."default",
    radar_id character varying(10) COLLATE pg_catalog."default",
    model character varying(20) COLLATE pg_catalog."default",
    reg character varying(10) COLLATE pg_catalog."default",
    last_update integer,
    origin character varying(10) COLLATE pg_catalog."default",
    destination character varying(10) COLLATE pg_catalog."default",
    flight character varying(10) COLLATE pg_catalog."default",
    on_ground integer,
    vert_speed integer,
    callsign character varying(10) COLLATE pg_catalog."default",
    source_type character varying(50) COLLATE pg_catalog."default",
    eta integer,
    enhanced jsonb,
    flightid character varying(20) COLLATE pg_catalog."default",
    geom geometry(Point,4326),
    id integer NOT NULL DEFAULT nextval('schiphol_traffic_id_seq'::regclass),
    created_at timestamp without time zone DEFAULT now(),
    last_update_to_time timestamp without time zone,
    CONSTRAINT schiphol_traffic_pkey PRIMARY KEY (id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.schiphol_traffic
    OWNER to pilot;