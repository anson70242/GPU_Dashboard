# app.py
# This script runs on a central server to display GPU status from multiple GPU servers.

from flask import Flask, render_template, jsonify
import requests # To make HTTP requests to the GPU exporter APIs
import concurrent.futures # For fetching data from multiple servers concurrently

# --- Configuration ---
# IMPORTANT: Replace these with the actual public IP addresses of your GPU servers
# and the port you configured in gpu_exporter.py (default is 5001).
GPU_SERVER_URLS = [
    "http://<Server_1_IP>:5001/gpu-status",
    "http://<Server_1_IP>:5001/gpu-status",
    "http://<Server_1_IP>:5001/gpu-status",
    "http://<Server_1_IP>:5001/gpu-status",
    # Add more servers here if needed
]

# You can assign names to your servers for better display
GPU_SERVER_NAMES = [
    "GPU Server 1",
    "GPU Server 2",
    "GPU Server 3",
    "GPU Server 4",
    # Add corresponding names if you add more servers
]

# Ensure the number of names matches the number of URLs
if len(GPU_SERVER_URLS) != len(GPU_SERVER_NAMES):
    raise ValueError("The number of GPU_SERVER_URLS must match the number of GPU_SERVER_NAMES.")


HOST = '0.0.0.0'  # Makes the app accessible from any IP on the network
PORT = 5000       # Port for the central dashboard; ensure it's not in use

# Initialize the Flask application
app = Flask(__name__)

def fetch_single_gpu_data(url, server_name):
    """
    Fetches GPU data from a single GPU server.
    Includes the server name in the response.
    """
    try:
        # Set a timeout for the request (e.g., 5 seconds)
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4XX or 5XX)
        data = response.json()
        return {"name": server_name, "status": "online", "data": data, "url": url}
    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, etc.
        print(f"Error fetching data from {server_name} ({url}): {e}")
        return {"name": server_name, "status": "offline", "error": str(e), "data": None, "url": url}
    except json.JSONDecodeError as e:
        # Handle errors if the response is not valid JSON
        print(f"Error decoding JSON from {server_name} ({url}): {e}")
        return {"name": server_name, "status": "error", "error": "Invalid JSON response", "data": None, "url": url}


@app.route('/')
def index():
    """
    Renders the main dashboard page.
    The initial data load will be handled by JavaScript calling /data.
    """
    return render_template('index.html', 
                           num_servers=len(GPU_SERVER_URLS), 
                           server_names=GPU_SERVER_NAMES)

@app.route('/data')
def get_all_gpu_data():
    """
    API endpoint to fetch data from all configured GPU servers.
    Uses a thread pool to fetch data concurrently for better performance.
    """
    all_server_data = []

    # Use a ThreadPoolExecutor to fetch data from all servers in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(GPU_SERVER_URLS)) as executor:
        # Create a list of future tasks
        future_to_server = {
            executor.submit(fetch_single_gpu_data, url, GPU_SERVER_NAMES[i]): url 
            for i, url in enumerate(GPU_SERVER_URLS)
        }
        
        for future in concurrent.futures.as_completed(future_to_server):
            try:
                data = future.result()
                all_server_data.append(data)
            except Exception as exc:
                # This catches exceptions from within fetch_single_gpu_data if not already caught,
                # or exceptions during future.result() itself.
                server_url_for_error = future_to_server[future]
                server_index_for_error = GPU_SERVER_URLS.index(server_url_for_error)
                server_name_for_error = GPU_SERVER_NAMES[server_index_for_error]
                print(f"Exception fetching data for {server_name_for_error} ({server_url_for_error}): {exc}")
                all_server_data.append({
                    "name": server_name_for_error, 
                    "status": "error", 
                    "error": "Failed to fetch data due to an internal error in the dashboard app.", 
                    "data": None,
                    "url": server_url_for_error
                })
                
    # Sort data to maintain a consistent order if needed, e.g., by server name
    # This is important because concurrent execution might return results in any order.
    # We'll sort based on the original order of GPU_SERVER_NAMES.
    ordered_data = sorted(all_server_data, key=lambda x: GPU_SERVER_NAMES.index(x['name']))
    
    return jsonify(ordered_data)

if __name__ == '__main__':
    print(f"Starting Central GPU Monitoring Dashboard on http://{HOST}:{PORT}")
    # Run the Flask development server
    # For production, consider using a more robust WSGI server like Gunicorn or uWSGI.
    app.run(host=HOST, port=PORT, debug=False) # debug=False for production/service
