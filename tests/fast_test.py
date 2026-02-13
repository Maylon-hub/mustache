import urllib.request
import urllib.parse
import json
import os

url = 'http://localhost:5001/upload'
boundary = '----WebKitFormBoundaryFastTest'

# Read file content
with open('datasets/synthetic_large.csv', 'rb') as f:
    file_content = f.read()

# Construct multipart body
body = []
def add_field(name, value):
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="{name}"'.encode())
    body.append(b'')
    body.append(str(value).encode())

add_field('min_cluster_size', 10)
add_field('min_samples', 2)
add_field('metric', 'euclidean')
add_field('cluster_selection_method', 'eom')

# File field
body.append(f'--{boundary}'.encode())
body.append('Content-Disposition: form-data; name="file"; filename="synthetic_large.csv"'.encode())
body.append('Content-Type: text/csv'.encode())
body.append(b'')
body.append(file_content)

body.append(f'--{boundary}--'.encode())
body.append(b'')
body_bytes = b'\r\n'.join(body)

req = urllib.request.Request(url, data=body_bytes)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

try:
    print(f"Sending fast test request (synthetic_large.csv) to {url}...")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print("Status: SUCCESS")
        print(f"Clusters found: {data['results']['n_clusters']}")
except urllib.error.HTTPError as e:
    print(f"Failed: {e.code}")
    print("Body:", e.read().decode('utf-8'))
except Exception as e:
    print(f"Error: {e}")
