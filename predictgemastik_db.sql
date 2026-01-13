-- phpMyAdmin SQL Dump
-- version 6.0.0-dev+20251230.bbfa40bd98
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Jan 12, 2026 at 04:53 PM
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
-- Database: `predictgemastik_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `daily`
--

CREATE TABLE `daily` (
  `id` int NOT NULL,
  `email` varchar(255) NOT NULL,
  `date` date NOT NULL,
  `upper_pressure` int DEFAULT NULL,
  `lower_pressure` int DEFAULT NULL,
  `daily_steps` int DEFAULT NULL,
  `heart_rate` int DEFAULT NULL,
  `duration` float NOT NULL,
  `prediction_result` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `daily`
--

INSERT INTO `daily` (`id`, `email`, `date`, `upper_pressure`, `lower_pressure`, `daily_steps`, `heart_rate`, `duration`, `prediction_result`) VALUES
(1, 'kahfi032004.kb.kb@gmail.com', '2026-01-07', 120, 80, 80, 50, 0.0224907, 2),
(2, 'kahfi032004.kb.kb@gmail.com', '2026-01-10', 120, 80, 80, 0, 0, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `monthly_predictions`
--

CREATE TABLE `monthly_predictions` (
  `id` int NOT NULL,
  `email` varchar(255) NOT NULL,
  `prediction_result` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sleep_records`
--

CREATE TABLE `sleep_records` (
  `id` int NOT NULL,
  `email` varchar(255) NOT NULL,
  `sleep_time` datetime NOT NULL,
  `wake_time` datetime NOT NULL,
  `duration` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `sleep_records`
--

INSERT INTO `sleep_records` (`id`, `email`, `sleep_time`, `wake_time`, `duration`) VALUES
(1, 'kahfi032004.kb.kb@gmail.com', '2026-01-07 18:36:39', '2026-01-07 18:38:00', 0.0224907);

-- --------------------------------------------------------

--
-- Table structure for table `weekly_predictions`
--

CREATE TABLE `weekly_predictions` (
  `id` int NOT NULL,
  `email` varchar(255) NOT NULL,
  `prediction_result` enum('Insomnia','Normal','Sleep Apnea') NOT NULL,
  `prediction_date` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `daily`
--
ALTER TABLE `daily`
  ADD PRIMARY KEY (`id`),
  ADD KEY `email` (`email`);

--
-- Indexes for table `monthly_predictions`
--
ALTER TABLE `monthly_predictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `email` (`email`);

--
-- Indexes for table `sleep_records`
--
ALTER TABLE `sleep_records`
  ADD PRIMARY KEY (`id`),
  ADD KEY `email` (`email`);

--
-- Indexes for table `weekly_predictions`
--
ALTER TABLE `weekly_predictions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `daily`
--
ALTER TABLE `daily`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `monthly_predictions`
--
ALTER TABLE `monthly_predictions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sleep_records`
--
ALTER TABLE `sleep_records`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `weekly_predictions`
--
ALTER TABLE `weekly_predictions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
