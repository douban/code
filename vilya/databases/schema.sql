CREATE SCHEMA IF NOT EXISTS `valentine` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci ;
USE `valentine` ;

-- -----------------------------------------------------
-- Table `valentine`.`users`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`users` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(200) NOT NULL ,
  `email` VARCHAR(255) NULL ,
  `password_digest` VARCHAR(200) NOT NULL ,
  `description` VARCHAR(1024) NULL ,
  `session_id` VARCHAR(16) NULL ,
  `session_expired_at` TIMESTAMP NULL ,
  `created_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  UNIQUE KEY `uk_email` (`email`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `valentine`.`projects`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`projects` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(200) NULL ,
  `description` VARCHAR(1024) NULL ,
  `upstream_id` INT UNSIGNED NULL ,
  `family_id` INT UNSIGNED NULL ,
  `owner_id` INT UNSIGNED NULL ,
  `creator_id` INT UNSIGNED NULL ,
  `created_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP ,
  PRIMARY KEY (`id`) ,
  UNIQUE KEY `idx_full_name` (`owner_id`, `name`),
  KEY `idx_name` (`name`),
  KEY `idx_owner` (`owner_id`),
  KEY `idx_network` (`owner_id`, `family_id`),
  KEY `idx_upstream` (`upstream_id`),
  KEY `idx_family` (`family_id`),
  KEY `idx_creator` (`creator_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `valentine`.`boards`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`boards` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(200) NOT NULL ,
  `position` INT NULL ,
  `role` INT NULL ,
  `description` VARCHAR(1024) NULL ,
  `number` INT UNSIGNED NULL ,
  `project_id` INT UNSIGNED NULL ,
  `creator_id` INT UNSIGNED NULL ,
  `created_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `archiver_id` INT UNSIGNED NULL ,
  `archived_at` TIMESTAMP NULL ,
  `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP ,
  PRIMARY KEY (`id`) ,
  UNIQUE KEY `uk_project_board` (`project_id`, `number`),
  KEY `idx_creator` (`creator_id`),
  KEY `idx_archiver` (`archiver_id`),
  KEY `idx_project_role` (`project_id`, `role`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `valentine`.`project_board_counters`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`project_board_counters` (
  `project_id` INT UNSIGNED NOT NULL ,
  `counter` INT UNSIGNED NOT NULL DEFAULT '1' ,
  PRIMARY KEY (`project_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `valentine`.`project_card_counters`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`project_card_counters` (
  `project_id` INT UNSIGNED NOT NULL,
  `counter` INT UNSIGNED NOT NULL DEFAULT '1',
  PRIMARY KEY (`project_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `valentine`.`cards`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`cards` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `name` VARCHAR(200) NOT NULL ,
  `position` INT NULL ,
  `description` TEXT NULL ,
  `number` INT UNSIGNED NULL ,
  `board_id` INT UNSIGNED NULL ,
  `project_id` INT UNSIGNED NULL ,
  `creator_id` INT UNSIGNED NULL ,
  `created_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ,
  `closer_id` INT UNSIGNED NULL ,
  `closed_at` TIMESTAMP NULL ,
  `archiver_id` INT UNSIGNED NULL ,
  `archived_at` TIMESTAMP NULL ,
  `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP ,
  PRIMARY KEY (`id`) ,
  UNIQUE KEY `uk_project_card` (`project_id`, `number`),
  KEY `idx_board` (`board_id`),
  KEY `idx_closer` (`closer_id`),
  KEY `idx_archiver` (`archiver_id`),
  KEY `idx_creator` (`creator_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `valentine`.`pulls`
-- -----------------------------------------------------
CREATE  TABLE IF NOT EXISTS `valentine`.`pulls` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT ,
  `card_id` INT UNSIGNED NOT NULL ,
  `origin_project_id` INT UNSIGNED NOT NULL ,
  `origin_project_ref` VARCHAR(1024) NOT NULL ,
  `upstream_project_id` INT UNSIGNED NOT NULL ,
  `upstream_project_ref` VARCHAR(1024) NOT NULL ,
  `origin_commit_sha` VARCHAR(40) NULL ,
  `upstream_commit_sha` VARCHAR(40) NULL ,
  `merged_commit_sha` VARCHAR(40) NULL ,
  `merged_at` TIMESTAMP NULL ,
  `creator_id` INT(11) UNSIGNED NOT NULL ,
  `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ,
  PRIMARY KEY (`id`) ,
  UNIQUE KEY `idx_card` (`card_id`) ,
  KEY `idx_project` (`upstream_project_id`) ,
  KEY `idx_merged` (`merged_commit_sha`) ,
  KEY `idx_upstream` (`upstream_project_id`, `upstream_project_ref`(255)) ,
  KEY `idx_origin` (`origin_project_id`, `origin_project_ref`(255)) ,
  KEY `idx_pull` (`upstream_project_id`, `origin_project_id`))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `valentine`.`organizations`
-- -----------------------------------------------------

CREATE  TABLE IF NOT EXISTS `valentine`.`organizations` (
  `id` INT(11) UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` INT(11) UNSIGNED NOT NULL,
  `owner_id` INT(11) UNSIGNED NOT NULL,
  `creator_id` INT(11) UNSIGNED NOT NULL,
  `created_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00',
  `updated_at` TIMESTAMP NOT NULL DEFAULT '0000-00-00 00:00:00' ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user` (`user_id`),
  KEY `idx_owner` (`owner_id`),
  KEY `idx_creator` (`creator_id`))
ENGINE=InnoDB;
