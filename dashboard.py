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

import plotly.io as pio
pio.templates.default = "plotly"


# Generating default data values 
plot_df = None
native_species = None

update_aviary_data(["Zoo Eindhoven, Large Aviary"])
plot_df, population_data = get_cached_data()
unique_events = [e for e in plot_df["event"].dropna().unique().tolist() if e is not None]
native_species = [s for s in population_data["species"].unique().tolist() if s is not None]

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
    
    dcc.Dropdown(style=LABEL_STYLE, id='aviary-dropdown', options=[file.replace("_processed.csv","") for file in os.listdir("processed_data") if file.endswith(".csv")], value="Zoo Eindhoven, Large Aviary", multi=True),

    html.Div(style=CARD_SPLIT_STYLE, children=[
        html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_species', style={"height": "200px"})]),
        html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_vocalisations', style={"height": "200px"})]),
        html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_songs', style={"height": "200px"})]),
        html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_calls', style={"height": "200px"})]),
    ]),

    # ── Time slider ───────────────────────────────────────────────────────────
    html.Div(style=CARD_STYLE, children=[
        html.Label('Time of Day (30-min intervals)', style=LABEL_STYLE),
        dcc.RangeSlider(
            id='hour-slider',
            min=0, max=47, step=1,
            value=[0, 47],
            marks={i: f"{i//2}:{'00' if i%2==0 else '30'}" for i in range(0, 48, 4)},
            tooltip={"placement": "bottom", "always_visible": False}
        ),
    ]),

    html.Div(style=CARD_SPLIT_STYLE, children=[
        html.Div(style={"flex": "1"}, children=[
            html.Label('Bird Species', style=LABEL_STYLE),
            dcc.Dropdown(style=LABEL_STYLE, id='species-dropdown', options=native_species, value=native_species, multi=True),
            html.Label('Aviary Population Table', style=LABEL_STYLE),
            dcc.Graph(id='population-table'),

            html.Div(style=CARD_STYLE, children=[
                html.Label('Distribution of Vocalisations per Species', style=LABEL_STYLE),
                dcc.Graph(id='species-pie-chart')
            ]),
        ]),

        html.Div(style={"flex": "1"}, children=[
            html.Div(style=CARD_STYLE, children=[
                html.Label('Vocalisation per 30-min Interval', style=LABEL_STYLE),
                dcc.Graph(id='vocalisation-bar')
            ]),

            html.Div(style=CARD_STYLE, children=[
                html.Label('', style=LABEL_STYLE),
                dcc.Graph(id='Vocalisation-nonnative')
            ]),
        ]),
    ]),

    html.P("Analysis of vocalisation events and types across different species and time periods.", style={"fontSize": "20px", "fontFamily": FONT, "color": COLORS["muted"], "marginBottom": "20px"}),
    html.Div(style=CARD_SPLIT_STYLE, children=[
        html.Div(style={"flex": "2"}, children=[
            html.Div(style=CARD_STYLE, children=[dcc.Graph(id='ind_events', style={"height": "200px"})]),
            html.Div(style=CARD_STYLE, children=[
                html.Label('Events selection menu', style=LABEL_STYLE),
                dcc.Dropdown(style=LABEL_STYLE, id='event-dropdown', options=unique_events, value=unique_events, multi=True),
                html.Label('Event distribution per species', style={**LABEL_STYLE, "marginTop": "48px"}),
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
                dcc.Dropdown(style=LABEL_STYLE, id='species-event-dropdown', options=native_species, value=native_species[0], multi=False),
                dcc.Dropdown(style=LABEL_STYLE, id='single-event-dropdown', options=[ev for ev in plot_df["event"].dropna().unique()], value=plot_df["event"].dropna().unique()[0], multi=False),
            ]),
            html.Div(style={"flex": "2"}, children=[]),
        ]),
        dcc.Graph(id='event-vocalisation-causal-graph'),
    ]),
])


# Indicators and dropdown menus

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
    return selected_aviaries, native_species, native_species, native_species, native_species[0]


@callback(Output('ind_species', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), prevent_initial_call=True)
def indicator_species(selected_species, selected_aviaries):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    fig = go.Figure(data=[go.Indicator(mode="number", value=len(selected_species), title={"text": "Number of Species", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[0], plot_bgcolor=px.colors.qualitative.Pastel[0])
    return fig


@callback(Output('ind_vocalisations', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def indicator_vocalisations(selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset = df[df["species"].isin(selected_species)]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset.shape[0], title={"text": "Total Vocalisations", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[1], plot_bgcolor=px.colors.qualitative.Pastel[1])
    return fig


@callback(Output('ind_calls', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def indicator_calls(selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset = df[df["species"].isin(selected_species) & df["call_type"].notnull()]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset[subset["call_type"]=="calls"].shape[0], title={"text": "Number of Calls", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[2], plot_bgcolor=px.colors.qualitative.Pastel[2])
    return fig


@callback(Output('ind_songs', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def indicator_songs(selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset = df[df["species"].isin(selected_species) & df["call_type"].notnull()]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset[subset["call_type"]=="songs"].shape[0], title={"text": "Number of Songs", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[3], plot_bgcolor=px.colors.qualitative.Pastel[3])
    return fig


@callback(Output('ind_events', 'figure'), Input('event-dropdown', 'value'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def indicator_events(selected_events, selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset = df[df["species"].isin(selected_species) & df["event"].isin(selected_events)]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset["event"].shape[0], title={"text": "Number of Identified Events", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[4], plot_bgcolor=px.colors.qualitative.Pastel[4])
    return fig


# Species general plots

@callback(Output('population-table', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), prevent_initial_call=True)
def create_gender_pop_table(selected_species, selected_aviaries):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    _, population_data = get_cached_data()
    plot_df = population_data[population_data["species"].isin(selected_species)]
    table_fig = go.Figure(data=[go.Table(
        header=dict(values=['Species', 'Males', 'Females', 'Unknown', 'Total']),
        cells=dict(values=[plot_df['species'], plot_df['males'], plot_df['females'], plot_df['unknown'], plot_df['total']]))
    ])
    table_fig.update_layout(title="Population Table")
    return table_fig


@callback(Output('vocalisation-bar', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def species_vocalisation_bar(selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset_df = df[df["species"].isin(selected_species)]
    grouped = subset_df.groupby(["half_hour", "time_label", "species"]).size().reset_index(name="total_count").sort_values("half_hour")
    fig = px.bar(grouped, x="time_label", y="total_count", color="species", title="Distribution of Vocalisations per 30-min Interval")
    fig.update_layout(xaxis_title="Time of Day", yaxis_title="Total Vocalisations", legend_title="Species")
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range))
    return fig


@callback(Output('Vocalisation-nonnative', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def vocalisation_nonnative(selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    native_sp = get_natives_species()
    df['Type'] = df['species'].apply(lambda x: 'Aviary bird' if x in native_sp else 'Wild bird')
    grouped = df.groupby(["half_hour", "time_label", "Type"]).size().reset_index(name="count").sort_values("half_hour")
    fig = px.bar(grouped, x="time_label", y="count", color="Type", barmode='group',
                 title="Comparison of vocalisation between wild and aviary birds",
                 labels={"time_label": "Time of Day", "count": "Vocalisations"})
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range))
    return fig


@callback(Output('species-pie-chart', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def species_pie_chart(selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset_df = df[df["species"].isin(selected_species) & df["species"].notna()]
    counts = subset_df["species"].value_counts().reset_index()
    counts.columns = ["species", "count"]
    fig = px.pie(counts, names="species", values="count", title="Vocalisation Share per Species", hole=0.35)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(legend_title="Species")
    return fig



# Bird vocalisation based on events

@callback(Output('vocalisation-event-bar', 'figure'), Input('event-dropdown', 'value'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def vocalisation_event_bar(selected_events, selected_species, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset_df = df[df["species"].isin(selected_species) & df['event'].isin(selected_events) & df['event'].notna() & df['species'].notna()]
    if subset_df.empty:
        return go.Figure()
    grouped = subset_df.groupby(["species", "event"]).size().reset_index(name="total_count")
    grouped.sort_values(by="total_count", ascending=False, inplace=True)
    fig_bar = px.bar(grouped, x="total_count", y="species", color="event", title="Distribution of Events per Species", orientation="h")
    fig_bar.update_layout(xaxis_title="Total Vocalisations with Event", yaxis_title="Species", legend_title="Events")
    fig_bar.update_xaxes(tickangle=45)
    fig_bar.update_yaxes(categoryorder="total ascending")
    return fig_bar


@callback(Output('bar-plot-graph', 'figure'), Input('event-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('species-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def update_event_bar_plot(selected_events, selected_aviaries, selected_species, hour_range):
    if not selected_species or not selected_aviaries or not selected_events:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset = df[df["species"].isin(selected_species) & df['event'].isin(selected_events) & df['event'].notna()]
    if subset.empty:
        return go.Figure()
    grouped = subset.groupby(["half_hour", "time_label", "event"]).size().reset_index(name="total_count").sort_values("half_hour")
    fig = px.bar(grouped, x="time_label", y="total_count", color="event", title="Distribution of Events per 30-min Interval")
    fig.update_layout(xaxis_title="Time of Day", yaxis_title="Event count", legend_title="Events")
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range))
    return fig


@callback(Output('flowchart-graph', 'figure'), Input('event-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('species-dropdown', 'value'))
def update_event_flowchart(selected_events, selected_aviaries, selected_species):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    subset = df[df["species"].isin(selected_species) & df['event'].isin(selected_events) & df['event'].notna() & df['species'].notna()]
    if subset.empty:
        return go.Figure()
    return flowchart_plot(subset)


@callback(Output('event-vocalisation-causal-graph', 'figure'), Input('species-event-dropdown', 'value'), Input('single-event-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), prevent_initial_call=True)
def event_vocalisation_causal_graph(selected_species, selected_event, selected_aviaries, hour_range):
    if not selected_species or not selected_aviaries or not selected_event:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range)
    subset_df = df[df["species"] == selected_species].copy()
    if subset_df.empty:
        return go.Figure()
    subset_df["selected event presence"] = subset_df["event"].apply(lambda x: "Yes" if x == selected_event else "No")
    grouped = subset_df.groupby(["half_hour", "time_label", "selected event presence"]).size().reset_index(name="total_count").sort_values("half_hour")
    fig = px.bar(grouped, x="time_label", y="total_count", color="selected event presence", barmode="group",
                 title=f"Vocalisation Count of {selected_species} per 30-min Interval with respect to {selected_event} Event")
    fig.update_layout(xaxis_title="Time of Day", yaxis_title="Total Vocalisations", legend_title=f"Presence of event: {selected_event}")
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range))
    return fig


# Run the app
if __name__ == '__main__':
    app.run(debug=True)