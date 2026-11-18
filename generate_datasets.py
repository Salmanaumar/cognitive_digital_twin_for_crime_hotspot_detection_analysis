import numpy as np
import pandas as pd
import random
from datetime import datetime, timedelta

def generate_dataset(city_name, areas, base_lat, base_lon, n_records=1200, filename='data/dataset.csv'):
    np.random.seed(42)
    random.seed(42)
    
    crime_types = [
        'Theft', 'Burglary', 'Robbery', 'Assault', 'Vehicle Theft',
        'Chain Snatching', 'Vandalism', 'Cybercrime', 'Harassment', 'Drug Offense'
    ]
    location_categories = [
        'Commercial', 'Residential', 'Transit Station', 'Street/Road',
        'Nightclub/Bar', 'Bank/ATM', 'Parking Lot', 'Park/Open Ground', 'Market/Bazaar'
    ]
    
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 4, 30)
    date_range_days = (end_date - start_date).days
    
    rows = []
    
    for i in range(n_records):
        area_info = random.choice(areas)
        area_name = area_info['name']
        c_lat, c_lon = area_info['lat'], area_info['lon']
        base_risk = area_info['base_risk']  # 'High', 'Medium', 'Low'
        
        # Add realistic coordinate jitter (roughly 300m - 1.5km)
        lat = round(c_lat + np.random.normal(0, 0.008), 6)
        lon = round(c_lon + np.random.normal(0, 0.008), 6)
        
        rand_days = random.randint(0, date_range_days)
        record_date = start_date + timedelta(days=rand_days)
        date_str = record_date.strftime('%Y-%m-%d')
        month_str = record_date.strftime('%B')
        day_of_week = record_date.strftime('%A')
        
        # Time distribution: peak at night (20:00 - 02:00) for high risk
        if base_risk == 'High':
            if random.random() < 0.65:
                hour = random.choice([20, 21, 22, 23, 0, 1, 2])
            else:
                hour = random.randint(3, 19)
        else:
            hour = random.randint(0, 23)
            
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        time_str = f"{hour:02d}:{minute:02d}:{second:02d}"
        
        crime_type = random.choice(crime_types)
        loc_cat = random.choice(location_categories)
        
        # Historical count and crime frequency with some variance
        if base_risk == 'High':
            hist_count = int(np.random.poisson(55) + random.randint(15, 30))
            crime_freq = round(hist_count / 25.0 + np.random.uniform(0.5, 1.2), 2)
        elif base_risk == 'Medium':
            hist_count = int(np.random.poisson(30) + random.randint(5, 15))
            crime_freq = round(hist_count / 25.0 + np.random.uniform(0.2, 0.6), 2)
        else:
            hist_count = int(np.random.poisson(12) + random.randint(1, 8))
            crime_freq = round(hist_count / 25.0 + np.random.uniform(0.05, 0.3), 2)
            
        is_night = 1 if (hour >= 20 or hour <= 4) else 0
        score = (hist_count * 0.72) + (crime_freq * 10.5) + (10.0 if base_risk == 'High' else (4.0 if base_risk == 'Medium' else 0.0)) + (4.0 if is_night else 0.0)
        if score >= 62:
            risk = 'High'
        elif score >= 32:
            risk = 'Medium'
        else:
            risk = 'Low'
            
        rows.append({
            'date': date_str,
            'time': time_str,
            'day_of_week': day_of_week,
            'month': month_str,
            'city': city_name,
            'area_name': area_name,
            'latitude': lat,
            'longitude': lon,
            'crime_type': crime_type,
            'location_category': loc_cat,
            'crime_frequency': crime_freq,
            'historical_crime_count': hist_count,
            'risk_level': risk
        })
        
    df = pd.DataFrame(rows)
    
    # Introduce explicit realistic missing values (e.g. 18 missing values)
    nan_indices_loc = random.sample(range(len(df)), 12)
    df.loc[nan_indices_loc, 'location_category'] = np.nan
    
    nan_indices_time = random.sample(range(len(df)), 6)
    df.loc[nan_indices_time, 'time'] = np.nan
    
    # Introduce explicit duplicate rows (15 duplicates from complete rows to maintain exact 18 missing count)
    dup_rows = df.dropna().sample(n=15, random_state=42)
    df = pd.concat([df, dup_rows], ignore_index=True)
    
    # Save to CSV
    df.to_csv(filename, index=False)
    print(f"Generated {filename}: {len(df)} total rows, {df.isna().sum().sum()} missing values, {df.duplicated().sum()} duplicate rows.")
    return df

# Hyderabad Areas
hyd_areas = [
    {'name': 'Charminar', 'lat': 17.3616, 'lon': 78.4747, 'base_risk': 'High'},
    {'name': 'Banjara Hills', 'lat': 17.4156, 'lon': 78.4357, 'base_risk': 'Medium'},
    {'name': 'Jubilee Hills', 'lat': 17.4319, 'lon': 78.4073, 'base_risk': 'Medium'},
    {'name': 'Secunderabad', 'lat': 17.4399, 'lon': 78.4983, 'base_risk': 'High'},
    {'name': 'Hitec City', 'lat': 17.4435, 'lon': 78.3772, 'base_risk': 'Medium'},
    {'name': 'Gachibowli', 'lat': 17.4401, 'lon': 78.3489, 'base_risk': 'Low'},
    {'name': 'Begumpet', 'lat': 17.4447, 'lon': 78.4664, 'base_risk': 'High'},
    {'name': 'Madhapur', 'lat': 17.4483, 'lon': 78.3915, 'base_risk': 'Medium'},
    {'name': 'Ameerpet', 'lat': 17.4375, 'lon': 78.4483, 'base_risk': 'High'},
    {'name': 'Kukatpally', 'lat': 17.4947, 'lon': 78.3996, 'base_risk': 'High'},
    {'name': 'Mehdipatnam', 'lat': 17.3916, 'lon': 78.4431, 'base_risk': 'High'},
    {'name': 'Dilsukhnagar', 'lat': 17.3688, 'lon': 78.5247, 'base_risk': 'High'},
    {'name': 'Abids', 'lat': 17.3910, 'lon': 78.4735, 'base_risk': 'Medium'},
    {'name': 'LB Nagar', 'lat': 17.3457, 'lon': 78.5522, 'base_risk': 'Medium'},
    {'name': 'Koti', 'lat': 17.3824, 'lon': 78.4867, 'base_risk': 'High'}
]

# Bengaluru Areas
blr_areas = [
    {'name': 'Koramangala', 'lat': 12.9352, 'lon': 77.6245, 'base_risk': 'High'},
    {'name': 'Indiranagar', 'lat': 12.9784, 'lon': 77.6408, 'base_risk': 'Medium'},
    {'name': 'MG Road', 'lat': 12.9756, 'lon': 77.6066, 'base_risk': 'High'},
    {'name': 'Whitefield', 'lat': 12.9698, 'lon': 77.7500, 'base_risk': 'Medium'},
    {'name': 'HSR Layout', 'lat': 12.9121, 'lon': 77.6446, 'base_risk': 'Low'},
    {'name': 'Electronic City', 'lat': 12.8452, 'lon': 77.6602, 'base_risk': 'Medium'},
    {'name': 'Jayanagar', 'lat': 12.9308, 'lon': 77.5838, 'base_risk': 'Low'},
    {'name': 'Shivajinagar', 'lat': 12.9863, 'lon': 77.6033, 'base_risk': 'High'},
    {'name': 'Hebbal', 'lat': 13.0358, 'lon': 77.5970, 'base_risk': 'Medium'},
    {'name': 'Malleshwaram', 'lat': 13.0031, 'lon': 77.5643, 'base_risk': 'Low'},
    {'name': 'Marathahalli', 'lat': 12.9591, 'lon': 77.6974, 'base_risk': 'High'},
    {'name': 'BTM Layout', 'lat': 12.9166, 'lon': 77.6101, 'base_risk': 'High'},
    {'name': 'Rajajinagar', 'lat': 12.9982, 'lon': 77.5530, 'base_risk': 'Medium'},
    {'name': 'Yelahanka', 'lat': 13.1007, 'lon': 77.5963, 'base_risk': 'Low'}
]

if __name__ == '__main__':
    generate_dataset('Hyderabad', hyd_areas, 17.3850, 78.4867, n_records=1200, filename='data/hyderabad_crime_records.csv')
    generate_dataset('Bengaluru', blr_areas, 12.9716, 77.5946, n_records=1200, filename='data/bengaluru_crime_records.csv')
