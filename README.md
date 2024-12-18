# ADIF-Log-Analyzer

Author: [DD7MB](https://dd7mb.de)

A python tool for analysing and visualising ADIF (Amateur Data Interchange Format) logbook files.

See example output below.

## Let's get started

### Installation

- Clone this repository and `cd` into it
- Create virtual python env `python -m venv algEnv`
- Activate env `source algEnv/bin/activate`
- Install dependencies `pip install -r requirements.txt`

### Usage

- Add your `*.adif` files to the `workData/input` folder
- Run the script `python main.py` (activate your virtual env before, see installation)
- See output in `workData/output` folder

## Example Output

### Pngs

![](workData/output/qso_map.png)
![](workData/output/qso_modes.png)
![](workData/output/qso_sub_modes.png)
![](workData/output/qso_bands.png)
![](workData/output/qso_distance.png)

![](workData/output/qso_per_date.png)
![](workData/output/qso_count_over_time.png)
![](workData/output/qso_per_month_of_year.png)
![](workData/output/qso_per_day_of_week.png)
![](workData/output/qso_per_hour_of_day.png)

### Stats

![](workData/output/stats_top_stations.png)
![](workData/output/stats_top_locators.png)
![](workData/output/stats_top_countries.png)

### Files

- `workData/output/qso_map.html`

### Stats

```
Total QSOs: 1368
First QSO: 2023-12-18 17:30:00
Last QSO: 2024-12-16 19:15:29
Num QSL Sent: 913 (66.74%)
Num Locators: 920
My Locator: JN59NK
My Call: DF0OHM
```

```
# Clubstations Germany 

DL0EPC Karl
DK0PT University Club Station OTH Regensburg
DF0TV Club Station Erlangen, B08
DL0DM Deutsches Museum
DL0MLU Martin-Luther-University
DK0BMW Clubstation BMW Werk Regensburg
DF0GIF Sigi DJ8VJ
```