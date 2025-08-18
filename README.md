# procurement-risk-model

## 📖 Project Overview

The **Procurement Risk Model** is both a research tool and a documented framework for identifying high-risk contracts in public procurement data. The goal of this project is to build something with tangible impact — a system that helps make the world more just and fair by holding businesses and governments accountable to transparent and competitive procurement practices. Fair competition benefits everyone, and this project is designed to highlight when the rules aren’t being followed.

At its core, the repository provides a reproducible workflow for analyzing procurement data to flag potential red flags such as non-competitive tenders, suspicious spending concentration, or unusually short bidding windows. While the current implementation is focused on **Mexico’s procurement data**, the model is designed to be extensible. The raw data source (Government Transparency Institute) provides CSV exports for over **40 countries**, meaning users can easily plug in other datasets and generate comparable risk analyses.

This project is intended to serve two audiences:
- **Technical users** who want to extend the codebase, adapt it for other countries, or build more advanced models (e.g., with machine learning and AI tools).  
- **Non-technical users** such as attorneys, investigators, and policymakers who need clear, data-driven indicators to identify high-risk entities and contracts as starting points for deeper investigations.

Ultimately, this repository documents what can be built with Python while also serving as a foundation for further projects in proactive risk monitoring and fraud detection.

## ✨ Features & Capabilities

The Procurement Risk Model provides a set of tools for analyzing public procurement data and flagging potential indicators of fraud or corruption risk. Current features include:

- **Aggregate Bidder Risk Scoring**  
  Generates a composite score for each bidder based on multiple red-flag indicators, making it easy to identify the riskiest entities.

- **Buyer & Market Summaries**  
  Produces summary reports of contracting authorities, spending patterns, and concentration of awards.

- **Red-Flag Modules**  
  The model evaluates several common risk signals in procurement data:
  - **Non-competitive tenders** – flags contracts awarded without open competition.  
  - **Spending concentration** – highlights when a single supplier consistently wins a large share of awards.  
  - **Short bid windows** – identifies contracts where the time to submit bids was unusually short.  
  - **Contract splitting** – detects when larger procurements may have been divided into smaller lots to bypass thresholds or oversight.  

- **Country-Specific Flexibility**  
  Currently configured for **Mexico’s procurement data**, but the system can be easily adapted to any of the 40+ countries with open CSV data from the Government Transparency Institute.

- **Extensible Framework**  
  Designed as a foundation for further development, including integration with **machine learning** or **AI tools** for advanced risk modeling.

- **Documentation & Transparency**  
  Clear output tables and summaries make the results accessible for both technical users (who can extend the code) and non-technical users (who can use the outputs to guide investigations).

