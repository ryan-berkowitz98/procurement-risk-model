# Global Procurement Risk Model  

## 📖 Project Overview

The **Global Procurement Risk Model** is both a research tool and a documented framework for identifying high-risk contracts in public procurement data. The goal of this project is to build something with tangible impact — a system that helps make the world more just and fair by holding businesses and governments accountable to transparent and competitive procurement practices. Fair competition benefits everyone, and this project is designed to highlight when the rules aren’t being followed.

At its core, the repository provides a reproducible workflow for analyzing procurement data to flag potential red flags such as non-competitive tenders, suspicious spending concentration, or unusually short bidding windows. While the current implementation is focused on **Mexico’s procurement data**, the model is designed to be extensible. The raw data source ([Government Transparency Institute](https://www.govtransparency.eu/)) provides CSV exports for over **40 countries**, meaning users can easily plug in other datasets and generate comparable risk analyses.

This project is intended to serve two audiences:
- **Technical users** who want to extend the codebase, adapt it for other countries, or build more advanced models (e.g., with machine learning and AI tools).  
- **Non-technical users** such as attorneys, investigators, and policymakers who need clear, data-driven indicators to identify high-risk entities and contracts as starting points for deeper investigations.

Ultimately, this repository documents what can be built with Python while also serving as a foundation for further projects in proactive risk monitoring and fraud detection.

## ✨ Features & Capabilities

The Procurement Risk Model provides a set of tools for analyzing public procurement data and flagging potential indicators of fraud or corruption risk. Current features include:

- **Aggregate Bidder Risk Scoring**  
  Generates a composite score for each bidder based on multiple red-flag indicators, making it easy to identify the riskiest entities.

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
  - Final outputs (including Excel summaries and more detailed flagged risk parquet files) will be written to the '/output' directory.
  

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
 

## 🧭 Red-Flag Definitions & Methodology

This project computes several directional indicators (“flags”). Flags are **clues, not proof**—use them to prioritize human review.

### How scoring works (high level)

- Each module emits a flag and a **module risk score** that is a **percentile rank scaled 0–100** (100 = highest risk relative to peers in the dataset).
- The **aggregate bidder risk score** is the **evenly weighted average across all modules** (e.g., Non-Competitive, Spending Concentration, Short Bid Windows, Contract Splitting).  
  **If a module is missing for a bidder, that module’s score is treated as 0.**
  - Example: `aggregate = (NC + CONC + SHORT + SPLIT) / 4`
- Higher scores = higher review priority. 

---

### 🔴 Non-Competitive Tenders

**What it flags (plain English):** contracts awarded with little or no real competition (e.g., direct awards or single-bidder tenders). Repeated success in these deals can be a warning sign.

**Why it matters:** when open competition is skipped, the risk of favoritism, waste, or corruption goes up. This module helps you spot suppliers who rely heavily on such awards.

#### What the module does
1. **Finds non-competitive awards** (pre-tagged earlier in the pipeline).
2. **Totals, per supplier:** how many non-competitive awards they won and how much those are worth.
3. **Calculates shares:**  
   - What **percent of the supplier’s wins** were non-competitive?  
   - What **percent of their total payments** came from non-competitive awards?
4. **Identifies the top buyer** paying that supplier for non-competitive awards.
5. **Applies minimum thresholds** to ignore trivial cases (see below).
6. **Ranks suppliers** with a simple risk score: more non-competitive wins **and** higher dependence on them → higher score.

#### Risk scoring (0–100)
For each supplier:
- Compute a **percentile rank** of their `non_competitive_tenders_won` among all suppliers (0–1).
- Multiply by their **percent** of wins that are non-competitive.  
- **Score = percentile × share × 100.**

> Scores are percentile-based (0–100). **100 = highest relative risk** in this dataset.

#### How to use it
- Sort the **summary** by `non_competitive_tenders_risk_score` (highest first).
- Prioritize suppliers with **many** non-competitive wins **and** a **high percentage** of their business from them.
- Look at the **top buyer** column—repeat pairings with the same buyer merit attention.
- Cross-reference with **Spending Concentration**, **Short Bid Windows**, and **Contract Splitting** for stronger signals.

#### Outputs (Parquet)
- **Detail file:** `output/ancillary/{COUNTRY}_non_competitive_tenders_all.parquet`  
  Every non-competitive contract for drill-down (who bought what, when, how much).
- **Supplier summary:** `output/ancillary/{COUNTRY}_non_competitive_tenders_summary.parquet`  
  One row per supplier with counts, dollars, shares, top buyer, and **risk score** (feeds the overall aggregate score).

#### Thresholds & caveats
- Flags only suppliers with:  
  - **≥ 1** non-competitive award, **and**  
  - **non-competitive dollars** ≥ `NON_COMP_DOLLAR_THRESHOLD`, **and**  
  - **at least one** non-competitive award ≥ `NON_COMP_MAX_TENDER_THRESHOLD`.  
  *(Tune these in `config.py` to match your risk tolerance.)*
- Percentages guard against divide-by-zero and ignore infinities; missing denominators become 0.
- A single large direct award can elevate a supplier—use the **detail file** to validate context.

---

### 🔴 Spending Concentration (Buyer → Supplier)

**What it flags:** cases where a **single government buyer** gives a **large share** of its open-tender awards (by **$, count**, or both) to the **same supplier** within a year. Even in “open” competitions, this pattern can hint at favoritism or weak competition.

**Why it matters:** if one supplier consistently captures a big slice of a buyer’s awards, it can signal reduced competition, steering, or cozy relationships—worth a closer look.

#### What the module does
1. **Focus on open tenders only** (non-competitive awards are excluded here).
2. For each **buyer × year**, compute totals:
   - awards **count** and **payments ($)**.
3. For each **buyer × supplier × year**, compute that supplier’s share of the buyer’s year:
   - `% of tenders` and `% of payments`.
4. **Basic quality gate:** ignore buyer-years with only **1 award** (avoids trivial 100% shares).
5. **Flag high-concentration cases** when, in a given buyer-year, a supplier has:
   - **> 10%** of the buyer’s **payments** **OR** **> 10%** of the buyer’s **tender count**, **AND**
   - at least **$1,000,000** paid to that supplier in that year.
6. For context, identify each supplier’s **top buyer** (the buyer who paid them the most across all years).

#### Risk scoring (0–100)
For each supplier:
- Sum their flagged **% of tenders** and **% of payments** across all flagged buyer-years.
- Convert each sum to a **percentile rank** among suppliers (0–1).
- **Score = (tenders percentile) × (payments percentile) × 100.**
  - Suppliers who are **high on both dimensions** rise to the top.

> Scores are percentile-based (0–100). **100 = highest relative risk** in this dataset.

#### How to use it
- Open the **summary** and sort by `spending_concentration_risk_score` (highest first).
- Prioritize suppliers with **many flagged years** *and* **large dollars at risk**.
- Check the **top buyer** column—repeat pairings with the same buyer merit attention.
- Cross-reference with the **Non-Competitive** and **Short Bid Window** flags for stronger signals.

#### Outputs (Parquet)
- **Detailed cases:** `output/ancillary/{COUNTRY}_spending_concentration_all.parquet`  
  One row per **buyer → supplier → year** that met the thresholds (with shares and dollars).
- **Supplier summary:** `output/ancillary/{COUNTRY}_spending_concentration_summary.parquet`  
  One row per **supplier** with: total dollars at risk, count of flagged cases, top buyer, and **risk score**.

#### Thresholds & caveats
- Current thresholds: **10%** share (payments **or** tenders) **and** **$1,000,000** annual paid to the supplier; buyer-years with only **1 award** are excluded.
- Thresholds are set **in the script**; adjust to fit your risk tolerance (e.g., raise the dollar floor).
- A high share at a **small buyer** can still appear—verify materiality using the dollars columns.

---

### 🔴 Short Bidding Windows

**What it flags:** tenders where the time to submit bids is unusually short. Very tight windows can tilt the playing field toward a pre-selected supplier.

**Why it matters:** when suppliers don’t have enough time to prepare bids, genuine competition drops. Repeated wins under short windows can indicate steering or process manipulation.

#### What the module does
1. **Focuses on open tenders only** (non-competitive awards are excluded here).
2. **Builds the bidding window (in days):** from first publication date → bid deadline.  
   - If the deadline is missing, it **fills** it using the earliest downstream milestone (award/contract dates) so we can still measure time.
3. **Keeps sensible windows & material tenders:**  
   - Only positive windows, capped at **≤ 365 days**.  
   - Filters to tenders **≥ $1,000,000** to focus on meaningful awards.
4. **Finds a dynamic threshold:** the **10th percentile** of observed bidding windows in the dataset (not hard-coded).
5. **Flags short-window tenders:** anything **below** that threshold.
6. **Summarizes by supplier:** counts, average and minimum window length, average payment, total dollars at risk, and the **top buyer** for that supplier.
7. **Visualizes the distribution:** saves a histogram with the **threshold, mean, and median** marked.

#### Risk scoring (0–100)
For each supplier:
- Convert the **count of short-window wins** to a percentile rank (0–1).
- Convert the **average window length** to a percentile rank and **invert** it (shorter → higher risk).
- **Score = count_percentile × (1 − avg_days_percentile) × 100.**

> Scores are percentile-based (0–100). **100 = highest relative risk** in this dataset.

#### How to use it
- Sort the **summary** by `short_bid_window_risk_score` (highest first).
- Prioritize suppliers with **many** short-window wins and **very short** average windows.
- Check the **top buyer** column for repeat buyer–supplier patterns.
- Cross-reference with **Non-Competitive** and **Spending Concentration** flags for stronger signals.

#### Outputs
- **Detail file (Parquet):** `output/ancillary/{COUNTRY}_short_bid_window_all.parquet`  
  Every flagged tender with dates, window length, buyer/supplier, and value.
- **Supplier summary (Parquet):** `output/ancillary/{COUNTRY}_short_bid_window_summary.parquet`  
  One row per supplier with counts, averages, dollars at risk, top buyer, and **risk score**.
- **Visualization (PNG):** `output/ancillary/{COUNTRY}_short_bid_window_histogram.png`  
  Distribution of bidding windows with the dynamic threshold, mean, and median.

#### Thresholds & caveats
- Dynamic threshold = **10th percentile** of observed windows (dataset-specific).  
- Materiality filter: only tenders **≥ $1,000,000** included in this module.  
- Date quality matters: if publication/award/contract dates are missing or noisy, results can be conservative.  
- A few short-window wins at a small buyer may still appear—use dollars at risk to gauge impact.

---

### 🔴 Contract Splitting

**What it flags:** patterns where several **similar, sub-threshold contracts** are awarded to the **same supplier** within a **short time window**. This can suggest a larger buy was split to avoid oversight thresholds.

**Why it matters:** splitting can bypass approvals, reduce transparency, and steer awards. Clusters of small, look-alike contracts in a few days are a classic warning sign.

#### What the module does
1. **Preps the data:** parses key dates, normalizes titles (lowercase, remove punctuation), and ensures values are numeric.
2. **Sets scope:** focuses on suppliers whose **total payments** exceed an **approval threshold** (default **$10,000,000**).
3. **Looks for sub-threshold awards:** keeps each supplier’s **individual tenders below** that threshold.
4. **Builds similarity clusters per supplier:**  
   - Connects tenders that are **close in time** (default **≤ 7 days**) **and** have **similar titles** (SequenceMatcher ratio **≥ 0.5**).  
   - Uses graph **connected components** to form candidate clusters, then re-splits any that exceed the time window.
5. **Keeps meaningful clusters:** at least **2 contracts** and **≥ $1,000,000** total value.
6. **Summarizes per supplier:** number of clusters, average/max contracts per cluster, dollars at risk, and a percentile-based **risk score**.

#### Risk scoring (0–100)
For each supplier:
- Convert **cluster count** to a percentile rank (0–1).
- Convert **average contracts per cluster** to a percentile rank (0–1).
- **Score = count_percentile × avg_size_percentile × 100.**

> Scores are percentile-based (0–100). **100 = highest relative risk** in this dataset.

#### How to use it
- Sort the **summary** by `contract_splitting_risk_score` (highest first).
- In the **detail** file, inspect clusters with:
  - **Many contracts** in **few days**,
  - **Very similar titles**, and
  - **Single or small set of buyers** (check `buyer_count` / `buyers` list).
- Cross-reference with **Short Bidding Windows** and **Spending Concentration** to strengthen the hypothesis.

#### Outputs (Parquet)
- **Cluster details:** `output/ancillary/{COUNTRY}_contract_split_all.parquet`  
  One row per detected cluster with: `cluster_id`, date span, number of contracts, total/avg value, buyers, titles, and tender IDs.
- **Supplier summary:** `output/ancillary/{COUNTRY}_contract_split_summary.parquet`  
  One row per supplier with cluster counts, sizes, dollars at risk, and **risk score**.

#### Thresholds & caveats
- Defaults: `approval_threshold = $10,000,000`, `time_window_days = 7`, `similarity_threshold = 0.5`, and **min cluster total** = **$1,000,000**.  
  *(These are function arguments and can be tuned.)*
- **Title similarity** uses a simple string matcher; it can miss synonyms or flag near-matches—manual review recommended.
- Clustering is **O(n²) per supplier**; for very large datasets, consider blocking (by CPV/category, buyer, or month) or approximate similarity.
- Imputed dates (when award date is missing) can make clusters conservative; always validate in source documents.



## 🧪 CLI Usage (per module)

Most scripts accept `--country XX`; otherwise they default to `DEFAULT_COUNTRY`.


## 🗺️ Roadmap

- Multi-country presets and config templates
- Entity resolution across aliases (buyers & suppliers)
- Richer contract-splitting detection (blocking by category/CPV; approximate text embeddings)
- ML-assisted risk scoring and explainability
- Optional lightweight UI for browsing flags and drill-downs



## 📄 License & Attribution

- Please attribute **Global Procurement Risk Model** and ryan-berkowitz98 when sharing derivatives.


## 📬 Contact

Questions or want a run for another country?  
- Open an issue in this repo or reach out directly.














