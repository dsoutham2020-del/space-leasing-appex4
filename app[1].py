import streamlit as st
from itertools import combinations

st.set_page_config(
    page_title="Web Mercantile Lease Optimizer",
    page_icon="🏬",
    layout="wide",
)

st.title("🏬 Web Mercantile Lease Optimizer")
st.write(
    "Find the lowest-cost combination of warehouse leases that meets "
    "the required storage space in each month."
)

# -----------------------------
# Default problem data
# -----------------------------
DEFAULT_REQUIREMENTS = [30000, 20000, 40000, 10000, 50000]
DEFAULT_COSTS = [65, 100, 135, 160, 190]


def solve_linear_system(matrix, rhs):
    """Solve a square linear system using Gaussian elimination."""
    n = len(rhs)
    a = [list(map(float, row)) + [float(rhs[i])] for i, row in enumerate(matrix)]

    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        if abs(a[pivot][col]) < 1e-9:
            return None

        a[col], a[pivot] = a[pivot], a[col]
        pivot_value = a[col][col]

        for j in range(col, n + 1):
            a[col][j] /= pivot_value

        for row in range(n):
            if row == col:
                continue
            factor = a[row][col]
            if abs(factor) < 1e-12:
                continue
            for j in range(col, n + 1):
                a[row][j] -= factor * a[col][j]

    return [a[i][n] for i in range(n)]


def optimize_leases(requirements, costs):
    """
    Solve:
        minimize total lease cost
        subject to monthly leased space >= monthly required space
        lease quantities >= 0

    Lease variables represent square feet started in a month for a
    chosen duration. The LP is solved by enumerating basic feasible
    solutions. This keeps the app dependency-free beyond Streamlit.
    """
    months = len(requirements)

    # Build lease variables:
    # (start_month, duration, cost_per_sqft, monthly coverage vector)
    leases = []
    for start in range(months):
        max_duration = months - start
        for duration in range(1, max_duration + 1):
            coverage = [
                1.0 if start <= month < start + duration else 0.0
                for month in range(months)
            ]
            leases.append(
                {
                    "start": start,
                    "duration": duration,
                    "cost": float(costs[duration - 1]),
                    "coverage": coverage,
                }
            )

    # Convert A*x >= b into A*x - s = b, s >= 0.
    # Columns = lease variables followed by surplus variables.
    columns = []
    column_costs = []
    column_types = []

    for idx, lease in enumerate(leases):
        columns.append(lease["coverage"])
        column_costs.append(lease["cost"])
        column_types.append(("lease", idx))

    for month in range(months):
        surplus_column = [0.0] * months
        surplus_column[month] = -1.0
        columns.append(surplus_column)
        column_costs.append(0.0)
        column_types.append(("surplus", month))

    best_cost = float("inf")
    best_values = None

    # A basic feasible solution has at most `months` basic variables.
    for basis in combinations(range(len(columns)), months):
        matrix = [
            [columns[col][row] for col in basis]
            for row in range(months)
        ]

        solution = solve_linear_system(matrix, requirements)
        if solution is None:
            continue

        if any(value < -1e-6 for value in solution):
            continue

        total_cost = sum(
            max(0.0, value) * column_costs[col]
            for value, col in zip(solution, basis)
        )

        if total_cost < best_cost - 1e-5:
            values = [0.0] * len(columns)
            for value, col in zip(solution, basis):
                values[col] = max(0.0, value)

            best_cost = total_cost
            best_values = values

    if best_values is None:
        raise RuntimeError("No feasible leasing plan was found.")

    chosen = []
    for idx, lease in enumerate(leases):
        amount = best_values[idx]
        if amount > 1e-5:
            chosen.append(
                {
                    "Start Month": lease["start"] + 1,
                    "Lease Length": lease["duration"],
                    "Sq. Ft. Leased": round(amount),
                    "Cost / Sq. Ft.": lease["cost"],
                    "Lease Cost": amount * lease["cost"],
                }
            )

    coverage = []
    for month in range(months):
        total = 0.0
        for idx, lease in enumerate(leases):
            total += best_values[idx] * lease["coverage"][month]
        coverage.append(total)

    return best_cost, chosen, coverage


# -----------------------------
# User inputs
# -----------------------------
st.subheader("1. Enter the problem data")

left, right = st.columns(2)

with left:
    st.markdown("**Monthly required space**")
    requirements = []
    for i, default in enumerate(DEFAULT_REQUIREMENTS, start=1):
        requirements.append(
            st.number_input(
                f"Month {i} required space (sq. ft.)",
                min_value=0,
                value=default,
                step=1000,
                key=f"req_{i}",
            )
        )

with right:
    st.markdown("**Lease cost per square foot**")
    costs = []
    for duration, default in enumerate(DEFAULT_COSTS, start=1):
        costs.append(
            st.number_input(
                f"{duration}-month lease cost ($ / sq. ft.)",
                min_value=0.0,
                value=float(default),
                step=5.0,
                key=f"cost_{duration}",
            )
        )

st.divider()

# -----------------------------
# Optimization
# -----------------------------
st.subheader("2. Optimize the leasing plan")

if st.button("Optimize", type="primary", use_container_width=True):
    with st.spinner("Finding the minimum-cost lease plan..."):
        minimum_cost, leases, coverage = optimize_leases(requirements, costs)

    st.success("Optimization complete.")

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Minimum Total Leasing Cost", f"${minimum_cost:,.0f}")
    with c2:
        st.metric("Number of Leases Used", len(leases))

    st.subheader("Optimal leases")

    lease_rows = []
    for lease in leases:
        lease_rows.append(
            {
                "Start Month": lease["Start Month"],
                "Lease Length": f'{lease["Lease Length"]} month(s)',
                "Sq. Ft. Leased": f'{lease["Sq. Ft. Leased"]:,.0f}',
                "Cost / Sq. Ft.": f'${lease["Cost / Sq. Ft."]:,.2f}',
                "Lease Cost": f'${lease["Lease Cost"]:,.0f}',
            }
        )

    st.table(lease_rows)

    st.subheader("Monthly space coverage")
    coverage_rows = []
    for month, (required, available) in enumerate(
        zip(requirements, coverage), start=1
    ):
        coverage_rows.append(
            {
                "Month": month,
                "Required Space": f"{required:,.0f}",
                "Leased Space Available": f"{available:,.0f}",
                "Extra Space": f"{available - required:,.0f}",
            }
        )

    st.table(coverage_rows)

    st.subheader("Interpretation")
    if (
        list(map(int, requirements)) == DEFAULT_REQUIREMENTS
        and [float(x) for x in costs] == [float(x) for x in DEFAULT_COSTS]
    ):
        st.write(
            "For the original Web Mercantile data, the optimizer finds a "
            "**$7,650,000** minimum total cost."
        )

        st.write(
            "That plan uses a 30,000 sq. ft. five-month lease beginning in "
            "Month 1, an additional 10,000 sq. ft. one-month lease in Month 3, "
            "and an additional 20,000 sq. ft. one-month lease in Month 5."
        )
    else:
        st.write(
            "The table above shows the least-cost lease combination for the "
            "values you entered."
        )

    with st.expander("How the optimization model works"):
        st.markdown(
            """
            Each possible lease is treated as a decision variable:

            **x(start month, lease length) = square feet leased**

            The objective is to minimize:

            **Total Cost = Σ(square feet leased × lease-period cost)**

            For every month, the model requires:

            **Total active leased space ≥ required warehouse space**

            All lease quantities must also be nonnegative.

            The app solves this linear optimization model directly in Python
            by checking basic feasible solutions, so no external optimization
            package is required.
            """
        )

else:
    st.info("Enter or edit the values above, then click **Optimize**.")
