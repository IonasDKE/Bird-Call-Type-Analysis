import dash
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


'''AVIARY = "Zoo Eindhoven, Large Aviary"
general_df = pd.read_csv("general_aviary_data.csv")
aviary_df = pd.read_excel("metadata_aviaries/fl_zoo_eindhoven_20250308_meta.xlsx")
process_metadata(aviary_df)

native_species=[format_data(sp.strip()) for sp in general_df[general_df['Aviary'] == AVIARY]['species'].iloc[0].split(",")]

plot_df = get_plot_data(aviary_df, native_species)
'''

plot_df = None
native_species = None

update_aviary_data(["Zoo Eindhoven, Large Aviary"])
plot_df, population_data = get_cached_data()
native_species = population_data["species"].unique().tolist()


app = Dash()

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

# App layout
app.layout = html.Div(style=CARD_STYLE, children=[
    html.H1("Bird Vocalisation Analysis Dashboard", style={"fontSize": "28px", "fontFamily": FONT, "color": COLORS["text"], "marginBottom": "12px"}),
    html.P("Explore the vocalisation patterns of different bird species in the aviary. Use the dropdown to filter by species and see how vocalisation types and events are distributed throughout the day.", style={"fontSize": "20px", "fontFamily": FONT, "color": COLORS["muted"], "marginBottom": "20px"}),
    
    dcc.Dropdown(style=LABEL_STYLE, id='aviary-dropdown', options=[file.split('_')[0] for file in os.listdir("processed_data") if file.endswith(".csv")], value="Zoo Eindhoven, Large Aviary", multi=True),
    
    html.Div(style=CARD_SPLIT_STYLE, children=[

        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_species', style={"height": "200px"}),
        ]),

        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_vocalisations', style={"height": "200px"}),
        ]),

        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_songs', style={"height": "200px"}),
        ]),

        html.Div(style={"flex": 1}, children=[
            dcc.Graph(id='ind_calls', style={"height": "200px"}),
        ]),

    ]),

    html.Div(style=CARD_SPLIT_STYLE, children=[
        html.Div(style={"flex": "1"}, children=[
            html.Label('Bird Species', style=LABEL_STYLE),
            dcc.Dropdown(
                style=LABEL_STYLE,
                id='species-dropdown',
                options=[],
                value=[],
                multi=True,
            ),

            html.Label('Aviary Population Table', style=LABEL_STYLE),
            dcc.Graph(id='population-table')
        ]),

        html.Div(style={"flex": "1"}, children=[
            html.Div(style=CARD_STYLE, children=[
                html.Label('Vocalisation per Hour', style=LABEL_STYLE),
                dcc.Graph(id='vocalisation-bar')
            ]),
            html.Div(style=CARD_STYLE, children=[
                html.Label('Heat map between native and non-native species to the aviary', style=LABEL_STYLE),
                dcc.Graph(id='Vocalisation-nonnative')
            ]),

        ]),
    ]),

    html.P("Analysis of vocalisation events and types across different species and time periods.", style={"fontSize": "20px", "fontFamily": FONT, "color": COLORS["muted"], "marginBottom": "20px"}),
    html.Div(style=CARD_SPLIT_STYLE, children=[

        html.Div(style={"flex": "2"}, children=[
            dcc.Graph(id='ind_events', style={"height": "200px"}),

            html.Div(style=CARD_STYLE, children=[
                html.Label('Event distribution per species', style=LABEL_STYLE),
                dcc.Graph(id='vocalisation-event-bar')
            ]),
        ]),

        html.Div(style={"flex": "3"}, children=[
            html.Div(style=CARD_STYLE, children=[
                html.Label('Distribution of Events Over the Day', style=LABEL_STYLE),
                dcc.Graph(id='bar-plot-graph'),
            ]),
            html.Div(style=CARD_STYLE, children=[
                html.Label('Flowchart of Species, Events, and Call Types', style=LABEL_STYLE),
                dcc.Graph(id='flowchart-graph')
            ])
        ]),
    ]),

    html.Div(style=CARD_STYLE, children=[
        html.Div(style=CARD_SPLIT_STYLE, children=[
            html.Div(style={"flex": "1"}, children=[
                dcc.Dropdown(
                    style=LABEL_STYLE,
                    id='species-event-dropdown',
                    options=[],
                    value=[],
                    multi=False,
                ),
                dcc.Dropdown(
                    style=LABEL_STYLE,
                    id='event-dropdown',
                    options=[ev for ev in plot_df["event"].dropna().unique()],
                    value=plot_df["event"].dropna().unique()[0],
                    multi=False,
                ),
            ]), 
            html.Div(style={"flex": "2"}, children=[

            ]),               
        ]),

        dcc.Graph(id='event-vocalisation-causal-graph'),
    ]),
])

@callback(
    Output('aviary-dropdown', 'value'),
    Output('species-dropdown', 'options'),
    Output('species-dropdown', 'value'),
    Output('species-event-dropdown', 'options'),
    Output('species-event-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def update_aviary_dropdown(selected_aviaries):
    if not selected_aviaries:
        return dash.no_update
    
    update_aviary_data(selected_aviaries)

    df, _ = get_cached_data()
    
    global plot_df
    plot_df = df

    global native_species
    native_species = get_natives_species()

    # Outputs are linked to the call back outputs, reason why why output the same thing mutltiple times
    return selected_aviaries, native_species, native_species, native_species, native_species[0]


@callback(
    Output('ind_species', 'figure'),
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def indicator_species(selected_species, selected_aviaries):
    fig =  go.Figure(data=[go.Indicator(
        mode = "number",
        value = len(selected_species),
        title = {"text": "Number of Species", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor=px.colors.qualitative.Pastel[0],
        plot_bgcolor=px.colors.qualitative.Pastel[0],
    )

    return fig


@callback(
    Output('ind_vocalisations', 'figure'),
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def indicator_vocalisations(selected_species, selected_aviaries):
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species)]

    fig = go.Figure(data=[go.Indicator(
        mode = "number",
        value = subset.shape[0],
        title = {"text": "Total Vocalisations", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor=px.colors.qualitative.Pastel[1],
        plot_bgcolor=px.colors.qualitative.Pastel[1],
    )
    return fig


@callback(
    Output('ind_calls', 'figure'),  
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def indicator_calls(selected_species, selected_aviaries):
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species) & df["call_type"].notnull()]

    fig = go.Figure(data=[go.Indicator(
        mode = "number",
        value = subset[subset["call_type"]=="calls"].shape[0],
        title = {"text": "Number of Calls", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor=px.colors.qualitative.Pastel[2],
        plot_bgcolor=px.colors.qualitative.Pastel[2],
    )
    return fig


@callback(
    Output('ind_songs', 'figure'),  
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def indicator_songs(selected_species, selected_aviaries):
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species) & df["call_type"].notnull()]

    fig = go.Figure(data=[go.Indicator(
        mode = "number",
        value = subset[subset["call_type"]=="songs"].shape[0],
        title = {"text": "Number of Songs", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor=px.colors.qualitative.Pastel[3],
        plot_bgcolor=px.colors.qualitative.Pastel[3],
    )
    return fig


@callback(
    Output('ind_events', 'figure'),
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def indicator_events(selected_species, selected_aviaries):
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species) & df["event"].notnull()]

    fig = go.Figure(data=[go.Indicator(
        mode = "number",
        value = subset["event"].shape[0],
        title = {"text": "Number of Identified Events", "font": {"size": 16}}
    )])
    fig.update_layout(
        paper_bgcolor=px.colors.qualitative.Pastel[4],
        plot_bgcolor=px.colors.qualitative.Pastel[4],
    )
    return fig


@callback(
    Output('Vocalisation-nonnative', 'figure'),
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def vocalisation_nonnative(selected_species, selected_aviaries):
    df, _ = get_cached_data()

    fig = px.bar(df, x="species", color=df["species"].apply(lambda x: "Native" if x in selected_species else "Non-Native"), title="Vocalisation Count by Native vs Non-Native Species")
    fig.update_layout(xaxis_title="Species", yaxis_title="Total Vocalisations", legend_title="Species Type")
    fig.update_xaxes(tickangle=45)

    return fig


@callback(
    Output('vocalisation-event-bar', 'figure'),
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def vocalisation_event_bar(selected_species, selected_aviaries):
    df, _ = get_cached_data()
    subset_df = df[df["species"].isin(selected_species) & df["event"].notnull()]

    grouped = subset_df.groupby(["species", "event"]).size().reset_index(name="total_count")
    grouped.sort_values(by="total_count", ascending=False, inplace=True)

    fig_bar = px.bar(grouped, x="total_count", y="species", color="event", title="Distribution of Events per Species", orientation="h")
    fig_bar.update_layout(xaxis_title="Total Vocalisations with Event", yaxis_title="Species", legend_title="Events")
    fig_bar.update_xaxes(tickangle=45)
    fig_bar.update_yaxes(categoryorder="total ascending")

    return fig_bar


@callback(
    Output('population-table', 'figure'),
    Input('species-dropdown', 'value'), 
    Input('aviary-dropdown', 'value'))
def create_gender_pop_table(selected_species, selected_aviaries):
    _, population_data = get_cached_data()

    plot_df = population_data[population_data["species"].isin(selected_species)]

    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Species', 'Males', 'Females', 'Unknown', 'Total'])
        , cells=dict(values=[plot_df['species'], plot_df['males'], plot_df['females'], plot_df['unknown'], plot_df['total']]))
    ])

    table_fig.update_layout(title="Population Table")
    
    return table_fig


@callback(
    Output('vocalisation-bar', 'figure'),
    Input('species-dropdown', 'value'),
    Input('aviary-dropdown', 'value'))
def vocalisation_bar(selected_species, selected_aviaries):
    df, _ = get_cached_data()
    subset_df = df[df["species"].isin(selected_species)]

    grouped = subset_df.groupby(["hour", "species"]).size().reset_index(name="total_count")
    fig_bar = px.bar(grouped, x="hour", y="total_count", color="species", title="Distribution of vocalisatoions per hour")
    fig_bar.update_layout(xaxis_title="Hour of the Day", yaxis_title="Total Vocalisations", legend_title="Species")
    #fig_bar.update_layout(plot_bgcolor=COLORS["card"], paper_bgcolor=COLORS["card"], font_color=COLORS["text"])
    fig_bar.update_xaxes(range=[-1, 24])

    return fig_bar


@callback(
    Output('bar-plot-graph', 'figure'),
    Input('aviary-dropdown', 'value'),
    Input('species-dropdown', 'value'))
def update_bar_plot(selected_aviaries, selected_species):
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species)]
    return bar_plot(subset)


@callback(
    Output('flowchart-graph', 'figure'),
    Input('aviary-dropdown', 'value'),
    Input('species-dropdown', 'value'))
def update_flowchart(selected_aviaries, selected_species):
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species)]
    return flowchart_plot(subset)


@callback(
    Output('event-vocalisation-causal-graph', 'figure'),
    Input('species-event-dropdown', 'value'),
    Input('event-dropdown', 'value'), 
    Input('aviary-dropdown', 'value'))
def event_vocalisation_causal_graph(selected_species, selected_event, selected_aviaries):
    df, _ = get_cached_data()
    subset_df = df[df["species"]==selected_species]
    if subset_df.empty:
        return go.Figure()

    subset_df["selected event presence"] = subset_df["event"].apply(lambda x: "Yes" if x == selected_event else "No")
    grouped = subset_df.groupby(["hour", "selected event presence"]).size().reset_index(name="total_count")

    fig = px.bar(grouped, x="hour", y="total_count", color="selected event presence", barmode="group",
                 title=f"Vocalisation Count of {selected_species} per Hour with respect to {selected_event} Event")
    fig.update_layout(xaxis_title="Hour of the Day", yaxis_title="Total Vocalisations", legend_title=f"{selected_event} Event Presence")
    fig.update_xaxes(range=[-1, 24])
    return fig


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
