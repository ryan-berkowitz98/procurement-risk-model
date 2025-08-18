# procurement-risk-model

## 📖 Project Overview

The **Procurement Risk Model** is both a research tool and a documented framework for identifying high-risk contracts in public procurement data. The goal of this project is to build something with tangible impact — a system that helps make the world more just and fair by holding businesses and governments accountable to transparent and competitive procurement practices. Fair competition benefits everyone, and this project is designed to highlight when the rules aren’t being followed.

At its core, the repository provides a reproducible workflow for analyzing procurement data to flag potential red flags such as non-competitive tenders, suspicious spending concentration, or unusually short bidding windows. While the current implementation is focused on **Mexico’s procurement data**, the model is designed to be extensible. The raw data source ([Government Transparency Institute](https://www.govtransparency.eu/)) provides CSV exports for over **40 countries**, meaning users can easily plug in other datasets and generate comparable risk analyses.

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
  - **Spending concentration** – highlights when a single supplier consistently wins a large share of awards from a single buyer.  
  - **Short bid windows** – identifies contracts where the time to submit bids was unusually short.  
  - **Contract splitting** – detects when larger procurements may have been divided into smaller lots to bypass thresholds or oversight.  

- **Country-Specific Flexibility**  
  Currently configured for **Mexico’s procurement data**, but the system can be easily adapted to any of the 40+ countries with open CSV data from the Government Transparency Institute.

- **Extensible Framework**  
  Designed as a foundation for further development, including integration with **machine learning** or **AI tools** for advanced risk modeling.

- **Documentation & Transparency**  
  Clear output tables and summaries make the results accessible for both technical users (who can extend the code) and non-technical users (who can use the outputs to guide investigations).


## ⚙️ Installation & Setup

This project is designed to support both **non-technical** and **technical** audiences. Choose the path that fits your role and needs:

### 🧑‍💼 For Non-Technical Users

- You can start exploring the results immediately by downloading the **`MX_procurement_risk_report.xlsx`** file from the `output/` folder in this repository.  
  This file contains a risk report already generated for **Mexico’s procurement data**.  
- The meaning of each red flag indicator will be covered in depth later in this README.  
- If you’d like to see results for a **different country**, you have two options:  
  1. **Contact me directly** and I can run the model for you.  
  2. Work with a **data scientist or technical colleague** who can run the model internally using the instructions below.


### 👩‍💻 For Technical Users

1. **Clone the repository**
   ```bash
   git clone https://github.com/ryan-berkowitz98/procurement-risk-model.git
   cd procurement-risk-model

2. **Set up a Python environment**  
   - Python 3.9+ is recommended.  
   - Install dependencies:  
  
     ```bash
     pip install -r requirements.txt
     ```

3. **Prepare the input data**
    - **Choose a country.** See the list of supported countries in the [data brief (p.4)](https://www.govtransparency.eu/wp-content/uploads/2024/04/Fazekas-et-al_Global-PP-data_published_2024.pdf).
    - **Download the country-level CSV.** Use the [Global Contract-Level Public Procurement Dataset](https://www.govtransparency.eu/global-contract-level-public-procurement-dataset/) (maintained by the **Government Transparency Institute**) or go directly to the [dataset download index](https://input.mendeley.com/inputsets/fwzpywbhgw/3).
    - **Place the file in `input/`.** Name it using the convention:
    
       `{country_code}_DIB_[YYYY].csv`  
       Example: `MX_DIB_2023.csv`

4. **Run the pipeline**
  - Each script in the `src/` directory is modular and can be executed from the command line or within a Python environment.
  - A typical run might look like:
    ```bash
    python src/01_input.py
    python src/02_clean_transform.py
    python src/03_flag_non_competitive.py
    ...
    python src/99_export_risk_report.py
  - Final outputs (including Excel summaries and flagged risk tables) will be written to the '/output' directory.
  

## 📊 Outputs

Running the pipeline generates a Excel risk report in the `output/` directory. Most users will start with the Excel report:

### Primary report
- **`output/{country_code}_procurement_risk_report.xlsx`**
  - A consolidated workbook with high-level summaries and red-flag tables.

#### Workbook tabs
- **Bidder Risk Summary**  
  Aggregated risk score per bidder based on multiple indicators.  
  _Key columns:_ `Bidder Name`, `Bidder Country`, `Total Risk Score`, `Total Dollars At Risk`, `Number of Risk Flags`.

- **Buyer Summary**  
  Contracting authority overview: spend, award counts, and concentration.  
  _Key columns:_ `Buyer Name`, `Buyer Country`, `Total Payouts`, `Top Bidder`.

- **Non-Comp Flag**  
  Summary of awards made with limited or no competition.  
  _Key columns:_ `Bidder Name`, `Bidder Country`, `Non Competitive Tenders Won`, `Non Competitive Dollars At Risk`, `Non Competitive Tenders Risk Score`.

- **Spending Concentration Flag**  
  Summary of buyers that captured an outsized share of tenders or payments from a buyer in a single year.  
  _Key columns:_ `Bidder Name`, `Bidder Country`, `Spending Concentration Count`, `Spending Concentration Dollars At Risk`, `Spending Concentration Risk Score`.

- **Short Bid Windows Flag**  
  Summary of bidders that won tenders with unusually short time between publication and deadline.  
  _Key columns:_ `Bidder Name`, `Bidder Country`, `Short Bid Window Count`, `Avg Short Bid Window Days`, `Short Bid Window Dollars At Risk`, `Short Bid Window Risk Score`.

- **Contract Splitting Flag**  
  Summary of bidders participating in potential splitting of procurements across similar items/time/windows to avoid thresholds.  
  _Key columns:_ `Bidder Name`, `Bidder Country`, `Contract Split Clusters Count`, `Avg Contracts Per Cluster`, `Max Contracts in Cluster Count`, `Contract Splitting Dollars At Risk`, `Contract Splitting Risk Score`.

> Note: `output/ancillary/` contains intermediate artifacts and is ignored by Git.

---

### How to read the results (quick guide)

- **Risk score = heat level.** A higher score simply means “look here first.” It’s a triage signal, not a final judgment.
- **Flags = clues, not proof.** Each flag points to a pattern (e.g., no competition, short bid window). Use them to form a hypothesis, then verify in the source docs.
- **Quick workflow:**
  1. Open **Bidder Risk Summary** and sort by `risk_score` (highest first).
  2. Filter for `Number of Risk Flags ≥ 2` to find stronger signals.
  3. Cross-check the same bidders/buyers across other tabs (Non-Comp, Concentration, Short Windows, Splitting). Names that repeat move up the priority list.
  4. Focus first on records with **larger spend** or **more awards** (higher potential impact).
- **Then dive deeper:** Investigate the entities behind each name—owners, shareholders, and parent/affiliate links. Repeat offenders often re-incorporate under new names. Look for continuity signals like:
  - Shared directors/officers or overlapping shareholders
  - Common addresses, phone numbers, or email domains
  - Reused tax IDs/registration numbers (where available)
  - Identical websites or branding across “new” companies






