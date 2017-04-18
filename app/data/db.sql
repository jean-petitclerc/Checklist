# python app/checklist.py shell
# from checklist import db
# db.create_all()

create index ix_section_01 on tcl_section(checklist_id, section_seq);

create index ix_step_01 on tcl_step(checklist_id, section_id, step_seq);

create unique index ix_cl_var_01 on tcl_var(checklist_id, var_id);
create unique index ix_cl_var_02 on tcl_var(var_id, checklist_id);
--
--
INSERT INTO "tadmin_user" VALUES(1,'Jean','Petitclerc','jean.petitclerc@groupepp.com','pbkdf2:sha1:1000$UW9prz0j$18052c6f0d6585136d2ba3208a442d21373640b0','1');

INSERT INTO "tchecklist" VALUES(2,'Stopper Oracle','Instructions détaillées pour stopper Oracle.','jean.petitclerc@groupepp.com','2017-02-22 16:02:01.185136','jean.petitclerc@groupepp.com','2017-03-23 06:18:04.425291','N');
INSERT INTO "tchecklist" VALUES(3,'Démarrer Oracle','Instructions détaillées pour démarrer Oracle','jean.petitclerc@groupepp.com','2017-02-22 16:02:41.929156','jean.petitclerc@groupepp.com','2017-03-02 22:13:14.194065','N');

INSERT INTO "tcl_section" VALUES(2,2,20,'Main Steps','main section','N');
INSERT INTO "tcl_section" VALUES(5,2,30,'Toute nouvelle section','blablabla','Y');
INSERT INTO "tcl_section" VALUES(6,2,10,'Pre-Steps','Préparation','N');
INSERT INTO "tcl_section" VALUES(8,2,30,'Post-Steps','Finalisation et ménage.','N');

INSERT INTO "tcl_step" VALUES(1,2,1,10,'pre-step 1','blablabla',NULL,NULL,'N');
INSERT INTO "tcl_step" VALUES(2,2,1,20,'pre-step 2','blablabla',NULL,NULL,'N');
INSERT INTO "tcl_step" VALUES(3,2,2,10,'Stopper l''instance','Utiliser soit sqlplus ou srvctl','oracle', 'sudo su - oracle
. profile_ora <DB_NAME>

sqlplus / as sysdba
shutdown immediate
exit

srvctl stop database -db <DB_NAME>','N');
INSERT INTO "tcl_step" VALUES(5,2,3,10,'post-step 1','blablabla',NULL,NULL,'N');
INSERT INTO "tcl_step" VALUES(8,2,6,10,'Blackout','Mettre un blackout dans Cloud','','','N');

INSERT INTO "tpredef_var" VALUES(1,'<DB_NAME>','Nom de la base de données');
INSERT INTO "tpredef_var" VALUES(2,'<DB_UNIQ_PRIM>','Nom de la base de données primaire');
INSERT INTO "tpredef_var" VALUES(3,'<DB_UNIQ_STDB>','Nom de la base de données de relève');
INSERT INTO "tpredef_var" VALUES(4,'<server_prim>','Nom du serveur où roule la BD primaire');
INSERT INTO "tpredef_var" VALUES(5,'<server_stdb>','Nom du serveur où roule la BD de relève');
