DROP DATABASE IF EXISTS recycle;
CREATE DATABASE
IF NOT EXISTS recycle;
USE `recycle`;

CREATE TABLE `electronics` (
  `id` bigint
(20) NOT NULL AUTO_INCREMENT,
    `name` TEXT,
    `notes` TEXT,
    `fullAddress` TEXT,
    `city` TEXT,
    `province` TEXT,
    `postalCode` TEXT,
    `lat` DECIMAL(10, 8),
    `lon` DECIMAL(11, 8),
    PRIMARY KEY
(`id`)
) 