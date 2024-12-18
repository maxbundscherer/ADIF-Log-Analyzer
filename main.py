from collections import Counter
from datetime import datetime
import os
from dataclasses import dataclass
import matplotlib.pyplot as plt
import adif_io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.LocationUtil import LocationUtil
from typing import Optional


@dataclass
class QsoEntity:
    call: str
    my_call: str
    time_utc_on: datetime
    time_utc_off: datetime
    mode: str
    band: str
    name: str
    sub_mode: Optional[str]
    my_locator: str
    locator: Optional[str]
    freq: float
    qsl_sent: bool
    country: str
    calc_distance: Optional[float]

    def __str__(self):
        return f"Call: {self.call}, My Call: {self.my_call}, Time On: {self.time_utc_on}, Time Off: {self.time_utc_off}, Mode: {self.mode}, Sub Mode: {self.sub_mode}, My Locator: {self.my_locator}, Locator: {self.locator}, Freq: {self.freq}, QSL Sent: {self.qsl_sent}"


def get_all_qsos(input_paths):
    print(f"Found {len(input_paths)} ADIF files: ")

    ret_qsos = []

    for t_fp in input_paths:
        t_qsos, _ = adif_io.read_from_file(C_WORK_DATA_DIR + "input/" + t_fp)
        print(f" - '{t_fp}' with {len(t_qsos)} QSOs")
        for t_qso in t_qsos:
            ret_qsos.append(t_qso)

    return ret_qsos


def get_all_qsos_ent(input_qsos) -> [QsoEntity]:
    ret_qsos: [QsoEntity] = []

    for t_qso in input_qsos:

        # print(t_qso)
        # raise Exception("Stop here")

        calc_distance = None
        if "gridsquare" in t_qso:
            try:
                calc_distance = LocationUtil.calc_distance_azimuth(
                    loc_0=LocationUtil.maidenhead_to_coordinates(t_qso["gridsquare"]),
                    loc_1=LocationUtil.maidenhead_to_coordinates(t_qso["my_gridsquare"])
                )
                calc_distance = calc_distance.distance
                calc_distance = round(calc_distance, 2)
            except Exception as e:
                print(f"Warn by {t_qso['gridsquare']}/{t_qso['call']}: {e}")

        t_name = ""
        if "name" in t_qso:
            t_name = t_qso["name"]

        ret_qsos.append(QsoEntity(
            call=t_qso["call"],
            my_call=t_qso["station_callsign"],
            time_utc_on=datetime.strptime(t_qso["qso_date"] + t_qso["time_on"], "%Y%m%d%H%M%S"),
            time_utc_off=datetime.strptime(t_qso["qso_date_off"] + t_qso["time_off"], "%Y%m%d%H%M%S"),
            mode=t_qso["mode"],
            band=t_qso["band"],
            sub_mode=t_qso["submode"] if "submode" in t_qso else None,
            my_locator=t_qso["my_gridsquare"],
            locator=t_qso["gridsquare"] if "gridsquare" in t_qso else None,
            freq=round(float(t_qso["freq"]), 3),
            qsl_sent=t_qso["qsl_sent"] == "Y",
            country=t_qso["country"],
            name=t_name,
            calc_distance=calc_distance
        ))

    ret_qsos.sort(key=lambda x: x.time_utc_off)

    return ret_qsos


def vis_barh_plot(vis_data, x_label, y_label, title, output_fp):
    vis_data_f = []
    for x in vis_data:
        if x is not None:
            vis_data_f.append(x)
    vis_data = vis_data_f

    counter = Counter(vis_data)
    counter = dict(sorted(counter.items(), key=lambda item: item[1], reverse=True))

    plt.figure()
    plt.barh(counter.keys(), counter.values())
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)
    plt.tight_layout()
    if output_fp is not None:
        plt.savefig(output_fp)
    else:
        plt.show()
    plt.close("all")


def vis_map(items: [QsoEntity], fp="", fp_html="", static_mode=False):
    print("Process Static Mode: ", static_mode)

    worked_items = []
    worked_grid_locators = []

    for item in items:
        if item.locator is not None:
            worked_items.append(item)
            worked_grid_locators.append(item.locator)

    # Convert to coordinates
    worked_grid_locators_cp = []
    items_cp = []
    for locator, item in zip(worked_grid_locators, worked_items):
        try:
            worked_grid_locators_cp.append(LocationUtil.maidenhead_to_coordinates(locator))
            items_cp.append(item)
        except Exception as e:
            print(f"Warn by {locator}/{item.call}: {e}")

    worked_grid_locators = worked_grid_locators_cp
    worked_items = items_cp
    del worked_grid_locators_cp, items_cp

    coordinates = []
    lines = []  #

    for locator, item in zip(worked_grid_locators, worked_items):
        out_time = item.time_utc_off.strftime("%Y-%m-%d %H:%M")

        coordinates.append(
            {
                "HoverLabel": item.call + " (" + item.mode + ") " + str(
                    item.freq) + " MHz " + out_time + " " + item.locator + " (" + str(
                    int(round(item.calc_distance, 0))) + " km)",
                "Latitude": locator.latitude,
                "Longitude": locator.longitude,
                "Band": item.band
            }
        )
        lines.append(
            {"start_lat": my_lat,
             "start_lon": my_lon,
             "end_lat": locator.latitude,
             "end_lon": locator.longitude
             })

    # Daten in ein DataFrame umwandeln
    df = pd.DataFrame(coordinates)

    # Group by Latitute and Longitude
    df = df.groupby(["Latitude", "Longitude"]).agg(
        {"HoverLabel": lambda x: "<br>".join(x), "Band": "last"}).reset_index()

    # Weltkarte mit den Koordinaten erstellen
    fig = px.scatter_mapbox(
        df,
        lat="Latitude",
        lon="Longitude",
        color="Band",
        hover_name="HoverLabel",
        hover_data={"HoverLabel": False,
                    "Latitude": False,
                    "Longitude": False,
                    "Band": False,
                    },

        # title="Amateurfunk Grid-Locators",
        # projection="natural earth"  # Projektion der Karte
    )

    # for line in lines:
    #     fig.add_trace(go.Scattergeo(
    #         lon=[line["start_lon"], line["end_lon"]],
    #         lat=[line["start_lat"], line["end_lat"]],
    #         mode="lines",
    #         line=dict(width=0.5, color="rgba(0, 0, 0, 0.2)"),
    #         # name="Connection"
    #         showlegend=False
    #     ))

    # fig.show()

    if static_mode:

        # PNG CONFIG
        fig.update_layout(
            # mapbox_style="carto-positron",
            mapbox_style="carto-darkmatter",
            # mapbox_style="open-street-map",
            mapbox_zoom=1.5,
            width=1920, height=1080,
            mapbox_center={"lat": 51.1657 - 25.0, "lon": 10.4515},
            margin=dict(l=0, r=0, t=0, b=0),
        )

    else:

        # HTML CONFIG
        fig.update_layout(
            # mapbox_style="carto-positron",
            mapbox_style="carto-darkmatter",
            # mapbox_style="open-street-map",
            mapbox_zoom=1,
            # width=1920, height=1080,
            # mapbox_center={"lat": 51.1657 - 25.0, "lon": 10.4515},
            margin=dict(l=0, r=0, t=0, b=0),
            showlegend=False,
            # dragmode="zoom"
        )

    fig.update_traces(marker=dict(size=9))

    # fig.update_layout(map_style="open-street-map")
    # fig.update_layout()
    # fig.update_traces(marker=dict(size=5))

    if fp_html != "":
        fig.write_html(fp_html,
                       # include_plotlyjs='cdn',
                       config={'scrollZoom': True},
                       full_html=True
                       )

    if fp != "":
        fig.write_image(fp, scale=3)
    # fig.show()

    # import plotly.express as px
    #
    # # Datenquelle: Beispieldaten mit Ländern und Werten
    # data = {
    #     'country': ['Germany', 'France', 'United States', 'China', 'Brazil'],
    #     'value': [80, 70, 300, 1400, 210]
    # }
    #
    # # Daten als DataFrame erstellen
    # import pandas as pd
    #
    # df = pd.DataFrame(data)
    #
    # # Weltkarte mit Plotly Express
    # fig = px.choropleth(
    #     df,
    #     locations="country",  # Spalte mit Ländernamen
    #     locationmode="country names",  # Länder-Modus: Name statt ISO-Codes
    #     color="value",  # Spalte, die farblich dargestellt wird
    #     title="Weltkarte mit Werten"
    # )
    #
    # # Karte anzeigen
    # fig.show()


if __name__ == "__main__":
    C_WORK_DATA_DIR = "workData/"

    print("########################################")
    print("[ADIF LOG ANALYZER]")
    print("########################################")

    # Load and parse ADIF files
    print("\n[LOAD AND PARSE ADIF FILES]\n")

    # Check if work data dir is present
    assert os.path.exists(C_WORK_DATA_DIR), "Error: Work Data Dir not found"
    # Get all ADIF files in input dir
    adif_input_files = [f for f in os.listdir(C_WORK_DATA_DIR + "input/", ) if
                        f.endswith(".adi") or f.endswith(".adif")]
    assert len(adif_input_files) > 0, "Error: No ADIF files found in Input Dir"

    all_qsos = get_all_qsos(adif_input_files)
    del adif_input_files
    assert len(all_qsos) > 0, "Error: No QSOs found in all ADIF files"

    all_qsos_ent: [QsoEntity] = get_all_qsos_ent(all_qsos)
    del all_qsos

    # Output logbook overview
    print("\n[Logbook Overview]\n")

    num_total_qsos = len(all_qsos_ent)
    num_send_qsl = len([x for x in all_qsos_ent if x.qsl_sent])
    num_diff_locator = len(set([x.locator for x in all_qsos_ent if x.locator is not None]))
    num_diff_my_locator = len(set([x.my_locator for x in all_qsos_ent]))
    num_diff_my_call = len(set([x.my_call for x in all_qsos_ent]))
    num_calc_distance = len([x for x in all_qsos_ent if x.calc_distance is not None])

    assert num_diff_my_locator == 1, "Error: Multiple My Locators found"
    my_locator = all_qsos_ent[0].my_locator
    my_lat, my_lon = LocationUtil.maidenhead_to_coordinates(
        my_locator).latitude, LocationUtil.maidenhead_to_coordinates(my_locator).longitude

    assert num_diff_my_call == 1, "Error: Multiple My Calls found"
    my_call = all_qsos_ent[0].my_call

    print(f"Total QSOs:\t\t{num_total_qsos}")
    print(f"First QSO:\t\t{all_qsos_ent[0].time_utc_off}")
    print(f"Last QSO:\t\t{all_qsos_ent[-1].time_utc_off}")
    print(f"Num Calc Dist:\t{num_calc_distance} ({round(num_calc_distance / num_total_qsos * 100, 2)}%)")
    print(f"Num QSL Sent:\t{num_send_qsl} ({round(num_send_qsl / num_total_qsos * 100, 2)}%)")
    print(f"Num Locators:\t{num_diff_locator}")
    print("My Locator:\t\t" + my_locator)
    print("My Call:\t\t" + my_call)

    # Bar-Plot Modes
    print("\n[Bar-Plot Modes]\n")

    vis_barh_plot(
        vis_data=[x.mode for x in all_qsos_ent],
        x_label="Count",
        y_label="Mode",
        title="QSO Mode",
        output_fp=f"{C_WORK_DATA_DIR}/output/qso_modes.png"
    )

    vis_barh_plot(
        vis_data=[x.sub_mode for x in all_qsos_ent],
        x_label="Count",
        y_label="Sub Mode",
        title="QSO Sub Mode",
        output_fp=f"{C_WORK_DATA_DIR}/output/qso_sub_modes.png"
    )

    vis_barh_plot(
        vis_data=[x.band for x in all_qsos_ent],
        x_label="Count",
        y_label="Band",
        title="QSO Band",
        output_fp=f"{C_WORK_DATA_DIR}/output/qso_bands.png"
    )

    # Time-Plot Modes
    print("\n[Time-Plot Modes]\n")

    # Plot QSOS per day
    df = pd.DataFrame([{"Date": x.time_utc_off.date(), "Count": 1} for x in all_qsos_ent])
    fig = px.histogram(df, x="Date", y="Count", title="QSO per Date", nbins=len(set(df["Date"])) * 4)
    fig.update_xaxes(tickangle=90)
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Count")
    # fig.update_traces(marker=dict(line=dict(width=0.5, color='DarkSlateGrey')))
    fig.write_image(f"{C_WORK_DATA_DIR}/output/qso_per_date.png")

    # Plot QSOS per Day of the week
    df = pd.DataFrame([{"Weekday": x.time_utc_off.weekday(), "Count": 1} for x in all_qsos_ent])
    df["Weekday"] = df["Weekday"].map({0: "Mo", 1: "Tu", 2: "We", 3: "Th", 4: "Fr", 5: "Sa", 6: "Su"})
    fig = px.histogram(df, x="Weekday", y="Count", title="QSO per Day of the Week", nbins=7)
    fig.update_xaxes(tickangle=90)
    fig.update_xaxes(title_text="Day of the Week")
    fig.update_yaxes(title_text="Count")
    fig.update_traces(marker=dict(line=dict(width=0.5, color='DarkSlateGrey')))
    fig.write_image(f"{C_WORK_DATA_DIR}/output/qso_per_day_of_week.png")

    # Plot QSOS per Hour of the day
    df = pd.DataFrame([{"Hour": x.time_utc_off.hour, "Count": 1} for x in all_qsos_ent])
    fig = px.histogram(df, x="Hour", y="Count", title="QSO per Hour of the Day", nbins=24)
    fig.update_xaxes(tickangle=90)
    fig.update_xaxes(title_text="Hour of the Day")
    fig.update_yaxes(title_text="Count")
    fig.update_traces(marker=dict(line=dict(width=0.5, color='DarkSlateGrey')))
    fig.write_image(f"{C_WORK_DATA_DIR}/output/qso_per_hour_of_day.png")

    # Hist Mode
    print("\n[Hist Mode]\n")

    # Plot Distance
    df = pd.DataFrame([{"Distance": x.calc_distance} for x in all_qsos_ent if x.calc_distance is not None])
    fig = px.histogram(df, x="Distance", title="QSO Distance", nbins=100)
    fig.update_xaxes(title_text="Distance [km]")
    fig.update_yaxes(title_text="Count")
    fig.update_xaxes(tickangle=90)
    fig.update_traces(marker=dict(line=dict(width=0.5, color='DarkSlateGrey')))
    fig.write_image(f"{C_WORK_DATA_DIR}/output/qso_distance.png")

    # Top n state
    print("\n[Top N Stats]\n")

    all_items = [x.call for x in all_qsos_ent]
    counter = Counter(all_items)
    counter = dict(sorted(counter.items(), key=lambda item: item[1], reverse=True))
    counter = dict(list(counter.items())[:25])
    plt.barh(list(counter.keys()), counter.values())
    plt.xlabel("Count")
    plt.ylabel("Station")
    plt.title("Top 25: Worked Stations")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/stats_top_stations.png")
    plt.close("all")

    all_items = [x.locator for x in all_qsos_ent]
    counter = Counter(all_items)
    counter = dict(sorted(counter.items(), key=lambda item: item[1], reverse=True))
    counter = dict(list(counter.items())[:25])
    plt.barh(list(counter.keys()), counter.values())
    plt.xlabel("Count")
    plt.ylabel("Locator")
    plt.title("Top 25: Worked Locators")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/stats_top_locators.png")
    plt.close("all")

    all_items = [x.country for x in all_qsos_ent]
    counter = Counter(all_items)
    counter = dict(sorted(counter.items(), key=lambda item: item[1], reverse=True))
    counter = dict(list(counter.items())[:25])
    plt.barh(list(counter.keys()), counter.values())
    plt.xlabel("Count")
    plt.ylabel("Country")
    plt.title("Top 25: Worked Countries")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/stats_top_countries.png")
    plt.close("all")

    # Dynamic Filter
    print("\n[Dynamic Filter]\n")


    def df_germany():

        print("# Clubstations Germany \n")

        # Filter
        filtered_items = [x for x in all_qsos_ent if x.country == "Federal Republic Of Germany"]
        filtered_items = [x for x in filtered_items if x.call[2] == "0"]
        filtered_items = [x for x in filtered_items if x.call[1] != "J"]
        # map to call
        filtered_items_call = [x.call for x in filtered_items]
        filtered_items_call = list(set(filtered_items_call))

        for item in filtered_items_call:
            i_call = item
            i_name = [x.name for x in filtered_items if x.call == i_call][0]
            print(f"{i_call}:\t {i_name}")


    df_germany()

    # Map
    print("\n[Map]\n")

    vis_map(all_qsos_ent, fp=f"{C_WORK_DATA_DIR}/output/qso_map.png", static_mode=True)

    vis_map(all_qsos_ent, fp_html=f"{C_WORK_DATA_DIR}/output/qso_map.html", static_mode=False)
