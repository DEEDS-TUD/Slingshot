SET FOREIGN_KEY_CHECKS=0;
DROP TABLE IF EXISTS function;
CREATE TABLE function(
  ID                int NOT NULL AUTO_INCREMENT,
  name              varchar(255) NOT NULL,
  tcl               varchar(255),
  header            varchar(255),
  number_of_params  int NOT NULL,
  c_types           varchar(255),
  signature         varchar(255),
  return_val        varchar(255),
  /* Keys */
  PRIMARY KEY (ID, tcl)
);
DROP TABLE IF EXISTS datatype;
CREATE TABLE datatype(
  ID        int NOT NULL AUTO_INCREMENT,
  name      varchar(255),
  type   varchar(255),
  include   TEXT,
  define    TEXT,
  /* keys */
  PRIMARY KEY (ID)
);
DROP TABLE IF EXISTS failures;
CREATE TABLE failures(
  ID        int NOT NULL,
  name      varchar(255),
  /* keys */
  PRIMARY KEY (ID)
);
DROP TABLE IF EXISTS result;
CREATE TABLE result(
  ID        int NOT NULL AUTO_INCREMENT,
  tcl       varchar(255) NOT NULL,
  f_ref     int NOT NULL,
  tc_ref    int NOT NULL,
  fail_ref     int NOT NULL,
  /* keys */
  PRIMARY KEY (ID, tcl),
  FOREIGN KEY (f_ref) REFERENCES function(ID)
    ON DELETE CASCADE,
  FOREIGN KEY (fail_ref) REFERENCES failures(ID)
    ON DELETE CASCADE
);
DROP TABLE IF EXISTS setting;
CREATE TABLE setting(
  ID           int NOT NULL AUTO_INCREMENT,
  name         varchar(255),
  code         TEXT,
  commit_code  TEXT,
  cleanup_code TEXT,
  dt_ref       int NOT NULL,
  /* keys */
  PRIMARY KEY (ID),
  FOREIGN KEY (dt_ref) REFERENCES datatype(ID)
    ON DELETE CASCADE
);
DROP TABLE IF EXISTS testcase;
CREATE TABLE testcase(
  ID           int NOT NULL AUTO_INCREMENT,
  f_ref        int,
  /* keys */
  PRIMARY KEY (ID),
  FOREIGN KEY (f_ref) REFERENCES function(ID)
    ON DELETE CASCADE
);
SET FOREIGN_KEY_CHECKS=1;
