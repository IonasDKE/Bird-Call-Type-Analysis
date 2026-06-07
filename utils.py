import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def add_time_cols(df):
    df = df.copy()
    has_minute = 'minute' in df.columns and df['minute'].notna().any()
    if has_minute:
        df['half_hour'] = df['hour'] * 2 + df['minute'].fillna(0).astype(int) // 30
    else:
        df['half_hour'] = df['hour'] * 2

    df['time_label'] = df['half_hour'].apply(lambda x: f"{x//2}:{'00' if x%2==0 else '30'}")
    return df


def apply_time_filter(df, hour_range):
    df = add_time_cols(df)
    return df[(df['half_hour'] >= hour_range[0]) & (df['half_hour'] <= hour_range[1])]

# All 48 half-hour labels in correct order
ALL_TIME_LABELS = [f"{h//2}:{'00' if h%2==0 else '30'}" for h in range(0, 48)]
def ordered_labels(hour_range):
    return [ALL_TIME_LABELS[i] for i in range(hour_range[0], hour_range[1] + 1)]


def update_aviary_data(selected_aviaries_path):
    # Make sure the input is a list
    if isinstance(selected_aviaries_path, str):
        selected_aviaries_path = [selected_aviaries_path]

    general_df = pd.read_csv("general_aviary_data.csv")

    aviary_metadata = pd.DataFrame()
    aviary_population_data = pd.DataFrame(columns=["species", "males", "females", "unknown", "total"])

    for aviary in selected_aviaries_path:
        # Extract individual information from the aviaries_obsolete data
        if aviary not in general_df["Aviary"].values:
            print(f"Aviary {aviary} not found in general data. Skipping.")
        
        else:
            subset = general_df[general_df["Aviary"] == aviary]
            native_species = subset["species"].iloc[0].split(",")
            native_species = [format_data(s.strip()) for s in native_species]

            gender_list = subset["individuals_genders (m.f.u)"].iloc[0].split(",")
            gender_list = [format_data(g).split('.') for g in gender_list]

            males = [g[0] for g in gender_list]
            females = [g[1] for g in gender_list]
            unknowns = [g[2] for g in gender_list]

            population_df = pd.DataFrame({
                "species": native_species,
                "males": males,
                "females": females,
                "unknown": unknowns,
                "total": [int(m) + int(f) + int(u) for m, f, u in zip(males, females, unknowns)]
            })

            aviary_population_data = pd.concat([aviary_population_data, population_df], ignore_index=True)

        # Stack metadata from the different aviaries
        file_path = f"processed_data/{aviary}_processed.csv"
        if os.path.exists(file_path):
            aviary_df = pd.read_csv(file_path)
            aviary_metadata = pd.concat([aviary_metadata, aviary_df], ignore_index=True)
        else:
            print(f"File {file_path} not found.")

    aviary_metadata.to_pickle("cached_plot_df.pkl")
    aviary_population_data.to_pickle("cached_aviary_population_data.pkl")


def get_cached_data():
    plot_df = pd.read_pickle("cached_plot_df.pkl")
    aviary_population_data = pd.read_pickle("cached_aviary_population_data.pkl")
    
    return plot_df, aviary_population_data


def get_natives_species():
    _, population_data = get_cached_data()
    return population_data["species"].unique().tolist()

# Used to reformat the species names
def format_data(species):
        return species.replace("'", "").replace("[", "").replace("]", "").replace('"', "").strip().lower()


def bar_plot(plot_df):
    subset_df = plot_df[plot_df["event"].notnull()]
    grouped = subset_df.groupby(["hour", "event"]).size().reset_index(name="total_count")
    fig_bar = px.bar(grouped, x="hour", y="total_count", color="event", title="Distribution of Events Over the Day")
    fig_bar.update_layout(xaxis_title="Hour of the Day", yaxis_title="Event count", legend_title="Events")
    fig_bar.update_xaxes(range=[-1, 24], tickvals=list(range(0, 24)))

    return fig_bar


def flowchart_plot(plot_df):

    subset_df = plot_df[plot_df["event"].notnull()]
    subset_df["event"] = subset_df["event"].dropna()

    #color = subset_df.call_type.map({"songs": "lightblue", "calls": "lightgreen"})

    specie_dim = go.parcats.Dimension(values=subset_df["species"], label="Specie")
    event_dim = go.parcats.Dimension(values=subset_df["event"], label="Event")
    call_type_dim = go.parcats.Dimension(values=subset_df["call_type"], label="Vocalisation Type")

    fig = go.Figure(data=[go.Parcats(dimensions=[specie_dim, event_dim, call_type_dim], 
                                     line={"color": px.colors.qualitative.Plotly[0]},
                                     hoveron="color",
                                     hoverinfo="all",
                                     labelfont={'size': 18, 'family': "'Inter', sans-serif"},
                                     tickfont={'size': 13, 'family': "'Inter', sans-serif"})
                    ])
    
    fig.update_layout(title="Flowchart of Species, Events, and Call Types")
    
    return fig