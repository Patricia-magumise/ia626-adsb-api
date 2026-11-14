-- Run once on the ia626 database (phpMyAdmin SQL tab or mysql client).
-- Creates the auth and logging tables and adds the valid key 123.

CREATE TABLE IF NOT EXISTS `magumip_auth` (
    `id`    INT AUTO_INCREMENT PRIMARY KEY,
    `token` VARCHAR(64) NOT NULL UNIQUE,
    `owner` VARCHAR(64) NULL
);

INSERT IGNORE INTO `magumip_auth` (`token`, `owner`) VALUES ('123', 'class');

CREATE TABLE IF NOT EXISTS `magumip_api_logs` (
    `id`       INT AUTO_INCREMENT PRIMARY KEY,
    `endpoint` VARCHAR(64)  NOT NULL,
    `token`    VARCHAR(64)  NULL,
    `response` VARCHAR(255) NULL,   
    `dt`       DATETIME     NOT NULL
);
