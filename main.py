"""
Proxy Server for API Requests

This Flask application acts as a proxy server, forwarding requests to a specified API endpoint.
It includes functionality to replace API keys in the 'Authorization' header and to filter out
certain keywords from the response content.

Author: Genesiu
Created on: 2024-01-12
"""

from flask import Flask, request, Response
import requests
import logging

app = Flask(__name__)

API_URL = "https://Baseurl"  # Base URL for the API endpoint

# API Key to be replaced and its replacement
KEY_TO_REPLACE = "sk-pbukey"
REPLACEMENT_KEY = "sk-reallkey"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy(path):
    # Check if the path contains the required 'completions' segment
    if 'completions' not in path:
        logging.info(f"Request path {path} is not allowed, discarding.")
        return Response("Request path is not allowed.", status=403)

    try:
        method = request.method
        url = f"{API_URL}/{path.lstrip('/')}"  # Construct the full URL for the request
        data = request.get_data() if method in ['POST', 'PUT', 'PATCH'] else None

        headers = dict(request.headers)
        headers['Host'] = API_URL.split('://')[-1]  # Set the 'Host' header

        # Log the 'Authorization' header sent by the client
        auth_header = headers.get("Authorization")
        logging.info(f"Client sent Authorization header: {auth_header}")

        # Replace the API Key in the 'Authorization' header if necessary
        if auth_header and KEY_TO_REPLACE in auth_header:
            new_auth_header = auth_header.replace(KEY_TO_REPLACE, REPLACEMENT_KEY)
            headers['Authorization'] = new_auth_header
            logging.info(f"Replaced API Key from {KEY_TO_REPLACE} to {REPLACEMENT_KEY}")

        # Remove headers that might expose proxy information
        headers.pop('X-Forwarded-For', None)
        headers.pop('X-Real-IP', None)
        headers.pop('X-Forwarded-Proto', None)
        headers.pop('X-Forwarded-Host', None)

        # Handle CORS preflight requests
        if method == 'OPTIONS':
            response_headers = {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, PATCH, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            }
            return Response(status=200, headers=response_headers)

        # Forward the request to the API endpoint
        response = requests.request(method, url, headers=headers, data=data)

        # Log the response status code and headers
        logging.info(f"Server returned status code: {response.status_code}")
        logging.info(f"Server returned headers: {response.headers}")

        # Filter out certain keywords from the response content
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection', 'server']
        response_headers = [(name, value) for (name, value) in response.headers.items() if name.lower() not in excluded_headers]

        if "some word" in response.content.decode():
            response_content = response.content.decode().replace("some word", "[Blocked Content]")
            logging.info("Blocked content containing 'some word' in the response.")
            return Response(response_content, response.status_code, headers=dict(response_headers))
        else:
            return Response(response.content, response.status_code, headers=dict(response_headers))

    except requests.RequestException as e:
        logging.error(f"Error handling request: {e}")
        return Response("Error: An unexpected error occurred. Please try again later.", status=500)
    except Exception as e:
        logging.error(f"Internal Server Error: {str(e)}")
        return Response("Internal Server Error: We are experiencing technical difficulties.", status=500)

if __name__ == "__main__":
    app.run(port=8090)
