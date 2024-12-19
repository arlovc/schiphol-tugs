-- select * from schiphol_bbox

-- drop table schiphol_old

-- create table schiphol_bbox  as select id, geom from schiphol;


-- create table schiphol_traffic as select * from flight_data limit 1

-- drop table traffic_schiphol

-- select * from schiphol_traffic

update schiphol_traffic set geom = ST_SetSRID(ST_MakePoint(lon,lat),4326) where geom is null;
-- alter table schiphol_traffic add column created_at timestamp;
-- ALTER TABLE schiphol_traffic alter COLUMN created_at SET DEFAULT now();

-- alter table schiphol_traffic add column last_update_to_time timestamp
-- update schiphol_traffic set last_update_to_time = TIMEZONE('Europe/Amsterdam', TO_TIMESTAMP(last_update));
update schiphol_traffic set last_update_to_time = TIMEZONE('Europe/Amsterdam', TO_TIMESTAMP(last_update)) where last_update_to_time is null;

-- delete from schiphol_traffic

--    ALTER TABLE schiphol_traffic ADD COLUMN id SERIAL PRIMARY KEY;
--    alter table schiphol_traffic drop column id;
--    select * from schiphol_traffic

-- delete from schiphol_traffic
-- select * from schiphol_traffic order by created_at desc;
-- select * from pg_timezone_names
select count(*) from schiphol_traffic;

-- select * from schiphol_traffic order by created_at asc limit 10;