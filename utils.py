import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def process_metadata(df):
    df.drop(columns=["Unnamed: 0.1", "Unnamed: 0", "sessionId", "time", "th1", "th1_value", 'th2', 'th2_value', 'th3', 'th3_value', 'wudate', 'lon', 'lat'], inplace=True)
    df["fusion_model_prediction"] = df["fusion_model_prediction"].replace("NO PREDICTION (0.0000)", None)
    df["Call_Presence"] = df["fusion_model_prediction"].notnull().astype(int)

    df["Final prediction"] = None
    
    for idx, row in df.iterrows():
        lines = str(row["fusion_model_prediction"]).split("\n")
        for line in lines:
            subset = line.split(" ")
            try:
                if subset[0] == "nan":
                    row["Final prediction"] = None
                    continue

                tmp_pred = ""
                for string in subset[:-1]:
                    tmp_pred += string + " "

                if df.loc[idx, "Final prediction"] is not None:
                    df.loc[idx, "Final prediction"] += ", " + tmp_pred
                else:
                    df.loc[idx, "Final prediction"] = tmp_pred

            except Exception as error:
                print(f"Error processing row {idx}: {error}")
                print(subset)
    

def get_plot_data(df, selected_species):
    MIT_classes_of_interest = ["Crowd", "Civil defense siren", "Railroad car, train wagon", "Vehicle", "Motorcycle", "Thunderstorm", "Air horn, truck horn", "Engine starting", "Siren", "Medium engine (mid frequency)", "Thunder", "Train", "Car", "Vehicle horn, car horn, honking", "Roaring cats (lions, tigers)", "Roar", "Dog"]
    plot_df = pd.DataFrame(columns = ["hour", "total_count", "species", "call_type", "event"])

    if os.path.exists("plot_data.csv"):
        plot_df = pd.read_csv("plot_data.csv")

    else:    
        for _, row in df.iterrows():
            if row["MIT_AST_label"] in MIT_classes_of_interest:
                current_event = row["MIT_AST_label"]
            else:
                current_event = None

            if row["Final prediction"] is not None:
                species = row["Final prediction"].split(", ")
                found = False
                for sp in species:
                    for native in selected_species:
                        if sp.lower().find(native.lower()) != -1:
                            found = True
                            found_specie = native
                            break

                    if found:
                        plot_df.loc[len(plot_df)] = {"hour": row["datetime"].hour, "total_count": "total count", "species": found_specie, "call_type": None, "event": current_event}
        
        plot_df.to_csv("plot_data.csv", index=False)

    return plot_df


def format_data(species):
        return species.replace("'", "").replace("[", "").replace("]", "").replace('"', "").strip().lower()


def bar_plot(plot_df):
    subset_df = plot_df[plot_df["event"]!=None]
    grouped = subset_df.groupby(["hour", "event"]).size().reset_index(name="total_count")
    fig_bar = px.bar(grouped, x="hour", y="total_count", color="event", title="Distribution of Events Over the Day")
    fig_bar.update_layout(xaxis_title="Hour of the Day", yaxis_title="Event count", legend_title="Events")
    fig_bar.update_xaxes(range=[0, 24], tickvals=list(range(0, 25, 1)))

    return fig_bar


def flowchart_plot(plot_df):

    subset_df = plot_df[plot_df["event"].notnull()]
    subset_df["event"] = subset_df["event"].dropna()

    #color = subset_df.call_type.map({"songs": "lightblue", "calls": "lightgreen"})

    specie_dim = go.parcats.Dimension(values=subset_df["species"], label="Specie")
    event_dim = go.parcats.Dimension(values=subset_df["event"], label="Event")
    call_type_dim = go.parcats.Dimension(values=subset_df["call_type"], label="Call Type")

    fig = go.Figure(data=[go.Parcats(dimensions=[specie_dim, event_dim, call_type_dim], 
                                     line={"color": px.colors.qualitative.Plotly[0]},
                                     hoveron="color",
                                     hoverinfo="all",
                                     labelfont={'size': 18, 'family': 'Inter'},
                                     tickfont={'size': 13, 'family': 'Inter'})
                    ])
    
    fig.update_layout(title="Flowchart of Species, Events, and Call Types", font=dict(family="Inter", size=14))
    
    return fig