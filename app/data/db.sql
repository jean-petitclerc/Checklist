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

drop table if exists tcl_section;
CREATE TABLE tcl_section(
    section_id     integer primary key autoincrement,
    checklist_id   integer not null,
    section_seq    integer not null,
    section_name   text    not null default '',
    section_detail text    not null default '',
    deleted_ind    char(1) not null default 'N'
);
create index cl_section_x1 on tcl_section(checklist_id, section_seq);

drop table if exists tcl_step;
CREATE TABLE tcl_step(
    step_id        integer primary key autoincrement,
    checklist_id   integer not null,
    section_id     integer not null,
    step_seq       integer not null,
    step_short     text    not null default '',
    step_detail    text    not null default '',
    deleted_ind    char(1) not null default 'N'
);
create index cl_step_x1 on tcl_step(checklist_id, section_id, step_seq);

drop table if exists tcl_step;
CREATE TABLE tcl_step(
    step_id        integer primary key autoincrement,
    checklist_id   integer not null,
    section_id     integer not null,
    step_seq       integer not null,
    step_short     text    not null default '',
    step_detail    text    default null,
    step_code      text    default null,
    step_user      text    default null,
    deleted_ind    char(1) not null default 'N'
);
create index cl_step_x1 on tcl_step(checklist_id, section_id, step_seq);

--
alter table tcl_step rename to tcl_step_old;
drop index cl_step_x1;

create table ...

insert into tcl_step (step_id, checklist_id, section_id, step_seq, step_short, step_detail, step_code,
                      step_user, deleted_ind)
       select step_id, checklist_id, section_id, step_seq, step_short, step_detail, step_code,
              null, deleted_ind
         from tcl_step_old;

--
insert into tcl_section values(1, 2, 10, 'section 1', 'pre-steps', 'N');
insert into tcl_section values(2, 2, 20, 'section 2', 'main section', 'N');
insert into tcl_section values(3, 2, 30, 'section 3', 'post-step', 'N');

insert into tcl_step values(1, 2, 1, 10, 'pre-step 1', 'blablabla', 'N');
insert into tcl_step values(2, 2, 1, 20, 'pre-step 2', 'blablabla', 'N');
insert into tcl_step values(3, 2, 2, 10, 'step 1', 'blablabla', 'N');
insert into tcl_step values(4, 2, 2, 20, 'step 2', 'blablabla', 'N');
insert into tcl_step values(5, 2, 3, 10, 'post-step 1', 'blablabla', 'N');
