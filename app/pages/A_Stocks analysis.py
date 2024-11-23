import pandas as pd
from PIL import Image
import streamlit as st

# Layout
twt_logo = Image.open('./app/images/twitter-logo.png')
st.set_page_config(page_title="Stock Analysis", page_icon=twt_logo, layout="wide")
st.title("💸💸 Stock Analysis based on returns on % 💸💸")

# Global Variables
DATE_COLUMN = "DATE"
DATA_PATH = "./data/"


@st.cache_data
def load_data():
    df = pd.read_excel(f"{DATA_PATH}stocks_data.xlsx", sheet_name="Returns", header=[5, 6]).T.iloc[2:, :]
    df = df.rename(columns=df.iloc[0])
    df = df.iloc[2:]
    df.rename(lambda x: str(x).upper(), axis="columns", inplace=True)
    df.reset_index(inplace=True)
    df.rename(columns={"level_0": "DATE1", "level_1": "DATE"}, inplace=True)
    df.drop(columns="DATE1", inplace=True)
    df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN]).dt.date
    return df


# Load data into the dataframe
data = load_data()

st.sidebar.markdown("## Select Data Time and Stock")

stocklist = [
    "BP PLC",
    "FMC CORP",
    "WEYERHAEUSER CO",
    "ALTAGAS LTD",
    "BHP GROUP",
    "INTERNATIONAL PAPER CO",
    "S&P 500 ENERGY INDEX",
    "STORA ENSO",
    "WILMAR INTERNATIONAL LTD",
    "TOTALENERGIES SE",
    "UPM-KYMMENE OYJ",
    "NEWMONT CORP",
    "EXXON MOBIL CORP",
    "VALERO ENERGY CORP",
    "NUCOR CORP",
    "BARRICK GOLD CORP",
    "FREEPORT-MCMORAN INC",
    "CONOCOPHILLIPS",
    "ARCHER-DANIELS-MIDLAND CO",
    "POSCO HOLDINGS INC -SPON ADR",
    "TECK RESOURCES LTD-CLS B",
    "RIO TINTO PLC-SPON ADR",
    "MONDI PLC",
    "ANGLO AMERICAN PLC",
    "CENOVUS ENERGY INC",
    "WESTLAKE CORP",
    "GLENCORE PLC",
    "MOSAIC CO/THE",
    "MARATHON PETROLEUM CORP",
    "PHILLIPS 66",
    "ENERGY TRANSFER LP",
    "VIPER ENERGY PARTNERS LP",
    "SUNOCO LP",
    "WESTROCK CO",
    "PEMBINA PIPELINE CORP",
    "ALCOA CORP",
    "ARCELORMITTAL",
    "NUTRIEN CT LTD",
    "NUTRIEN US LTD",
    "DOW INC",
    "CORTEVA INC",
    "OCCIDENTAL PETROLEUM CORP",
    "ONEOK INC",
    "CHEVRON CORP",
    "PIONEER NATURAL RESOURCES CO",
    "TARGA RESOURCES CORP",
    "SCHLUMBERGER LTD",
    "BAKER HUGHES CO",
    "DEVON ENERGY CORP",
    "HESS CORP",
    "MARATHON OIL CORP",
    "WILLIAMS COS INC",
    "COTERRA ENERGY INC",
    "APA CORP",
    "EOG RESOURCES INC",
    "KINDER MORGAN INC",
    "EQT CORP",
    "HALLIBURTON CO",
    "DIAMONDBACK ENERGY INC",
]

df_columns_list = [
    "BP/ LN Equity",
    "FMC US Equity",
    "WY US Equity",
    "ALA CT Equity",
    "BHP US Equity",
    "IP US Equity",
    "S5ENRS Index",
    "STERV FH Equity",
    "WIL SP Equity",
    "TTE FP Equity",
    "UPM FH Equity",
    "NEM US Equity",
    "XOM US Equity",
    "VLO US Equity",
    "NUE US Equity",
    "ABX CT Equity",
    "FCX US Equity",
    "COP US Equity",
    "ADM US Equity",
    "PKX US Equity",
    "TECK/B CT Equity",
    "RIO US Equity",
    "MNDI LN Equity",
    "AAL LN Equity",
    "CVE CT Equity",
    "WLK US Equity",
    "GLEN LN Equity",
    "MOS US Equity",
    "MPC US Equity",
    "PSX US Equity",
    "ET US Equity",
    "VNOM UW Equity",
    "SUN US Equity",
    "WRK US Equity",
    "PBA US Equity",
    "AA US Equity",
    "MTS SQ Equity",
    "NTR CT Equity",
    "NTR US Equity",
    "DOW US Equity",
    "CTVA US Equity",
    "OXY US Equity",
    "OKE US Equity",
    "CVX US Equity",
    "PXD US Equity",
    "TRGP US Equity",
    "SLB US Equity",
    "BKR US Equity",
    "DVN US Equity",
    "HES US Equity",
    "MRO US Equity",
    "WMB US Equity",
    "CTRA US Equity",
    "APA US Equity",
    "EOG US Equity",
    "KMI US Equity",
    "EQT US Equity",
    "HAL US Equity",
    "FANG US Equity",
]

search_dictio = {}
for i, k in enumerate(df_columns_list):
    search_dictio[stocklist[i]] = k

# -- Choose stocks from stockslists
container = st.sidebar.container()
all = st.sidebar.checkbox("Select all")
if all:
    stocks_selected = container.multiselect("Select one or more options:", stocklist, stocklist)
else:
    stocks_selected =  container.multiselect("Select one or more options:", stocklist)

stocks = []
stocks.append("DATE")
for i in stocks_selected:
    stocks.append(search_dictio.get(i).upper())

# -- Choose the start and end dates
min_date = data[DATE_COLUMN].min()
max_date = data[DATE_COLUMN].max()
start_date = st.sidebar.date_input(
    "Start date:", min_value=min_date, max_value=max_date, value=min_date
)
end_date = st.sidebar.date_input(
    "End date:", min_value=min_date, max_value=max_date, value=max_date
)
st.write("Selected range:", start_date, "to", end_date)

# -- Show data
# ----- Conditions
condition1 = start_date <= data[DATE_COLUMN]
condition2 = data[DATE_COLUMN] <= end_date
mask = condition1 & condition2
filtered_df = data.loc[mask, :]
stocks_df = filtered_df[stocks]
stocks_df[stocks_df.columns[1:]] = stocks_df[stocks_df.columns[1:]].astype(float)

# # ----- Reporting
if len(stocks) > 1:
    m1, m2, m3, m4, m5 = st.columns((1, 1, 1, 1, 1))

    total_returns = stocks_df.drop(columns=DATE_COLUMN).sum(axis=1)

    m1.write("")
    m2.metric(label="Number of selected stocks:", value=str(len(stocks) - 1))
    m3.metric(label="Total Returns for Portfolio", value=str(round(sum(total_returns), 1))+"%")
    m1.write("")

    # ---- Plot
    if st.checkbox("Show returns on % by month"):
        st.dataframe(stocks_df)

    if st.checkbox("Show summary"):
        summary_stats = stocks_df.describe().T
        skewness = stocks_df.skew()
        kurtosis = stocks_df.kurt()
        summary_stats['skewness'] = skewness
        summary_stats['kurtosis'] = kurtosis
        st.dataframe(summary_stats)

    st.title("Cumulate returns")
    st.line_chart(
        data=filtered_df, x="DATE", y=stocks, width=0, height=0, use_container_width=True
    )

    # def correlations(df):
    #     # Increase the size of the heatmap.
    #     plt.figure(figsize=(16, 6))
    #     # Store heatmap object in a variable to easily access it when you want to include more features (such as title).
    #     # Set the range of values to be displayed on the colormap from -1 to 1, and set the annotation to True to display the correlation values on the heatmap.
    #     heatmap = sns.heatmap(df.corr(), vmin=-1, vmax=1, annot=True)
    #     # Give a title to the heatmap. Pad defines the distance of the title from the top of the heatmap.
    #     heatmap.set_title('Correlation Heatmap', fontdict={'fontsize':12}, pad=12)
    #     st.pyplot(heatmap)

    # correlations(filtered_df)

    # st.write(sns.heatmap(filtered_df.corr(),annot=True))
    # st.pyplot()

else:
    st.warning("Please select at least one stock to see the metrics.")
# -- Aknowledgments
c1, c2 = st.columns(2)
with c1:
    st.info(
        "**Data Scientists Linkedin: [@JAGS](https://www.linkedin.com/in/jagarciasanchez) [@Sarra](https://www.linkedin.com/in/sarrabenyahia/)**",
        icon="💡",
    )
with c2:
    st.info(
        "**GitHub: [@JAGS](https://github.com/JoseAngelGarciaSanchez) [@Sarra](https://github.com/sarrabenyahia)**",
        icon="💻",
    )
