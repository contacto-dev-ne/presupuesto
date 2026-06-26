import pandas as pd
import json

def process_excel():
    excel_path = 'ejecucion_total.xlsx'
    json_path = 'datos_ejecucion.json'
    
    print(f"Reading {excel_path}...")
    # Load excel file
    df = pd.read_excel(excel_path)
    
    # Clean the column names (remove leading/trailing spaces)
    df.columns = [str(col).strip() for col in df.columns]
    
    # Fill NA
    df = df.fillna('')
    
    # Convert dates to string
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
            
    # Convert to list of dicts
    records = df.to_dict(orient='records')
    
    # Write to JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False)
        
    print(f"Successfully exported {len(records)} rows to {json_path}")

if __name__ == '__main__':
    process_excel()
