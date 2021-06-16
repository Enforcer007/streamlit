from typing import OrderedDict
import streamlit as st
import os
from src.utils import defaults
from src import utils
import pandas as pd
from pathlib import Path
import re

# Write Notes
markdownFile = Path("src/intra_gap/description.md")

REGEX_PATTERN = r"@\[(.+)\][\n\r]([\s\S]+?)(?=\n{2,}@|$)"


def extract_markdown_contents(mFilePath):
    with open(mFilePath) as file:
        data = file.read()
    data = re.findall(REGEX_PATTERN, data)
    markdown_identifiers = {}
    for key, desc in data:
        markdown_identifiers[key] = desc
    return markdown_identifiers


comps = extract_markdown_contents(markdownFile)


data_folder = defaults.DATA_FOLDER


def get_interval_folder(data_folder, interval="1d"):
    return data_folder + "interval=" + interval


one_day_folder = get_interval_folder(data_folder)


stocks_data = list(utils.get_all_files(one_day_folder))
stocks = OrderedDict({i.split("/")[-1].split(".")[0]: i for i in stocks_data})

option = st.sidebar.selectbox("Select any one", list(stocks.keys()))


@st.cache
def load_data(file_path):
    df = pd.read_csv(file_path)
    return df


df_clone = load_data(stocks[option])
df = df_clone.copy()

df["Date"] = pd.to_datetime(df["Date"]).dt.date


df = df.drop_duplicates()


df.columns = [x.lower() for x in df.columns]


df["intra_range"] = (df["close"] / df["open"] - 1) * 100


df["gap_range"] = (df["open"] / df.shift(periods=1)["close"] - 1) * 100

# Plotly gen figure
from plotly import graph_objects as go

# Gap Range
gap_range = st.sidebar.slider(
    "Gap Up / Down range in %", min_value=0.1, max_value=20.0, value=4.0, step=1.0
)

df["markers"] = df["gap_range"].apply(
    lambda x: {"opacity": 1} if abs(x) > gap_range else {"opacity": 0}
)


fig = go.Figure(
    data=go.Scatter(
        x=df["intra_range"],
        y=df["gap_range"],
        mode="markers",
        marker=dict(opacity=df["markers"].apply(lambda x: x["opacity"])),
        customdata=df["date"],
        hovertemplate="<br>".join(
            ["Gap Range: %{y:.2f}%, Intra Range: %{x:.2f}%", "Date: %{customdata}"]
        ),
        name="Intra",
    )
)


x_min, x_max, y_min, y_max = (
    df["intra_range"].min(),
    df["intra_range"].max(),
    df["gap_range"].min(),
    df["gap_range"].max(),
)

red_x0, red_y0, red_x1, red_y1 = 0, y_min, x_max, 0
green_x0, green_y0, green_x1, green_y1 = x_min, 0, 0, y_max


red_points = df[
    (df["intra_range"] >= red_x0)
    & (df["intra_range"] <= red_x1)
    & (df["gap_range"] >= red_y0)
    & (df["gap_range"] <= red_y1)
    & (df["markers"].apply(lambda x: x["opacity"] != 0))
].shape[0]

green_points = df[
    (df["intra_range"] >= green_x0)
    & (df["intra_range"] <= green_x1)
    & (df["gap_range"] >= green_y0)
    & (df["gap_range"] <= green_y1)
    & (df["markers"].apply(lambda x: x["opacity"] != 0))
].shape[0]

total_points = df[df["markers"].apply(lambda x: x["opacity"] != 0)].shape[0]
print(red_points, green_points, total_points, df.shape[0])


fig.add_shape(
    type="rect",
    x0=red_x0,
    y0=red_y0,
    x1=red_x1,
    y1=red_y1,
    # line=dict(color="Royalblue"),
    fillcolor="Red",
    opacity=0.3,
    line_width=0,
)

fig.add_shape(
    type="rect",
    x0=green_x0,
    y0=green_y0,
    x1=green_x1,
    y1=green_y1,
    # line=dict(color="Royalblue"),
    fillcolor="Green",
    opacity=0.3,
    line_width=0,
)


fig.update_layout(
    title="Gap Range vs Day Range",
    xaxis_title="day_range",
    yaxis_title="gap_range",
    legend_title="Legend",
    font=dict(family="Courier New, monospace", size=18, color="RebeccaPurple"),
)

st.markdown(comps["start"])
st.plotly_chart(fig, use_container_width=True)
st.write(comps["after-graph"])
st.markdown(
    comps["trading-probabilities"].format(
        red_points=red_points,
        green_points=green_points,
        total_points=total_points,
        success_rate=round((red_points + green_points) / total_points * 100, 2),
    ),
    unsafe_allow_html=True,
)
st.write(comps["final"])
