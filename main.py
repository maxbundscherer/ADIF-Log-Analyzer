import os
from dataclasses import dataclass

import adif_io


@dataclass
class QsoEntity:
    call: str


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
            call=t_qso["call"]
        ))

    return ret_qsos


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

    print(f"Found {len(all_qsos_ent)} QSOs in total")
