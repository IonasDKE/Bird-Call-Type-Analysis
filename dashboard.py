import dash
import pandas as pd
import numpy as np
import os, re

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

update_aviary_data(["Zoo Eindhoven, Large Aviary week 2"])
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
}

SECTION_HEADER_STYLE = {
    "fontFamily": FONT,
    "fontSize": "18px",
    "fontWeight": "700",
    "color": COLORS["text"],
    "marginBottom": "4px",
    "marginTop": "8px",
}

SECTION_SUB_STYLE = {
    "fontFamily": FONT,
    "fontSize": "13px",
    "color": COLORS["muted"],
    "marginBottom": "20px",
}

app.layout = html.Div(
    style={"background": COLORS["bg"], "minHeight": "100vh", "padding": "24px 32px", "fontFamily": FONT},
    children=[

        # Header
        html.H1("Bird Vocalisation Analysis Dashboard",
                style={"fontSize": "28px", "color": COLORS["text"], "marginBottom": "6px"}),
        html.P("Explore vocalisation patterns across species, time of day, and acoustic events.",
               style={"fontSize": "15px", "color": COLORS["muted"], "marginBottom": "24px"}),

        # Aviary selector
        html.Div(style=CARD_STYLE, children=[
            html.Label("Aviary", style=LABEL_STYLE),
            dcc.Dropdown(
                id='aviary-dropdown',
                options=[file.replace("_processed.csv", "") for file in os.listdir("processed_data") if file.endswith(".csv")],
                value="Zoo Eindhoven, Large Aviary week 2",
                multi=True,
                style={"fontFamily": FONT},
            ),
        ]),

        # Indicators
        html.Div(style=CARD_SPLIT_STYLE, children=[
            html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_species',      style={"height": "160px"})]),
            html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_vocalisations', style={"height": "160px"})]),
            html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_songs',         style={"height": "160px"})]),
            html.Div(style={"flex": 1}, children=[dcc.Graph(id='ind_calls',         style={"height": "160px"})]),
        ]),

        # Time controls
        html.Div(style=CARD_STYLE, children=[
            html.Div(style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "12px"}, children=[
                html.Label("Time of Day Filter", style=LABEL_STYLE),
                dcc.RadioItems(
                    id='interval-selector',
                    options=[
                        {'label': '15 min', 'value': 15},
                        {'label': '30 min', 'value': 30},
                        {'label': '1 hour', 'value': 60},
                    ],
                    value=30,
                    inline=True,
                    labelStyle={"color": COLORS["text"], "fontFamily": FONT, "fontSize": "13px", "marginRight": "16px"},
                    style={"display": "flex"},
                ),
            ]),
            dcc.RangeSlider(
                id='hour-slider',
                min=0, max=23, step=1,
                value=[0, 23],
                marks={i: {"label": f"{i}:00", "style": {"color": COLORS["text"]}} for i in range(0, 24, 3)},                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ]),

        
        # Species overview
        html.H2("Species Overview", style=SECTION_HEADER_STYLE),
        html.P("Distribution of vocalisations across species and time of day.", style=SECTION_SUB_STYLE),

        # Species filter (full width, above section)
        html.Div(style={**CARD_STYLE, "marginBottom": "12px"}, children=[
            html.Label("Bird Species", style=LABEL_STYLE),
            dcc.Dropdown(
                id='species-dropdown',
                options=native_species,
                value=native_species,
                multi=True,
                style={"fontFamily": FONT},
            ),
        ]),

        html.Div(style=CARD_SPLIT_STYLE, children=[
            html.Div(style={"flex": "1", "minWidth": 0}, children=[
                html.Label("Population", style=LABEL_STYLE),
                dcc.Graph(id='population-table', style={"height": "320px"}),
            ]),
            html.Div(style={"flex": "1", "minWidth": 0}, children=[
                html.Label("Vocalisation Share per Species", style=LABEL_STYLE),
                dcc.Graph(id='species-pie-chart', style={"height": "320px"}),
            ]),
        ]),

        # Heatmap
        html.Div(style=CARD_STYLE, children=[
            html.Label("Vocalisation Heatmap — Species × Time of Day", style=LABEL_STYLE),
            dcc.Graph(id='vocalisation-heatmap', style={"height": "360px"}),
        ]),

        # Row: stacked bar | wild vs aviary
        html.Div(style=CARD_SPLIT_STYLE, children=[
            html.Div(style={"flex": "1", "minWidth": 0}, children=[
                html.Label("Vocalisations over Time by Species", style=LABEL_STYLE),
                dcc.Graph(id='vocalisation-bar', style={"height": "340px"}),
            ]),
        ]),

        
        # Event analysis
        html.H2("Acoustic Event Analysis", style=SECTION_HEADER_STYLE),
        html.P("How identified sound events co-occur with bird vocalisations.", style=SECTION_SUB_STYLE),

        # Event filter + indicator
        html.Div(style=CARD_SPLIT_STYLE, children=[
            html.Div(style={"flex": "2", "minWidth": 0}, children=[
                html.Label("Events", style=LABEL_STYLE),
                dcc.Dropdown(
                    id='event-dropdown',
                    options=unique_events,
                    value=unique_events,
                    multi=True,
                    style={"fontFamily": FONT},
                ),
            ]),
            html.Div(style={"flex": "1", "minWidth": 0}, children=[
                dcc.Graph(id='ind_events', style={"height": "120px"}),
            ]),
        ]),

        # Row: event distribution over time | event per species
        html.Div(style=CARD_SPLIT_STYLE, children=[
            html.Div(style={"flex": "3", "minWidth": 0}, children=[
                html.Label("Event Distribution over Time", style=LABEL_STYLE),
                dcc.Graph(id='bar-plot-graph', style={"height": "340px"}),
            ]),
            html.Div(style={"flex": "2", "minWidth": 0}, children=[
                html.Label("Event Distribution per Species", style=LABEL_STYLE),
                dcc.Graph(id='vocalisation-event-bar', style={"height": "340px"}),
            ]),
        ]),

        # Flowchart
        html.Div(style=CARD_STYLE, children=[
            html.Label("Flowchart — Species → Event → Call Type", style=LABEL_STYLE),
            dcc.Graph(id='flowchart-graph', style={"height": "420px"}),
        ]),

        # Per-species event drill-down
        html.H2("Species × Event Drill-down", style=SECTION_HEADER_STYLE),
        html.P("Select a species and an event to see how vocalisation rate changes with its presence.", style=SECTION_SUB_STYLE),

        html.Div(style=CARD_STYLE, children=[
            html.Div(style={"display": "flex", "gap": "16px", "marginBottom": "16px"}, children=[
                html.Div(style={"flex": "1"}, children=[
                    html.Label("Species", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id='species-event-dropdown',
                        options=native_species,
                        value=native_species[0],
                        multi=False,
                        style={"fontFamily": FONT},
                    ),
                ]),
                html.Div(style={"flex": "1"}, children=[
                    html.Label("Event", style=LABEL_STYLE),
                    dcc.Dropdown(
                        id='single-event-dropdown',
                        options=[ev for ev in plot_df["event"].dropna().unique()],
                        value=plot_df["event"].dropna().unique()[0],
                        multi=False,
                        style={"fontFamily": FONT},
                    ),
                ]),
                html.Div(style={"flex": "2"}),
            ]),
            dcc.Graph(id='event-vocalisation-causal-graph', style={"height": "380px"}),
        ]),
    ]
)


# Slider updates when interval changes
@callback(
    Output('hour-slider', 'max'),
    Output('hour-slider', 'value'),
    Output('hour-slider', 'marks'),
    Input('interval-selector', 'value'))
def update_slider(interval):
    max_val, marks = get_slider_config(interval)
    return max_val, [0, max_val], marks


# Aviary dropdown
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


# Indicators
@callback(Output('ind_species', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), prevent_initial_call=True)
def indicator_species(selected_species, selected_aviaries):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    fig = go.Figure(data=[go.Indicator(mode="number", value=len(selected_species), number={"font": {"size": 40}}, title={"text": "Number of Species", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[0], plot_bgcolor=px.colors.qualitative.Pastel[0])
    return fig


@callback(Output('ind_vocalisations', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def indicator_vocalisations(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset = df[df["species"].isin(selected_species)]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset.shape[0], number={"font": {"size": 40}}, title={"text": "Total Vocalisations", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[1], plot_bgcolor=px.colors.qualitative.Pastel[1])
    return fig


@callback(Output('ind_calls', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def indicator_calls(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset = df[df["species"].isin(selected_species) & df["call_type"].notnull()]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset[subset["call_type"]=="call"].shape[0], number={"font": {"size": 40}}, title={"text": "Number of Calls", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[2], plot_bgcolor=px.colors.qualitative.Pastel[2])
    return fig


@callback(Output('ind_songs', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def indicator_songs(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset = df[df["species"].isin(selected_species) & df["call_type"].notnull()]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset[subset["call_type"]=="song"].shape[0], number={"font": {"size": 40}}, title={"text": "Number of Songs", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[3], plot_bgcolor=px.colors.qualitative.Pastel[3])
    return fig


@callback(Output('ind_events', 'figure'), Input('event-dropdown', 'value'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def indicator_events(selected_events, selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset = df[df["species"].isin(selected_species) & df["event"].isin(selected_events)]
    fig = go.Figure(data=[go.Indicator(mode="number", value=subset["event"].shape[0], number={"font": {"size": 40}}, title={"text": "Number of Identified Events", "font": {"size": 16}})])
    fig.update_layout(paper_bgcolor=px.colors.qualitative.Pastel[4], plot_bgcolor=px.colors.qualitative.Pastel[4])
    return fig


# Species plots

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


@callback(Output('vocalisation-bar', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def species_vocalisation_bar(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset_df = df[df["species"].isin(selected_species)]
    n_days = df["datetime"].dt.date.nunique()
    grouped = subset_df.groupby(["time_slot", "time_label", "species"]).size().reset_index(name="total_count").sort_values("time_slot")
    grouped["total_count"] = grouped["total_count"] / n_days
    interval_label = {15: "15-min", 30: "30-min", 60: "Hour"}[interval]
    fig = px.bar(grouped, x="time_label", y="total_count", color="species", title=f"Distribution of Vocalisations per {interval_label} Interval")
    fig.update_layout(xaxis_title="Time of Day", yaxis_title="Average Vocalisations per Day", legend_title="Species")
    tick_labels = get_xaxis_tick_config(hour_range, interval)
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range, interval),
                     tickmode="array", tickvals=tick_labels, ticktext=tick_labels)
    return fig


@callback(Output('vocalisation-heatmap', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def species_vocalisation_heatmap(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    return heatmap_plot(df, selected_species, hour_range, interval)

"""
@callback(Output('Vocalisation-nonnative', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def vocalisation_nonnative(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    native_sp = get_natives_species()
    df['Type'] = df['species'].apply(lambda x: 'Aviary bird' if x in native_sp else 'Wild bird')
    grouped = df.groupby(["time_slot", "time_label", "Type"]).size().reset_index(name="count").sort_values("time_slot")
    fig = px.bar(grouped, x="time_label", y="count", color="Type", barmode='group',
                 title="Comparison of vocalisation between wild and aviary birds",
                 labels={"time_label": "Time of Day", "count": "Vocalisations"})
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range, interval))
    return fig
"""

@callback(Output('species-pie-chart', 'figure'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def species_pie_chart(selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset_df = df[df["species"].isin(selected_species) & df["species"].notna()]
    n_days = subset_df["datetime"].dt.date.nunique()
    counts = subset_df["species"].value_counts().reset_index()
    counts["count"] = counts["count"]/n_days
    counts.columns = ["species", "count"]
    fig = px.pie(counts, names="species", values="count", title="Vocalisation Share per Species", hole=0.35)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(legend_title="Species")
    return fig


# Event plots

@callback(Output('vocalisation-event-bar', 'figure'), Input('event-dropdown', 'value'), Input('species-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def vocalisation_event_bar(selected_events, selected_species, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset_df = df[df["species"].isin(selected_species) & df['event'].isin(selected_events) & df['event'].notna() & df['species'].notna()]
    if subset_df.empty:
        return go.Figure()
    
    n_days = subset_df["datetime"].dt.date.nunique()
    grouped = subset_df.groupby(["species", "event"]).size().reset_index(name="total_count")
    grouped["total_count"] = grouped["total_count"]/n_days
    grouped.sort_values(by="total_count", ascending=False, inplace=True)
    fig_bar = px.bar(grouped, x="total_count", y="species", color="event", title="Distribution of Events per Species", orientation="h")
    fig_bar.update_layout(xaxis_title="Total Vocalisations with Event", yaxis_title="Species", legend_title="Events")
    fig_bar.update_xaxes(tickangle=45)
    fig_bar.update_yaxes(categoryorder="total ascending")
    return fig_bar


@callback(Output('bar-plot-graph', 'figure'), Input('event-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('species-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def update_event_bar_plot(selected_events, selected_aviaries, selected_species, hour_range, interval):
    if not selected_species or not selected_aviaries or not selected_events:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset = df[df["species"].isin(selected_species) & df['event'].isin(selected_events) & df['event'].notna()]
    if subset.empty:
        return go.Figure()
    n_days = subset["datetime"].dt.date.nunique()
    grouped = subset.groupby(["time_slot", "time_label", "event"]).size().reset_index(name="total_count").sort_values("time_slot")
    grouped["total_count"] = grouped["total_count"]/n_days
    interval_label = {15: "15-min", 30: "30-min", 60: "Hour"}[interval]
    fig = px.bar(grouped, x="time_label", y="total_count", color="event", title=f"Distribution of Events per {interval_label} Interval")
    fig.update_layout(xaxis_title="Time of Day", yaxis_title="Event count", legend_title="Events")
    tick_labels = get_xaxis_tick_config(hour_range, interval)
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range, interval),
                     tickmode="array", tickvals=tick_labels, ticktext=tick_labels)
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


@callback(Output('event-vocalisation-causal-graph', 'figure'), Input('species-event-dropdown', 'value'), Input('single-event-dropdown', 'value'), Input('aviary-dropdown', 'value'), Input('hour-slider', 'value'), Input('interval-selector', 'value'), prevent_initial_call=True)
def event_vocalisation_causal_graph(selected_species, selected_event, selected_aviaries, hour_range, interval):
    if not selected_species or not selected_aviaries or not selected_event:
        return go.Figure()
    df, _ = get_cached_data()
    df = apply_time_filter(df, hour_range, interval)
    subset_df = df[df["species"] == selected_species].copy()
    if subset_df.empty:
        return go.Figure()
    subset_df["selected event presence"] = subset_df["event"].apply(lambda x: "Yes" if x == selected_event else "No")
    n_days = subset_df["datetime"].dt.date.nunique()
    grouped = subset_df.groupby(["time_slot", "time_label", "selected event presence"]).size().reset_index(name="total_count").sort_values("time_slot")
    grouped["total_count"] = grouped["total_count"]/n_days
    interval_label = {15: "15-min", 30: "30-min", 60: "Hour"}[interval]
    fig = px.bar(grouped, x="time_label", y="total_count", color="selected event presence", barmode="group",
                 title=f"Vocalisation Count of {selected_species} per {interval_label} Interval with respect to {selected_event} Event")
    fig.update_layout(xaxis_title="Time of Day", yaxis_title="Total Vocalisations", legend_title=f"Presence of event: {selected_event}")
    tick_labels = get_xaxis_tick_config(hour_range, interval)
    fig.update_xaxes(categoryorder='array', categoryarray=ordered_labels(hour_range, interval),
                     tickmode="array", tickvals=tick_labels, ticktext=tick_labels)
    return fig


if __name__ == '__main__':
    app.run(debug=True)