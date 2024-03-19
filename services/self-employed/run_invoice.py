import re
from urllib.parse import urlencode, urlparse, urlunparse

import pandas as pd
import streamlit as st
from streamlit.runtime.legacy_caching import clear_cache

# st.set_page_config(layout="wide")
st.title("Invoice")

st.markdown("## Data Sheet")


@st.cache_data
def get_excel(url: str) -> dict[str, pd.DataFrame]:
    xls = pd.ExcelFile(url)
    return pd.read_excel(xls, sheet_name=xls.sheet_names)


def craft_google_sheet_url(url: str, export_format="xlsx") -> str:
    parsed = urlparse(url)
    if "docs.google.com" not in parsed.netloc or "/spreadsheets" not in parsed.path:
        return url

    path = parsed.path.rstrip("/").replace("/edit", "/export")
    if not path.endswith("/export"):
        path = path + "/export"

    query_params = {"format": export_format}
    new_query = urlencode(query_params)

    new_url = urlunparse(parsed._replace(path=path, query=new_query))
    return new_url


url_data = st.text_input("Data sheet url:")
if url_data is None or url_data == "":
    quit()

if st.button("Reload"):
    clear_cache()


formatted_url_data = craft_google_sheet_url(url_data)

st.markdown(f"```" f"{formatted_url_data}" f"```")
data = get_excel(formatted_url_data)

data["invoices"].set_index("invoice_id", inplace=True)
assert data["invoices"].index.is_unique

for k, v in data.items():
    st.markdown(f"### Sheet: {k}")
    st.write(v)

st.markdown("## Hours Tracking")

uploaded_file = st.file_uploader("Choose file :sunglasses:")
if uploaded_file is not None:
    df_hours_raw = pd.read_csv(uploaded_file)

    st.write(df_hours_raw)

    st.markdown("### Processed Raw Hours")

    def process_columns(df):
        df.columns = (
            df.columns.str.lower()
            .str.replace(r"\((.+)\)", r"\1", regex=True)
            .str.replace(" ", "_")
        )
        return df

    def processing_time(df):
        for x in ("start", "end"):
            df[f"{x}_date"] = pd.to_datetime(
                df[f"{x}_date"] + " " + df.pop(f"{x}_time")
            )

        df["duration_h"] = pd.to_timedelta(df["duration_h"])
        mask = df.duration_h == df.end_date - df.start_date
        assert mask.all()
        df.drop(columns="duration_h", inplace=True)
        return df

    # columns
    df_hours = process_columns(df_hours_raw)

    # time
    df_hours = processing_time(df_hours)

    df_hours = df_hours[["project", "client", "task", "tags", "start_date", "end_date"]]

    st.write(df_hours)

    #
    st.markdown("## Create Invoice")

    box_invoice_id = st.sidebar.selectbox("Create invoice:", data["invoices"].index)
    invoice_row = data["invoices"].loc[box_invoice_id]

    def df_with_selections(df):
        df = df.copy()
        df.insert(0, "select", True)
        edited = st.data_editor(
            df,
            column_config={"select": st.column_config.CheckboxColumn(required=True)},
            num_rows="dynamic",
        )
        edited = edited[edited.pop("select")]
        return edited

    st.markdown("### Edit Data")
    df_hours_edited = df_with_selections(df_hours)

    st.markdown("### Processed Data")

    def process_rows(df: pd.DataFrame):
        def expand_row(row: pd.Series):
            if row.end_date.date() == row.start_date.date():
                return [row]

            row1 = row.copy()
            row1.end_date = row1.start_date.replace(hour=23, minute=59, second=59)
            row2 = row.copy()
            row2.start_date = (row.start_date + pd.Timedelta("1 day")).replace(
                hour=0, minute=0, second=0
            )
            # further split second row if needed
            rows = [row1] + expand_row(row2)
            return rows

        rows = []
        for _, row in df.iterrows():
            rows.extend(expand_row(row))
        return pd.DataFrame(rows).sort_values("start_date", ascending=False)

    st.markdown("#### Split by day")
    df_days = process_rows(df_hours_edited)
    df_days["dt"] = df_days.end_date - df_days.start_date
    st.write(df_days)

    st.markdown("#### Aggregated")
    df_agg = (
        df_days.groupby([df_days.start_date.dt.date, "task"]).dt.sum().reset_index()
    )
    st.write(df_agg)

    st.markdown("### Output Invoice")
    df_agg["hours"] = (df_agg.pop("dt").dt.total_seconds() / 3600).round(3)
    df_agg["task"] = df_agg.task.str.capitalize()
    df_agg["rate"] = invoice_row.HOURLY_RATE
    df_agg["total"] = df_agg.rate * df_agg.hours

    total = df_agg.total.sum()
    total_hours = df_agg.hours.sum()

    df_agg.rename(
        columns={
            "start_date": "Date",
            "task": "Tâche",
            "hours": "Heures",
            "rate": f"Taux ({invoice_row.DEVISE})",
            "total": f"Total ({invoice_row.DEVISE})",
        },
        inplace=True,
    )
    st.write(df_agg)

    df_agg_task = df_agg.drop(columns="Date").groupby("Tâche").sum()
    st.write(df_agg_task)

    def to_latex(df: pd.DataFrame):
        ltx = df.style.format(decimal=".", precision=3, thousands="'").to_latex(
            hrules=True, environment="longtable", siunitx=True
        )
        ltx = re.sub(r"& \{([^}]*)\}", r"& \\textbf{\g<1>}", ltx)
        return ltx

    period = " - ".join(
        d.strftime("%Y/%m/%d")
        for d in (invoice_row.INVOICE_START_DATE, invoice_row.INVOICE_END_DATE)
    )
    mapping = {
        "numeroFacture": box_invoice_id,
        "periodeFacturee": period,
        "tauxHoraire": str(invoice_row.HOURLY_RATE),
        "totalAPayer": str(total),
        "totalHeures": str(total_hours),
        "devise": invoice_row.DEVISE,
        "detailHeuresTravaillees": to_latex(df_agg),
    }

    def to_command(k, v):
        return "\\newcommand{\\" + k + "}{" + v + "}"

    variables = "\n\n".join(to_command(k, v) for k, v in mapping.items())
    st.code(variables, language="latex")
