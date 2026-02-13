import urllib.request
import urllib.parse
import json
import os

if not os.path.exists('tests'):
    os.makedirs('tests')

url = 'http://localhost:5001/upload'
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

# Read file content
with open('datasets/simple_2d.csv', 'rb') as f:
    file_content = f.read()

# Construct multipart body
body = []
body.append(f'--{boundary}'.encode())
body.append('Content-Disposition: form-data; name="min_cluster_size"'.encode())
body.append(b'')
body.append(b'5')
body.append(f'--{boundary}'.encode())
body.append('Content-Disposition: form-data; name="distance_metric"'.encode())
body.append(b'')
body.append(b'euclidean')
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
    print(f"Sending request to {url}...")
    with urllib.request.urlopen(req) as response:
        if response.status == 200:
            print("Backend Analysis Successful")
            response_data = json.loads(response.read().decode('utf-8'))
            with open('tests/single_result.json', 'w') as f_out:
                json.dump(response_data, f_out, indent=2)
            print("Result saved to tests/single_result.json")
        else:
            print(f"Failed: {response.status}")
except Exception as e:
    print(f"Error: {e}")
