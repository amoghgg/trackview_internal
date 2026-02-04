from flask import Flask, send_from_directory, request, jsonify, Response
import os
from lockview_converter import LockviewConverter # Import our converter
import json # Import json to read lockview_data.json
import io # For CSV export
import csv # For CSV export

app = Flask(__name__, static_folder='.')

# Initialize the converter
converter = LockviewConverter()

@app.route('/')
def serve_dashboard():
    return send_from_directory('.', 'lockview_dashboard_json.html')

@app.route('/lockview_data.json')
def serve_data_json():
    return send_from_directory('.', 'lockview_data.json')

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
            
            # Ensure logs are sorted latest to oldest (already done by converter, but re-confirming logic)
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
                for log in logs:
                    row = [
                        vehicle_id,
                        center_code,
                        last_location_vehicle,
                        log.get('timestamp', 'N/A'),
                        log.get('status', 'No Data'),
                        log.get('message', 'No Data')
                    ]
                    writer.writerow(row)

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
