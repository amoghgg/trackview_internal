import pandas as pd
import json
from datetime import datetime

class LockviewConverter:
    """Convert CSV/Excel data to JSON for dashboard visualization"""
    
    def __init__(self):
        # Define the 7-8 key remarks for lock status
        # LOCKED indicators (2)
        self.lock_indicators = [
            "Close Shackle Auto Seal",
            "Shackle Closed",
            "Shakle Closed" # Added to handle common misspelling
        ]
        
        # UNLOCKED indicators (5)
        self.unlock_indicators = [
            "Shackle Opened",
            "Shackle Opned",  # Typo in data
            "Shakle Opened",  # Added to handle common misspelling
            "Shakle Opned",   # Added to handle misspelling combination
            "Dynamic password unseal",
            "Platform unseal",
            "SMS unseal",
            "Swipe card to unseal"
        ]
    
    def determine_status(self, message):
        """Determine lock status from message"""
        if pd.isna(message):
            return "Unknown"
        
        message = str(message).strip()
        
        # Check for lock indicators
        for indicator in self.lock_indicators:
            if indicator.lower() in message.lower():
                return "Locked"
        
        # Check for unlock indicators
        for indicator in self.unlock_indicators:
            if indicator.lower() in message.lower():
                return "Unlocked"
        
        return "Unknown"
    
    def parse_csv(self, filepath):
        """Parse the CSV file and extract relevant data"""
        # Read CSV, skipping the header rows - try different encodings
        try:
            df = pd.read_csv(filepath, skiprows=3, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, skiprows=3, encoding='latin-1')
            except:
                df = pd.read_csv(filepath, skiprows=3, encoding='cp1252')
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Filter out empty rows
        df = df.dropna(subset=['Vehicle No.'])
        
        return df
    
    def process_data(self, df):
        """Process dataframe and extract all log entries for each vehicle"""
        vehicles = {}
        
        for _, row in df.iterrows():
            vehicle_id = row['Vehicle No.']
            # Handle Excel serial date format for 'Alert Generated Time'
            # Excel's date origin is '1899-12-30' for Windows systems
            try:
                date_time = pd.to_datetime(row['Alert Generated Time'], unit='D', origin='1899-12-30', errors='coerce')
            except ValueError:
                # Fallback for other potential formats if needed, though this should cover Excel serial
                date_time = pd.to_datetime(row['Alert Generated Time'], errors='coerce')

            # Handle NaN for location, message, center_id
            location = row['Address'] if pd.notna(row['Address']) else ''
            message = row['Message'] if pd.notna(row['Message']) else ''
            center_id = row.get('Center ID')
            center_id = str(center_id) if pd.notna(center_id) else 'N/A'
            
            status = self.determine_status(message)
            
            if pd.isna(date_time):
                continue

            # NEW: Skip log entries where status is "Unknown"
            if status == "Unknown":
                continue
            
            # Initialize vehicle if not exists
            if vehicle_id not in vehicles:
                vehicles[vehicle_id] = {
                    'vehicle_id': vehicle_id,
                    'center_id': center_id, # Use processed center_id
                    'logs': [],
                    # These will be dynamically calculated by the server, so just initialize
                    'status_15_20': 'No Data', 
                    'status_21': 'No Data',
                    'last_location': '', # Will be set by server if logs exist
                    'last_updated': None
                }
            
            # Add log entry
            log_entry = {
                'timestamp': date_time.strftime('%Y-%m-%d %H:%M'),
                'location': location,
                'message': message,
                'status': status,
                'center_id': center_id,
                'day': date_time.day # Keep for potential future use or consistency
            }
            vehicles[vehicle_id]['logs'].append(log_entry)
        
        # After processing all logs, set last_location and last_updated from the most recent log
        for vehicle_id, vehicle_data in vehicles.items():
            vehicle_data['logs'].sort(key=lambda x: x['timestamp'], reverse=True) # Sort to get most recent
            if vehicle_data['logs']:
                vehicle_data['last_location'] = vehicle_data['logs'][0]['location']
                vehicle_data['last_updated'] = vehicle_data['logs'][0]['timestamp']
            else:
                vehicle_data['last_location'] = 'Unknown'
                vehicle_data['last_updated'] = None

        return vehicles    
    def convert_to_json(self, csv_filepath, json_output_path='lockview_data.json'):
        """Main conversion function: CSV -> JSON"""
        print(f"Reading CSV from: {csv_filepath}")
        df = self.parse_csv(csv_filepath)
        print(f"Found {len(df)} log entries")
        
        print("Processing vehicle data...")
        vehicles = self.process_data(df) # process_data no longer calculates fixed statuses
        print(f"Processed {len(vehicles)} vehicles")
        
        # Create summary statistics (these will be for the raw data, not filtered)
        total_vehicles = len(vehicles)
        
        # Create JSON structure
        json_data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_vehicles': total_vehicles,
                'date_range': 'All available data' # Indicate this is raw data
            },
            'statistics': { # These statistics are for the raw, full dataset
                'total_vehicles': total_vehicles,
                'total_logs': len(df),
                'first_log_date': df['Alert Generated Time'].min() if not df.empty else 'N/A',
                'last_log_date': df['Alert Generated Time'].max() if not df.empty else 'N/A'
            },
            'vehicles': list(vehicles.values())
        }
        
        # Save to JSON file
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ JSON file created: {json_output_path}")
        print(f"📊 Summary:")
        print(f"   Total Vehicles (raw data): {total_vehicles}")
        print(f"   Total Logs (raw data): {len(df)}")
        print(f"   Date Range (raw data): {json_data['statistics']['first_log_date']} to {json_data['statistics']['last_log_date']}")
        
        return json_data


if __name__ == "__main__":
    converter = LockviewConverter()
    
    # Example usage if run directly:
    # json_data = converter.convert_to_json(
    #     'final_imz_report.csv', # Assuming this CSV is in the same directory for direct testing
    #     'lockview_data.json'
    # )
