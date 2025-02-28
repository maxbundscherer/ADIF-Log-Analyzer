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

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, portrait
import pandas as pd


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
    qsl_sent_improved: bool
    country: str
    rst_rcvd: str
    rst_sent: str
    calc_distance: Optional[float]
    calc_duration: float

    # def __str__(self):
    #     return f"Call: {self.call}, My Call: {self.my_call}, Time On: {self.time_utc_on}, Time Off: {self.time_utc_off}, Mode: {self.mode}, Sub Mode: {self.sub_mode}, My Locator: {self.my_locator}, Locator: {self.locator}, Freq: {self.freq}, QSL Sent: {self.qsl_sent} Country: {self.country}, RST Rcvd: {self.rst_rcvd}, Name: {self.name}, Calc Distance: {self.calc_distance}, Calc Duration: {self.calc_duration} "


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

        rst_rcvd = ""
        if "rst_rcvd" in t_qso:
            rst_rcvd = t_qso["rst_rcvd"]

        rst_sent = ""
        if "rst_sent" in t_qso:
            rst_sent = t_qso["rst_sent"]

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
            qsl_sent_improved=t_qso["qsl_sent"] != "N",
            country=t_qso["country"],
            rst_rcvd=rst_rcvd,
            rst_sent=rst_sent,
            name=t_name,
            calc_distance=calc_distance,
            calc_duration=(datetime.strptime(t_qso["qso_date_off"] + t_qso["time_off"],
                                             "%Y%m%d%H%M%S") - datetime.strptime(t_qso["qso_date"] + t_qso["time_on"],
                                                                                 "%Y%m%d%H%M%S")).total_seconds()
        ))

    ret_qsos.sort(key=lambda x: x.time_utc_off)

    return ret_qsos


if __name__ == "__main__":
    C_WORK_DATA_DIR = "workData/"

    print("########################################")
    print("[ADIF LOG TO PDF]")
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
    num_send_qsl = len([x for x in all_qsos_ent if x.qsl_sent_improved])
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

    txt_out = ""
    # print(f"Total QSO: {num_total_qsos}")
    txt_out += f"Total QSO: {num_total_qsos}\n"
    # print(f"First QSO: {all_qsos_ent[0].time_utc_off}")
    txt_out += f"First QSO: {all_qsos_ent[0].time_utc_off}\n"
    # print(f"Last QSO: {all_qsos_ent[-1].time_utc_off}")
    txt_out += f"Last QSO: {all_qsos_ent[-1].time_utc_off}\n"
    # print(f"Num Calc Dist: {num_calc_distance} ({round(num_calc_distance / num_total_qsos * 100, 2)}%)")
    txt_out += f"Num Calc Dist: {num_calc_distance} ({round(num_calc_distance / num_total_qsos * 100, 2)}%)\n"
    # print(f"Num Paper QSL Sent: {num_send_qsl} ({round(num_send_qsl / num_total_qsos * 100, 2)}%)")
    txt_out += f"Num Paper QSL Sent: {num_send_qsl} ({round(num_send_qsl / num_total_qsos * 100, 2)}%)\n"
    # print(f"Num Locators: {num_diff_locator}")
    txt_out += f"Num Locators: {num_diff_locator}\n"
    # print("My Locator: " + my_locator)
    txt_out += "My Locator: " + my_locator + "\n"
    # print("My Call: " + my_call)
    txt_out += "My Call: " + my_call + "\n"

    print(txt_out)

    del txt_out

    # Collect Data Last n QSOs

    # Enter Operator CALLSIGN
    input_operator = input("Enter Operator Callsign: ")
    # input_operator = "DD7MB"
    input_operator = input_operator.strip()
    input_operator = input_operator.upper()
    c_operator = input_operator

    # Enter last known Station Callsign
    input_station = input("Enter last printed Station Callsign (leave empty for all): ")
    # input_station = "YY4EBD"
    # input_station = ""
    input_station = input_station.strip()
    input_station = input_station.upper()

    # Search QSOs for Operator
    if input_station != "":
        all_qsos_ent_filter = [x for x in all_qsos_ent if x.call == input_station]

        assert len(all_qsos_ent_filter) > 0, f"Error: No QSOs found for {input_station}"

        if len(all_qsos_ent_filter) > 1:
            print(f"Multiple QSOs found for {input_station}. Please select one:")
            for i, qso in enumerate(all_qsos_ent_filter):
                print(f"{i}: {qso.time_utc_off}")
            input_idx = int(input("Enter Index: "))
            all_qsos_ent_filter = [all_qsos_ent_filter[input_idx]]

        print("Last QSO for Operator:", all_qsos_ent_filter[0].time_utc_off, all_qsos_ent_filter[0].call)

        # Get Date from next qso (in all_qsos_ent)
        all_qsos_ent_filter = all_qsos_ent_filter[0]
        all_qsos_ent_filter = [x for x in all_qsos_ent if x.time_utc_off > all_qsos_ent_filter.time_utc_off]

        # Filter Last to qso from this point
        all_qsos_ent = [x for x in all_qsos_ent if x.time_utc_off >= all_qsos_ent_filter[0].time_utc_off]

    # Reverse
    # all_qsos_ent = all_qsos_ent[::-1]

    all_qsos_ent_prep = []

    for qso in all_qsos_ent:
        qso: QsoEntity = qso
        print(
            c_operator,
            qso.call,
            qso.mode,
            qso.time_utc_off,
            qso.sub_mode,
            qso.band,
            qso.name,
            qso.freq,
            qso.rst_sent,
            qso.rst_rcvd,
            qso.qsl_sent_improved
        )

        qso.name = qso.name[:23]
        qso.qsl_sent_improved = "yes" if qso.qsl_sent_improved else "no"
        qso.time_utc_off = qso.time_utc_off.strftime("%d.%m.%Y %H:%M:%S")
        qso.freq = f"{round(qso.freq, 3)}"

        all_qsos_ent_prep.append(qso)

    del all_qsos_ent

    # TO PDF

    # Beispiel-Daten aus deiner Schleife
    data = [
        [
            c_operator,
            qso.call,
            qso.time_utc_off,
            qso.mode,
            qso.sub_mode,
            qso.band,
            qso.freq,
            qso.rst_sent,
            qso.rst_rcvd,
            qso.qsl_sent_improved,
            qso.name,
        ]
        for qso in all_qsos_ent_prep
    ]

    # Spaltenüberschriften hinzufügen
    columns = [
        "Operator",
        "Station",
        "QSO End (UTC)",
        "Mode",
        "Sub Mode",
        "Band",
        "Freq.\nMHz",
        "RST\nSent",
        "RST\nRec.",
        "QSL\nSent",
        "Name"
    ]
    data.insert(0, columns)

    # PDF erstellen
    pdf_file = f"{C_WORK_DATA_DIR}outputPDF/logbook.pdf"
    pdf = SimpleDocTemplate(pdf_file, pagesize=portrait(A4),

                            topMargin=25,
                            bottomMargin=25,

                            # leftMargin=25,
                            # rightMargin=25,
                            )

    # Spaltenbreiten manuell festlegen (in Punkten)
    column_widths = [40, 70, 80, 40, 50, 30, 40, 20, 20, 20, 100]

    table = Table(data, colWidths=column_widths, repeatRows=1)

    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, 0), 7),  # Kopfzeilen-Schriftgröße auf 8pt
        ('FONTSIZE', (0, 1), (-1, -1), 7),  # Inhalt-Schriftgröße auf 7pt
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),  # Weniger Padding in der Kopfzeile
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('WORDWRAP', (0, 0), (-1, -1), True)  # Textumbruch aktivieren
    ])
    table.setStyle(style)

    # PDF speichern
    pdf.build([table])

    print(f"PDF '{pdf_file}' erfolgreich erstellt!")
