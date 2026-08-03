import requests
import pandas as pd
from datetime import datetime, timedelta

def get_emsc_data(days_back=13000):
    lat_min, lat_max = 22.0, 32.0
    lon_min, lon_max = 25.0, 36.0

    url = "https://www.seismicportal.eu/fdsnws/event/1/query"

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    all_quakes = []

    current_start = start_date
    chunk_days = 30

    print(f"Fetching data from {start_date.date()} to {end_date.date()} in {chunk_days}-day chunks...")

    while current_start < end_date:
        current_end = min(current_start + timedelta(days=chunk_days), end_date)

        # Format times exactly to FDSN WS-Event spec: YYYY-MM-DDTHH:MM:SS
        start_str = current_start.strftime("%Y-%m-%dT%H:%M:%S")
        end_str = current_end.strftime("%Y-%m-%dT%H:%M:%S")

        print(f"  -> Querying {start_str} to {end_str}")

        params = {
                    "format": "json",
                    "starttime": start_str,
                    "endtime": end_str,
                    "minmagnitude": 3.0,
                    "minlatitude": lat_min,
                    "maxlatitude": lat_max,
                    "minlongitude": lon_min,
                    "maxlongitude": lon_max,
                    "limit": 20000
                }

        response = requests.get(url, params=params)

        if response.status_code == 200:
            try:
                data = response.json()
                features = data.get('features', [])
                print(f"     Found {len(features)} events.")

                for feature in features:
                    props = feature['properties']
                    geom = feature['geometry']['coordinates']

                    all_quakes.append({
                        "time": pd.to_datetime(props['time'], format="mixed", utc=True),
                        "mag": props['mag'],
                        "place": props['flynn_region'],
                        "lon": geom[0],
                        "lat": geom[1],
                        "depth": geom[2]
                    })
            except requests.exceptions.JSONDecodeError:
                print(f"     Error: API returned non-JSON data. Response: {response.text[:100]}")
        else:
            # Added more robust error logging
            print(f"     Status Code {response.status_code}: {response.text[:100]}")

        current_start = current_end

    print(f"\nTotal earthquakes fetched: {len(all_quakes)}")

    if len(all_quakes) > 0:
        df = pd.DataFrame(all_quakes)
        df = df.drop_duplicates(subset=['time', 'lat', 'lon'])

        start_time = df['time'].min()
        df['time_days'] = (df['time'] - start_time).dt.total_seconds() / (24 * 3600)

        df.to_csv("emsc_catalog_1yr.csv", index=False)
        print("Data saved to emsc_catalog_1yr.csv")
        return df
    else:
        return pd.DataFrame()

df = get_emsc_data(13000)
