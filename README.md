# Home Energy Estimator

A lightweight command‑line tool that estimates the electricity consumption of a set of appliances over a user‑defined period.  It reads two CSV files:

* **appliances.csv** – `name,power_watts`
* **schedule.csv** – `name,day,hours`

The tool prints the daily kWh, per‑appliance totals, and the cumulative period total.  An optional ``--confidence`` flag shows ±5 % bounds based on the assumption that each appliance’s power rating may vary by 5 %.

## Installation

No installation is required; the project uses only the Python standard library.  Run it directly with:

```bash
python -m home_energy_estimator --appliances appliances.csv \
    --schedule schedule.csv --period 7
```

## Usage

```text
usage: home_energy_estimator [-h] --appliances APPLIANCES --schedule SCHEDULE \
                            --period PERIOD [--confidence]

Estimate home energy consumption from appliance power ratings and usage schedule.

options:
  -h, --help            show this help message and exit
  --appliances APPLIANCES
                        Path to CSV file with columns name,power_watts
  --schedule SCHEDULE   Path to CSV file with columns name,day,hours
  --period PERIOD       Number of days to compute
  --confidence          Show ±5%% confidence bounds
```

## Example

```csv
# appliances.csv
name,power_watts
fridge,100
lamp,60

# schedule.csv
name,day,hours
fridge,1,24
lamp,1,5
fridge,2,24
lamp,2,5
```

```bash
python -m home_energy_estimator --appliances appliances.csv \
    --schedule schedule.csv --period 2
```

Output:

```
Day 1: 2.70 kWh
Day 2: 2.70 kWh

Per appliance totals:
  fridge: 4.80 kWh
  lamp: 0.60 kWh

Period total: 5.40 kWh
```

## Testing

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

---

This project is released under the MIT license.  No external dependencies or network calls are required.


## Installation

```bash
pip install git+https://github.com/ScobieWorks/home-energy-estimator.git
```


## Command-line usage

```bash
home-energy-estimator --help
```

## Limitations
<!-- generated-limitations:abb0f070ff791826261d5e1e24241d05b1f80fafe3ee35b9802dd54982dcae26 -->
- The CLI parser in `home_energy_estimator.py` requires an explicit `--appliances` argument.
- The CLI parser in `home_energy_estimator.py` requires an explicit `--schedule` argument.
- The CLI parser in `home_energy_estimator.py` requires an explicit `--period` argument.
<!-- /generated-limitations -->
