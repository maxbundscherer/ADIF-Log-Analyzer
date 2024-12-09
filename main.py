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
    sub_mode: Optional[str]
    my_locator: str
    locator: Optional[str]
    freq: float
    qsl_sent: bool
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
                print(f"Warn by {t_qso['gridsquare']}: {e}")

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


def vis_map(worked_grid_locators, fp):
    # Convert to coordinates
    worked_grid_locators_cp = []
    for locator in worked_grid_locators:
        try:
            worked_grid_locators_cp.append(LocationUtil.maidenhead_to_coordinates(locator))
        except Exception as e:
            print(f"Warn by {locator}: {e}")

    worked_grid_locators = worked_grid_locators_cp

    coordinates = []
    lines = []  # Speicher für Verbindungsdaten
    for locator in worked_grid_locators:
        coordinates.append({"Grid": "Test", "Latitude": locator.latitude, "Longitude": locator.longitude})
        lines.append(
            {"start_lat": my_lat, "start_lon": my_lon, "end_lat": locator.latitude, "end_lon": locator.longitude})

    # Daten in ein DataFrame umwandeln
    df = pd.DataFrame(coordinates)

    # Weltkarte mit den Koordinaten erstellen
    fig = px.scatter_geo(
        df,
        lat="Latitude",
        lon="Longitude",
        # text="Grid",  # Textbeschriftung (Grid-Locator)
        # title="Amateurfunk Grid-Locators",
        # projection="natural earth"  # Projektion der Karte
    )

    for line in lines:
        fig.add_trace(go.Scattergeo(
            lon=[line["start_lon"], line["end_lon"]],
            lat=[line["start_lat"], line["end_lat"]],
            mode="lines",
            line=dict(width=0.5, color="rgba(0, 0, 0, 0.2)"),
            # name="Connection"
            showlegend=False
        ))

    # fig.show()

    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))
    fig.update_traces(marker=dict(size=3))

    fig.write_image(fp, scale=3)

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
        x_label="Mode",
        y_label="Count",
        title="QSO Modes",
        output_fp=f"{C_WORK_DATA_DIR}/output/qsos_modes.png"
    )

    vis_barh_plot(
        vis_data=[x.sub_mode for x in all_qsos_ent],
        x_label="SubMode",
        y_label="Count",
        title="QSO SubModes",
        output_fp=f"{C_WORK_DATA_DIR}/output/qsos_sub_modes.png"
    )

    vis_barh_plot(
        vis_data=[x.band for x in all_qsos_ent],
        x_label="Band",
        y_label="Count",
        title="QSO Bands",
        output_fp=f"{C_WORK_DATA_DIR}/output/qsos_bands.png"
    )

    # Time-Plot Modes
    print("\n[Time-Plot Modes]\n")

    # Plot QSOS per day
    plt.figure()
    plt.hist([x.time_utc_off.date() for x in all_qsos_ent],
             bins=len(set([x.time_utc_off.date() for x in all_qsos_ent])), rwidth=0.8)
    plt.xlabel("Date")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    plt.title("QSOs per Date")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/qsos_per_date.png")
    plt.close("all")

    # Plot QSOS per Day of the week
    plt.figure()
    plt.hist([x.time_utc_off.weekday() for x in all_qsos_ent],
             bins=7, rwidth=0.8)
    plt.xlabel("Day of the Week")
    plt.ylabel("Count")
    # map to monday-sunday
    plt.xticks(range(7), ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"])
    plt.title("QSOs per Day of the Week")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/qsos_per_day_of_week.png")
    plt.close("all")

    # Plot QSOS per Hour of the day
    plt.figure()
    plt.hist([x.time_utc_off.hour for x in all_qsos_ent],
             bins=24, rwidth=0.8)
    plt.xlabel("Hour of the Day")
    plt.ylabel("Count")
    plt.title("QSOs per Hour of the Day")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/qsos_per_hour_of_day.png")
    plt.close("all")

    # Hist Mode
    print("\n[Hist Mode]\n")

    # Plot Distance
    plt.figure()
    plt.hist([x.calc_distance for x in all_qsos_ent if x.calc_distance is not None],
             bins=100, rwidth=0.8)
    plt.xlabel("Distance [km]")
    plt.ylabel("Count")
    plt.title("QSOs Distance")
    plt.tight_layout()
    # plt.show()
    plt.savefig(f"{C_WORK_DATA_DIR}/output/qsos_distance.png")
    plt.close("all")

    # Map
    print("\n[Map]\n")

    vis_map([x.locator for x in all_qsos_ent if x.locator is not None], fp=f"{C_WORK_DATA_DIR}/output/qsos_map.png")
