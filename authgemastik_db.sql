-- phpMyAdmin SQL Dump
-- version 6.0.0-dev+20251230.bbfa40bd98
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jan 12, 2026 at 04:45 PM
-- Server version: 8.4.3
-- PHP Version: 8.3.28

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `authgemastik_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE `feedback` (
  `id` int NOT NULL,
  `email` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `feedback` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `email` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `hashed_password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `gender` int DEFAULT NULL,
  `work` enum('Accountant','Doctor','Engineer','Lawyer','Manager','Nurse','Sales Representative','Salesperson','Scientist','Software Engineer','Teacher') CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `date_of_birth` date DEFAULT NULL,
  `age` int DEFAULT NULL,
  `weight` float DEFAULT NULL,
  `height` float DEFAULT NULL,
  `upper_pressure` int DEFAULT NULL,
  `lower_pressure` int DEFAULT NULL,
  `daily_steps` int DEFAULT NULL,
  `heart_rate` int DEFAULT NULL,
  `reset_token` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `role` varchar(255) COLLATE utf8mb4_general_ci DEFAULT 'user'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `email`, `hashed_password`, `created_at`, `name`, `gender`, `work`, `date_of_birth`, `age`, `weight`, `height`, `upper_pressure`, `lower_pressure`, `daily_steps`, `heart_rate`, `reset_token`, `role`) VALUES
(221, 'kahfi032004.kb.kb@gmail.com', '$2b$12$5OpwqpviOYd2OJ0lADDWju5Kp8KkcBeEmvH2pi62yBcZ2Kwz/lJV2', '2026-01-07 06:18:43', 'Kahfi Budianto', 1, 'Doctor', '2004-03-31', 21, 53, 149, 120, 80, 80, 50, NULL, 'user'),
(222, 'budiantokahfi95@gmail.com', '$2b$12$KxPWbBDd.7BQ09ufLrlfkuCKAe4eO4KVZNWSYdMJxaHLVlTNlGXs2', '2026-01-07 16:59:27', NULL, NULL, NULL, NULL, NULL, 0, 0, NULL, NULL, NULL, NULL, NULL, 'admin');

-- --------------------------------------------------------

--
-- Table structure for table `work_data`
--

CREATE TABLE `work_data` (
  `id` int NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `work_id` int DEFAULT NULL,
  `quality_of_sleep` float DEFAULT NULL,
  `physical_activity_level` float DEFAULT NULL,
  `stress_level` float DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `work_data`
--

INSERT INTO `work_data` (`id`, `title`, `email`, `work_id`, `quality_of_sleep`, `physical_activity_level`, `stress_level`) VALUES
(3, NULL, 'kahfi032004.kb.kb@gmail.com', 1, 5, 50, 5);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_feedback_id` (`id`),
  ADD KEY `ix_feedback_email` (`email`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_email` (`email`);

--
-- Indexes for table `work_data`
--
ALTER TABLE `work_data`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_work_data_title` (`title`),
  ADD KEY `email` (`email`),
  ADD KEY `ix_work_data_id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `feedback`
--
ALTER TABLE `feedback`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=223;

--
-- AUTO_INCREMENT for table `work_data`
--
ALTER TABLE `work_data`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `work_data`
--
ALTER TABLE `work_data`
  ADD CONSTRAINT `work_data_ibfk_1` FOREIGN KEY (`email`) REFERENCES `users` (`email`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
