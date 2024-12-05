from collections import Counter
from datetime import datetime
import os
from dataclasses import dataclass
from typing import Optional
import matplotlib.pyplot as plt

import adif_io


@dataclass
class QsoEntity:
    call: str
    my_call: str
    time_utc_on: datetime
    time_utc_off: datetime
    mode: str
    sub_mode: Optional[str]
    my_locator: str
    locator: Optional[str]
    freq: float
    qsl_sent: bool

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
        ret_qsos.append(QsoEntity(
            call=t_qso["call"],
            my_call=t_qso["station_callsign"],
            time_utc_on=datetime.strptime(t_qso["qso_date"] + t_qso["time_on"], "%Y%m%d%H%M%S"),
            time_utc_off=datetime.strptime(t_qso["qso_date_off"] + t_qso["time_off"], "%Y%m%d%H%M%S"),
            mode=t_qso["mode"],
            sub_mode=t_qso["submode"] if "submode" in t_qso else None,
            my_locator=t_qso["my_gridsquare"],
            locator=t_qso["gridsquare"] if "gridsquare" in t_qso else None,
            freq=round(float(t_qso["freq"]), 3),
            qsl_sent=t_qso["qsl_sent"] == "Y"
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

    print(f"Total QSOs:\t\t{num_total_qsos}")
    print(f"First QSO:\t\t{all_qsos_ent[0].time_utc_off}")
    print(f"Last QSO:\t\t{all_qsos_ent[-1].time_utc_off}")
    print(f"Num QSL Sent:\t{num_send_qsl} ({round(num_send_qsl / num_total_qsos * 100, 2)}%)")
    print(f"Num Locators:\t{num_diff_locator}")

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

    # Time-Plot Modes
    print("\n[Time-Plot Modes]\n")

    # Plot QSOS per day
    plt.figure()
    plt.hist([x.time_utc_off.date() for x in all_qsos_ent],
             bins=len(set([x.time_utc_off.date() for x in all_qsos_ent])), rwidth=0.8)
    plt.xlabel("Date")
    plt.ylabel("Count")
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
