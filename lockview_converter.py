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
        """Process dataframe and calculate status for date ranges"""
        vehicles = {}
        
        for _, row in df.iterrows():
            vehicle_id = row['Vehicle No.']
            date_time = pd.to_datetime(row['Alert Generated Time'], format='%d-%m-%Y %H:%M', errors='coerce')
            location = row['Address']
            message = row['Message']
            center_id = row.get('Center ID', 'N/A')  # Get Center ID
            status = self.determine_status(message)
            
            if pd.isna(date_time):
                continue
            
            # Initialize vehicle if not exists
            if vehicle_id not in vehicles:
                vehicles[vehicle_id] = {
                    'vehicle_id': vehicle_id,
                    'center_id': str(center_id),  # Add center code
                    'logs': [],
                    'status_15_20': 'No Data',
                    'status_21': 'No Data',
                    'last_location': 'Unknown',
                    'last_updated': None
                }
            
            # Add log entry
            log_entry = {
                'timestamp': date_time.strftime('%Y-%m-%d %H:%M'),
                'location': location,
                'message': message,
                'status': status,
                'center_id': str(center_id),
                'day': date_time.day
            }
            vehicles[vehicle_id]['logs'].append(log_entry)
        
        # Process each vehicle to determine status for date ranges
        for vehicle_id, vehicle_data in vehicles.items():
            # Sort logs by timestamp
            vehicle_data['logs'].sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Get status for 15-20th (most recent in this range)
            logs_15_20 = [log for log in vehicle_data['logs'] if 15 <= log['day'] <= 20]
            if logs_15_20:
                vehicle_data['status_15_20'] = logs_15_20[0]['status']
            
            # Get status for 21st
            logs_21 = [log for log in vehicle_data['logs'] if log['day'] == 21]
            if logs_21:
                vehicle_data['status_21'] = logs_21[0]['status']
            
            # Set last location and update time
            if vehicle_data['logs']:
                vehicle_data['last_location'] = vehicle_data['logs'][0]['location']
                vehicle_data['last_updated'] = vehicle_data['logs'][0]['timestamp']
        
        return vehicles
    
    def convert_to_json(self, csv_filepath, json_output_path='lockview_data.json'):
        """Main conversion function: CSV -> JSON"""
        print(f"Reading CSV from: {csv_filepath}")
        df = self.parse_csv(csv_filepath)
        print(f"Found {len(df)} log entries")
        
        print("Processing vehicle data...")
        vehicles = self.process_data(df)
        print(f"Processed {len(vehicles)} vehicles")
        
        # Create summary statistics
        total_vehicles = len(vehicles)
        locked_15_20 = sum(1 for v in vehicles.values() if v['status_15_20'] == 'Locked')
        locked_21 = sum(1 for v in vehicles.values() if v['status_21'] == 'Locked')
        unlocked_15_20 = sum(1 for v in vehicles.values() if v['status_15_20'] == 'Unlocked')
        unlocked_21 = sum(1 for v in vehicles.values() if v['status_21'] == 'Unlocked')
        
        # Create JSON structure
        json_data = {
            'metadata': {
                'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_vehicles': total_vehicles,
                'date_range': '15-01-2026 to 21-01-2026'
            },
            'statistics': {
                'total_vehicles': total_vehicles,
                'status_15_20': {
                    'locked': locked_15_20,
                    'unlocked': unlocked_15_20,
                    'no_data': total_vehicles - locked_15_20 - unlocked_15_20
                },
                'status_21': {
                    'locked': locked_21,
                    'unlocked': unlocked_21,
                    'no_data': total_vehicles - locked_21 - unlocked_21
                }
            },
            'vehicles': list(vehicles.values())
        }
        
        # Save to JSON file
        with open(json_output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ JSON file created: {json_output_path}")
        print(f"📊 Summary:")
        print(f"   Total Vehicles: {total_vehicles}")
        print(f"   Status (15-20th) - Locked: {locked_15_20}, Unlocked: {unlocked_15_20}")
        print(f"   Status (21st) - Locked: {locked_21}, Unlocked: {unlocked_21}")
        
        return json_data


if __name__ == "__main__":
    converter = LockviewConverter()
    
    # Example usage if run directly:
    # json_data = converter.convert_to_json(
    #     'final_imz_report.csv', # Assuming this CSV is in the same directory for direct testing
    #     'lockview_data.json'
    # )
