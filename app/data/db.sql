drop table if exists tuser;
create table tuser (
    user_name text primary key,
    user_pass text not null
);
insert into tuser values('jean','');

drop table if exists tadmin_user;
create table tadmin_user (
    user_id integer primary key autoincrement,
    first_name text not null,
    last_name text not null,
    user_email text not null,
    user_pass text not null,
    activated text not null default 'N'
);

drop table if exists tchecklist;
CREATE TABLE tchecklist (
    checklist_id   integer primary key autoincrement,
    checklist_name text      not null,
    checklist_desc text      not null default '',
    audit_crt_user text      not null default '',
    audit_crt_ts   timestamp not null,
    audit_upd_user text,
    audit_upd_ts   timestamp,
    deleted_ind    char(1)   not null default 'N'
);
create index checklist_x1 on tchecklist(checklist_name, checklist_id);
