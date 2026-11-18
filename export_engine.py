import os
import json
import pandas as pd
from datetime import datetime
from config import EXPORTS_DIR

def export_predictions_csv(predictions_df, filename=None):
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    if not filename:
        t = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"predictions_export_{t}.csv"
    path = os.path.join(EXPORTS_DIR, filename)
    predictions_df.to_csv(path, index=False)
    return path

def export_predictions_excel(predictions_df, filename=None):
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    if not filename:
        t = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"predictions_export_{t}.xlsx"
    path = os.path.join(EXPORTS_DIR, filename)
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        predictions_df.to_excel(writer, sheet_name='Predictions', index=False)
    return path

def export_predictions_json(predictions_df, metadata, eval_results, filename=None):
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    if not filename:
        t = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"predictions_export_{t}.json"
    path = os.path.join(EXPORTS_DIR, filename)
    
    # Export full consistent payload
    data = {
        'export_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'authoritative_counts': {
            'raw_rows': metadata.get('raw_rows'),
            'missing_values_count': metadata.get('missing_values_count'),
            'duplicate_rows_count': metadata.get('duplicate_rows_count'),
            'invalid_rows_count': metadata.get('invalid_rows_count'),
            'cleaned_rows_count': metadata.get('cleaned_rows_count'),
            'final_processed_rows_count': metadata.get('final_processed_rows_count')
        },
        'city': metadata.get('city'),
        'bounds': metadata.get('bounds'),
        'zones_count': len(metadata.get('zones', [])),
        'model_version': eval_results.get('version'),
        'models_evaluation': eval_results.get('metrics_table'),
        'leakage_assessment': eval_results.get('leakage_assessment'),
        'spatial_statistics': eval_results.get('spatial_statistics'),
        'records_sample': predictions_df.head(200).to_dict(orient='records')
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    return path
