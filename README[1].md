# Web Mercantile Lease Optimizer

A Streamlit web application for solving the Web Mercantile warehouse-leasing optimization problem.

## What it does

The app lets the user edit:

- warehouse space required in Months 1–5
- cost per square foot for leases lasting 1–5 months

It then finds the minimum-cost combination of leases that satisfies every month's warehouse-space requirement.

For the textbook data, the optimal total cost is:

**$7,650,000**

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy with GitHub + Streamlit

1. Create a new GitHub repository.
2. Upload:
   - `app.py`
   - `requirements.txt`
   - `README.md`
3. Sign in to Streamlit Community Cloud.
4. Choose **Create app**.
5. Select the GitHub repository and `app.py`.
6. Deploy.

## Model

Decision variables represent the square feet leased for each possible:

- starting month
- lease duration

Objective:

```text
Minimize total lease cost
```

Subject to:

```text
Active leased space in each month >= required space
Lease quantities >= 0
```

The optimization routine is implemented directly in Python, so no external solver such as PuLP or SciPy is required.
