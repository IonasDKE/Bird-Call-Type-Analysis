import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, re
from scipy.stats import chi2_contingency
import queue
from collections import Counter

from dash import Dash, html, dcc, Input, Output, callback
import dash_ag_grid as dag

import plotly.graph_objects as go
import plotly.express as px

from utils import *


AVIARY = "Zoo Eindhoven, Large Aviary"
general_df = pd.read_csv("general_aviary_data.csv")
aviary_df = pd.read_excel("metadata_aviaries/fl_zoo_eindhoven_20250308_meta.xlsx")
process_metadata(aviary_df)

native_species=[format_data(sp.strip()) for sp in general_df[general_df['Aviary'] == AVIARY]['species'].iloc[0].split(",")]

plot_df = get_plot_data(aviary_df, native_species)

# Initialize the app
#app = Dash()

# Edit theme
app = Dash(__name__, external_stylesheets=[
    "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap"
])

COLORS = {
    "bg":       "#0D1117",
    "card":     "#161B22",
    "border":   "#30363D",
    "text":     "#E6EDF3",
    "muted":    "#8B949E",
    "accent":   "#4ECDC4",
}

FONT = "'Inter', sans-serif"

CARD_STYLE = {
    "background": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding": "20px 24px",
    "marginBottom": "20px",
    "gap": "60px",
}

CARD_SPLIT_STYLE = {
    "background": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "12px",
    "padding": "20px 24px",
    "marginBottom": "20px",
    "display": "flex",
    "gap": "20px",
}

LABEL_STYLE = {
    "fontFamily": FONT,
    "fontSize": "13px",
    "fontWeight": "600",
    "letterSpacing": "0.1em",
    "color": COLORS["muted"],
    "marginBottom": "8px",
    "display": "block",
    "textTransform": "uppercase",
    "gap": "8px",
}

app.layout = html.Div(style={
    "background": COLORS["bg"],
    "minHeight": "100vh",
    "fontFamily": FONT,
    "color": COLORS["text"],
    "padding": "32px 40px",
})

# App layout
app.layout = html.Div(style=CARD_STYLE, children=[
    html.Div(style={"display": "flex", "alignItems": "center", "gap": "40px", "marginBottom": "20px"}, children=[
        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_species', style={"height": "200px"}),
        ]),

        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_calls', style={"height": "200px"}),
        ]),

        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_events', style={"height": "200px"}),
        ]),
    ]),

    html.Div(style=CARD_SPLIT_STYLE, children=[
        html.Div(style={"flex": "1"}, children=[
            html.Label('Bird Species', style=LABEL_STYLE),
            dcc.Dropdown(
                style=LABEL_STYLE,
                id='species-dropdown',
                options=[sp for sp in native_species],
                value=[sp for sp in native_species],
                multi=True,
            ),

            html.Label('Aviary Population Table', style=LABEL_STYLE),
            dcc.Graph(id='population-table')
        ]),

        html.Div(style={"flex": "1"}, children=[
            html.Label('Vocalisation per Hour', style=LABEL_STYLE),
            dcc.Graph(id='vocalisation-bar')

        ]),
    ]),

    html.Div(style=CARD_STYLE, children=[
        html.Div(style=CARD_STYLE, children=[
            html.Label('Distribution of Events Over the Day', style=LABEL_STYLE),
            dcc.Graph(figure=bar_plot(plot_df)),
        ]),
        html.Div(style=CARD_STYLE, children=[
            html.Label('Flowchart of Species, Events, and Call Types', style=LABEL_STYLE),
            dcc.Graph(figure=flowchart_plot(plot_df))
        ])
    ])
])

@callback(
    Output('ind_species', 'figure'),
    Input('species-dropdown', 'value'))
def indicator_species(selected_species, plot_df=plot_df):
    fig =  go.Figure(data=[go.Indicator(
        mode = "number",
        value = len(selected_species),
        title = {"text": "Number of Species", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor="lightblue",
        plot_bgcolor="lightblue",
    )

    return fig

@callback(
    Output('ind_calls', 'figure'),
    Input('species-dropdown', 'value'))
def indicator_calls(selected_species, plot_df=plot_df):
    subset = plot_df[plot_df["species"].isin(selected_species)]
    fig = go.Figure(data=[go.Indicator(
        mode = "number",
        value = subset.shape[0],
        title = {"text": "Total Vocalisations", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor="lightgreen",
        plot_bgcolor="lightgreen",
    )
    return fig

@callback(
    Output('ind_events', 'figure'),
    Input('species-dropdown', 'value'))
def indicator_events(selected_species, plot_df=plot_df):
    subset = plot_df[plot_df["species"].isin(selected_species) & plot_df["event"].notnull()]
    fig = go.Figure(data=[go.Indicator(
        mode = "number",
        value = subset["event"].nunique(),
        title = {"text": "Unique Events", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor="lightcoral",
        plot_bgcolor="lightcoral",
    )
    return fig

@callback(
    Output('population-table', 'figure'),
    Input('species-dropdown', 'value'))
def create_gender_pop_table(selected_species, general_df=general_df, AVIARY=AVIARY):
    aviary_info = general_df[general_df["Aviary"] == AVIARY]

    native_species = aviary_info["species"].iloc[0].split(",")
    native_species = [format_data(s.strip()) for s in native_species]

    gender_list = aviary_info["individuals_genders (m.f.u)"].iloc[0].split(",")
    gender_list = [format_data(g).split('.') for g in gender_list]

    males = [g[0] for g in gender_list]
    females = [g[1] for g in gender_list]
    unknowns = [g[2] for g in gender_list]

    plot_df = pd.DataFrame({
		"Species": native_species,
		"Males": males,
		"Females": females,
		"Unknown": unknowns,
        "total": [int(m) + int(f) + int(u) for m, f, u in zip(males, females, unknowns)]
	})

    plot_df = plot_df[plot_df["Species"].isin(selected_species)]

    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Species', 'Males', 'Females', 'Unknown', 'Total'])
        , cells=dict(values=[plot_df['Species'], plot_df['Males'], plot_df['Females'], plot_df['Unknown'], plot_df['total']]))
    ])

    table_fig.update_layout(title="Population Table")
    
    return table_fig

@callback(
    Output('vocalisation-bar', 'figure'),
    Input('species-dropdown', 'value')) 
def vocalisation_bar(selected_species, plot_df=plot_df):
    subset_df = plot_df[plot_df["species"].isin(selected_species)]
    grouped = subset_df.groupby(["hour", "species"]).size().reset_index(name="total_count")
    fig_bar = px.bar(grouped, x="hour", y="total_count", color="species", title="Distribution of vocalisatoions per hour")
    fig_bar.update_layout(xaxis_title="Hour of the Day", yaxis_title="Total Vocalisations", legend_title="Species")
    #fig_bar.update_layout(plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"], font_color=COLORS["text"])
    fig_bar.update_xaxes(range=[0, 24])

    return fig_bar


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
