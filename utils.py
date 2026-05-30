import pandas as pd
import plotly.express as px


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
    MIT_classes_of_interest = ["Crowd", "Civil defense siren", "Railroad car, train wagon", "Vehicle", "Motorcycle", "Thunderstorm", "Air horn, truck horn", "Grunt", "Engine starting", "Siren", "Medium engine (mid frequency)", "Thunder", "Train", "Car", "Vehicle horn, car horn, honking", "Roaring cats (lions, tigers)", "Roar", "Dog"]
    plot_df = pd.DataFrame(columns = ["hour", "total_count", "species", "call_type", "previous_event"])

    previous_event = None
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
                    plot_df.loc[len(plot_df)] = {"hour": row["datetime"].hour, "total_count": "total count", "species": found_specie, "call_type": None, "previous_event": previous_event}
        previous_event = current_event

    return plot_df


def format_data(species):
        return species.replace("'", "").replace("[", "").replace("]", "").replace('"', "").strip().lower()


def bar_plot(plot_df):
    grouped = plot_df.groupby(["hour", "previous_event"]).size().reset_index(name="total_count")
    fig_bar = px.bar(grouped, x="hour", y="total_count", color="previous_event", title="Distribution of Events Over the Day")
    
    return fig_bar