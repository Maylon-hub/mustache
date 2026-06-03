import json
import base64
import numpy as np

with open('scratch/reachability_mpts_11.json', 'r') as f:
    data = json.load(f)

y_data = data['data'][0]['y']
bdata = y_data['bdata']
raw_bytes = base64.b64decode(bdata)
array = np.frombuffer(raw_bytes, dtype='float64')

print("Decoded array length:", len(array))
print("First 20 reachability values:", list(array[:20]))
print("Is sorted?", all(array[i] <= array[i+1] for i in range(len(array)-1)))
