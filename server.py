from flask import Flask, send_from_directory, request, jsonify, Response
import os
from lockview_converter import LockviewConverter # Import our converter
import json # Import json to read lockview_data.json
import io # For CSV export
import csv # For CSV export
from datetime import datetime

app = Flask(__name__, static_folder='.')

# Initialize the converter
converter = LockviewConverter()

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'lockview_dashboard_json.html')

@app.route('/lockview_data.json')
def serve_data_json():
    return send_from_directory('.', 'lockview_data.json')

@app.route('/get_filtered_data')
def get_filtered_data():
    dateRange1Start_str = request.args.get('dateRange1Start')
    dateRange1End_str = request.args.get('dateRange1End')
    dateRange2Start_str = request.args.get('dateRange2Start')
    dateRange2End_str = request.args.get('dateRange2End')
    searchVehicle = request.args.get('searchVehicle', '').lower()
    searchCenter = request.args.get('searchCenter', '').lower()

    json_file_path = os.path.join(app.root_path, 'lockview_data.json')
    if not os.path.exists(json_file_path):
        return jsonify({'error': 'lockview_data.json not found. Upload CSV first.'}), 404

    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            full_data = json.load(f)
        
        all_vehicles_raw = full_data.get('vehicles', [])
        
        processed_vehicles = []
        for vehicle_raw in all_vehicles_raw:
            vehicle = vehicle_raw.copy()
            
            # Convert log timestamps to datetime objects for easier comparison
            for log in vehicle['logs']:
                log['datetime'] = datetime.strptime(log['timestamp'], '%Y-%m-%d %H:%M')

            # --- Process Status 1 ---
            status1 = 'No Data'
            if dateRange1Start_str and dateRange1End_str:
                start1 = datetime.strptime(dateRange1Start_str, '%Y-%m-%d')
                end1 = datetime.strptime(dateRange1End_str, '%Y-%m-%d')

                relevant_logs1 = [log for log in vehicle['logs'] if start1.date() <= log['datetime'].date() <= end1.date()]
                if relevant_logs1:
                    relevant_logs1.sort(key=lambda x: x['datetime'], reverse=True)
                    status1 = relevant_logs1[0]['status']
            vehicle['status_15_20'] = status1 # Using existing key for dynamic status 1

            # --- Process Status 2 ---
            status2 = 'No Data'
            if dateRange2Start_str and dateRange2End_str:
                start2 = datetime.strptime(dateRange2Start_str, '%Y-%m-%d')
                end2 = datetime.strptime(dateRange2End_str, '%Y-%m-%d')

                relevant_logs2 = [log for log in vehicle['logs'] if start2.date() <= log['datetime'].date() <= end2.date()]
                if relevant_logs2:
                    relevant_logs2.sort(key=lambda x: x['datetime'], reverse=True)
                    status2 = relevant_logs2[0]['status']
            vehicle['status_21'] = status2 # Using existing key for dynamic status 2

            # Apply search filters
            vehicle_id_matches = not searchVehicle or searchVehicle in vehicle['vehicle_id'].lower()
            center_id_matches = not searchCenter or searchCenter in vehicle['center_id'].lower()
            
            if vehicle_id_matches and center_id_matches:
                processed_vehicles.append(vehicle)

        # Update metadata for the filtered response
        filtered_metadata = full_data.get('metadata', {}).copy()
        filtered_metadata['date_range_1'] = f"{dateRange1Start_str} to {dateRange1End_str}" if dateRange1Start_str and dateRange1End_str else "N/A"
        filtered_metadata['date_range_2'] = f"{dateRange2Start_str} to {dateRange2End_str}" if dateRange2Start_str and dateRange2End_str else "N/A"
        filtered_metadata['total_vehicles'] = len(processed_vehicles)

        # Update statistics for the filtered response
        filtered_statistics = full_data.get('statistics', {}).copy()
        
        # Calculate statistics for dynamic ranges
        locked_1 = sum(1 for v in processed_vehicles if v['status_15_20'] == 'Locked')
        unlocked_1 = sum(1 for v in processed_vehicles if v['status_15_20'] == 'Unlocked')
        no_data_1 = len(processed_vehicles) - locked_1 - unlocked_1

        locked_2 = sum(1 for v in processed_vehicles if v['status_21'] == 'Locked')
        unlocked_2 = sum(1 for v in processed_vehicles if v['status_21'] == 'Unlocked')
        no_data_2 = len(processed_vehicles) - locked_2 - unlocked_2
        
        filtered_statistics['total_vehicles'] = len(processed_vehicles)
        filtered_statistics['status_15_20'] = { # Reusing these keys
            'locked': locked_1,
            'unlocked': unlocked_1,
            'no_data': no_data_1
        }
        filtered_statistics['status_21'] = { # Reusing these keys
            'locked': locked_2,
            'unlocked': unlocked_2,
            'no_data': no_data_2
        }

        # Construct the response JSON
        response_data = {
            'metadata': filtered_metadata,
            'statistics': filtered_statistics,
            'vehicles': processed_vehicles
        }
        
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': f'Error filtering data: {str(e)}'}), 500


@app.route('/upload_csv', methods=['POST'])
def upload_csv():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        # Save the uploaded file temporarily
        csv_path = os.path.join(app.root_path, 'uploaded_data.csv')
        file.save(csv_path)

        try:
            # Process the CSV and update lockview_data.json
            json_output_path = os.path.join(app.root_path, 'lockview_data.json')
            converter.convert_to_json(csv_path, json_output_path)
            os.remove(csv_path) # Clean up the temporary CSV
            return jsonify({'message': 'CSV processed successfully and dashboard data updated!'}), 200
        except Exception as e:
            os.remove(csv_path) # Clean up even if error
            return jsonify({'error': f'Error processing CSV: {str(e)}'}), 500

@app.route('/export_csv')
def export_csv():
    try:
        # Read the current lockview_data.json
        json_file_path = os.path.join(app.root_path, 'lockview_data.json')
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vehicles = data.get('vehicles', [])

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        header = [
            'Vehicle ID', 
            'Center Code', 
            'Last Location (Vehicle)', # Changed to specify it's the vehicle's last location
            'Timestamp (Log)', 
            'Status (Log)', 
            'Message (Log)'
        ]
        writer.writerow(header)

        # Write vehicle data, one row per log entry
        for vehicle in vehicles:
            vehicle_id = vehicle.get('vehicle_id', '')
            center_code = vehicle.get('center_id', 'N/A')
            last_location_vehicle = vehicle.get('last_location', 'Unknown')
            
            logs = sorted(vehicle.get('logs', []), key=lambda x: x['timestamp'], reverse=True)

            if not logs:
                # If no logs, still write one row for the vehicle with N/A for log-specific fields
                row = [
                    vehicle_id,
                    center_code,
                    last_location_vehicle,
                    'N/A', # Timestamp
                    'No Data', # Status
                    'No Data' # Message
                ]
                writer.writerow(row)
            else:
                first_log_of_vehicle = True
                for log in logs:
                    current_vehicle_id = vehicle_id if first_log_of_vehicle else ''
                    current_center_code = center_code if first_log_of_vehicle else ''
                    current_last_location_vehicle = last_location_vehicle if first_log_of_vehicle else ''

                    row = [
                        current_vehicle_id,
                        current_center_code,
                        current_last_location_vehicle,
                        log.get('timestamp', 'N/A'),
                        log.get('status', 'No Data'),
                        log.get('message', 'No Data')
                    ]
                    writer.writerow(row)
                    first_log_of_vehicle = False # Set to False after the first log

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment;filename=lockview_dashboard_export.csv'}
        )

    except FileNotFoundError:
        return jsonify({'error': 'No data available to export. Please upload a CSV first.'}), 404
    except Exception as e:
        return jsonify({'error': f'Error generating CSV: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
