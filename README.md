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

---

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

Running the pipeline generates a set of artifacts in the `output/` directory. Most users will start with the Excel report:

### Primary report
- **`output/MX_procurement_risk_report.xlsx`**
  - A consolidated workbook with high-level summaries and red-flag tables.

#### Workbook tabs
- **Bidder Risk Summary**  
  Aggregated risk score per bidder based on multiple indicators.  
  _Key columns:_ `bidder_id`, `bidder_name`, `risk_score`, `flags_triggered`, `total_awards`, `total_award_value_usd`.

- **Buyer Summary**  
  Contracting authority overview: spend, award counts, and concentration.  
  _Key columns:_ `buyer_id`, `buyer_name`, `award_count`, `total_spend_usd`, `top_bidder_share`.

- **Non-Comp Flag**  
  Awards made with limited or no competition.  
  _Key columns:_ `tender_id`, `buyer_name`, `bidder_name`, `procedure_type`, `award_value_usd`, `award_date`, `non_competitive_flag`.

- **Spending Concentration Flag**  
  Buyer–supplier pairs where one supplier captures an outsized share.  
  _Key columns:_ `buyer_name`, `bidder_name`, `share_of_buyer_spend`, `award_count`, `total_award_value_usd`.

- **Short Bid Windows Flag**  
  Tenders with unusually short time between publication and deadline.  
  _Key columns:_ `tender_id`, `buyer_name`, `bid_window_days`, `award_value_usd`, `award_date`, `short_window_flag`.

- **Contract Splitting Flag**  
  Potential splitting of procurements across similar items/time/windows to avoid thresholds.  
  _Key columns:_ `cluster_id`, `buyer_name`, `suspected_splits_count`, `sum_award_value_usd`, `time_window_days`.

> Note: `output/ancillary/` contains intermediate artifacts and is ignored by Git.

---

### How to read the results (quick guide)
- **Risk scores**: Higher scores = more concerning pattern combinations across flags.  
- **Flags are directional, not dispositive**: Use them as starting points for human review/investigation.  
- **Cross-reference**: Prioritize entities appearing in multiple tabs (e.g., a bidder flagged for both non-competitive awards and buyer-spend concentration).

---




