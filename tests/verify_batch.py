import urllib.request
import urllib.parse
import json
import os

if not os.path.exists('tests'):
    os.makedirs('tests')

url = 'http://localhost:5001/batch'
boundary = '----WebKitFormBoundaryBatchTest'

# Read file content
with open('datasets/simple_2d.csv', 'rb') as f:
    file_content = f.read()

# Construct multipart body
body = []
def add_field(name, value):
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="{name}"'.encode())
    body.append(b'')
    body.append(str(value).encode())

add_field('min_mpts', 5)
add_field('max_mpts', 15)
add_field('step_mpts', 5)
add_field('metric', 'euclidean')

# File field
body.append(f'--{boundary}'.encode())
body.append('Content-Disposition: form-data; name="file"; filename="simple_2d.csv"'.encode())
body.append('Content-Type: text/csv'.encode())
body.append(b'')
body.append(file_content)

body.append(f'--{boundary}--'.encode())
body.append(b'')
body_bytes = b'\r\n'.join(body)

req = urllib.request.Request(url, data=body_bytes)
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

try:
    print(f"Sending batch request to {url}...")
    # Increase timeout for batch processing
    with urllib.request.urlopen(req, timeout=60) as response:
        if response.status == 200:
            print("Backend Batch analysis Successful")
            response_data = json.loads(response.read().decode('utf-8'))
            with open('tests/batch_result.json', 'w') as f_out:
                json.dump(response_data, f_out, indent=2)
            print("Result saved to tests/batch_result.json")
        else:
            print(f"Failed: {response.status}")
except Exception as e:
    print(f"Error: {e}")
