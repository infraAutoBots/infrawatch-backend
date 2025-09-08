PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE endpoints (
	id INTEGER NOT NULL, 
	ip VARCHAR, 
	interval INTEGER, 
	version VARCHAR, 
	community VARCHAR, 
	port INTEGER, 
	user VARCHAR, 
	"authKey" VARCHAR, 
	"privKey" VARCHAR, 
	id_usuario INTEGER, nickname VARCHAR, active BOOLEAN, 
	PRIMARY KEY (id), 
	FOREIGN KEY(id_usuario) REFERENCES users (id)
);
INSERT INTO endpoints VALUES(1,'127.0.0.1',30,'2c','public',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(2,'127.0.0.2',30,'2c','public',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(3,'127.0.0.3',30,'2c','public',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(5,'192.168.8.146',30,'','',0,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(6,'127.0.0.4',30,'2c','public',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(7,'127.0.0.5',30,'','',0,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(8,'8.8.8.8',30,'','',0,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(9,'dgg.gg',30,'','',0,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(10,'127.0.0.11',30,'1','public',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(11,'127.0.0.12',30,'2c','public',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(12,'127.0.0.13',30,'3','',161,'','','',2,NULL,1);
INSERT INTO endpoints VALUES(13,'192.168.0.3',40,'','',0,'','','',2,'',1);
INSERT INTO endpoints VALUES(14,'1.1.1.1',30,'','',0,'','','',2,'',1);
INSERT INTO endpoints VALUES(15,'2.1.1.1',30,'','',0,'','','',2,'',0);
INSERT INTO endpoints VALUES(16,'3.1.1.1',30,'','',0,'','','',2,'',1);
INSERT INTO endpoints VALUES(17,'192.168.1.100',30,'2c','public',161,'','','',2,'Test Endpoint',1);
COMMIT;
