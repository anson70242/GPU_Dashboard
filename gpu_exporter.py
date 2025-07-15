# gpu_exporter.py
# This script runs on each GPU server to expose GPU status via a Flask API.

import subprocess # For running shell commands like nvidia-smi
import json       # For formatting the output as JSON
from flask import Flask, jsonify # For creating the web API
import re         # For parsing nvidia-smi output using regular expressions

# --- Configuration ---
# You can change the host and port if needed.
# '0.0.0.0' makes the app accessible from any IP address on the network.
# If you want it to be accessible only from localhost, use '127.0.0.1'.
HOST = '0.0.0.0'
PORT = 5001 # Choose a port that is not in use

# Initialize the Flask application
app = Flask(__name__)

def get_gpu_status():
    """
    Fetches GPU status using nvidia-smi and parses the output.
    Returns a list of dictionaries, where each dictionary represents a GPU.
    """
    gpus_data = []
    try:
        # Execute nvidia-smi command to get GPU utilization and memory usage
        # --query-gpu=index,utilization.gpu,memory.used,memory.total
        #   index: The GPU index (0, 1, etc.)
        #   utilization.gpu: Percent of time over the past sample period during which one or more kernels was executing on the GPU.
        #   memory.used: Total memory allocated by active contexts.
        #   memory.total: Total installed GPU memory.
        # --format=csv,noheader,nounits: Output in CSV format, without headers, and without units (e.g., MiB, %)
        #                                This makes parsing easier.
        process = subprocess.Popen(
            ['nvidia-smi', '--query-gpu=index,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True # Ensures stdout and stderr are strings
        )
        stdout, stderr = process.communicate(timeout=10) # Added timeout for safety

        if process.returncode != 0:
            # nvidia-smi command failed
            print(f"Error running nvidia-smi: {stderr.strip()}")
            return {"error": "Failed to run nvidia-smi", "details": stderr.strip()}

        # Process each line of the output (each line corresponds to one GPU)
        for line in stdout.strip().split('\n'):
            if not line: # Skip empty lines
                continue
            parts = line.split(', ')
            if len(parts) == 4:
                gpu_index = int(parts[0])
                gpu_utilization = float(parts[1]) # GPU utilization in %
                memory_used = float(parts[2])     # Used memory in MiB
                memory_total = float(parts[3])    # Total memory in MiB

                gpus_data.append({
                    "gpu_index": gpu_index,
                    "utilization_percent": gpu_utilization,
                    "memory_used_mib": memory_used,
                    "memory_total_mib": memory_total,
                    "memory_free_mib": memory_total - memory_used,
                    "memory_utilization_percent": round((memory_used / memory_total) * 100, 2) if memory_total > 0 else 0
                })
            else:
                print(f"Warning: Could not parse line from nvidia-smi: {line}")


    except FileNotFoundError:
        print("Error: nvidia-smi command not found. Make sure NVIDIA drivers and CUDA toolkit are installed.")
        return {"error": "nvidia-smi not found"}
    except subprocess.TimeoutExpired:
        print("Error: nvidia-smi command timed out.")
        return {"error": "nvidia-smi command timed out"}
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {"error": "An unexpected error occurred", "details": str(e)}

    if not gpus_data:
        # This can happen if nvidia-smi runs but returns no GPU data (e.g., no NVIDIA GPUs)
        return {"error": "No GPU data returned by nvidia-smi"}
        
    return {"gpus": gpus_data}


@app.route('/gpu-status', methods=['GET'])
def gpu_status_api():
    """
    API endpoint to get the GPU status.
    """
    status = get_gpu_status()
    if "error" in status:
        # Return a 500 Internal Server Error if fetching GPU status failed
        return jsonify(status), 500
    return jsonify(status)

if __name__ == '__main__':
    # --- Welcome Message ---
    print("Starting GPU Data Exporter API Server...")
    print(f"Listening on http://{HOST}:{PORT}/gpu-status")
    print("Press CTRL+C to quit.")
    
    # Run the Flask development server
    # For production, consider using a more robust WSGI server like Gunicorn or uWSGI.
    app.run(host=HOST, port=PORT, debug=False) # debug=False for production/service
