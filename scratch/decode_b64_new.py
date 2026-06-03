import base64
import numpy as np

bdata = "KTFPwN5bJEClRMHToYgBQLanp7pkDgFA2LACpoOS+D+u2K6yaSfQ/67YrrJpJ9D/rtiusmkn0P+u2K6yaSfQ/67YrrJpJ9D/rtiusmkn0P+u2K6yaSfQ/67YrrJpJ9D/rtiusmkn0P+u2K6yaSfQ/67YrrJpJ9D/rtiusmkn0P+u2K6yaSfQ/67YrrJpJ9D9+Zvx6R63zP35m/HpHrfM/fmb8eket8z9+Zvx6R63zPwa3K6yaSfQ/qtDI3azw9D/6cXKbkFv1PzOVO/xT6/Y/6PdFWnSw9z8odrztEQD6PxTp+ydJQfo/BHzf/UKY+j8CRxaIMMwAQEoKk2SpSwZAVQ3P6mJv/z9VDc/qim//P1UNz+pib/8/VQ3P6mJv/z9VDc/qim//P1UNz+pib/8/9qoadlaC+j/9qGnZWgvo/kGMScGk79z+QYxJwaTv3P5BjEnBpO/c/kGMScGk79z+QYxJwaTv3P66ojuXc0fc/rqojuXc0fc/rqojuXc0fc/rqojuXc0fc/NWUKo/5D+D/9qGnZWgvo/9qGnZWgvo/b/vwnUWI+j9c6UFoQF77P5qJu8ACVxpANtofhNJ4AUC3S1lL3or6P7dLWUveivo/t0tZS96K+j+3S1lL3or6PxsqjvVflfU/GyqO9V+V9T8bKo71X5X1PxsqjvVflfU/GyqO9V+V9T8bKo71X5X1PxsqjvVflfU/oaK27sBU9j+ayPCL7Av3P6ApHwofavg/oCkfCh9q+D8nnn+KM6f5P6THlevZE/o/90udfO3C+j/3S5187cL6P7cp+mEbBv0/PdKHDB6U/z88W7xREIIiQEiUjM7JgQVA8inbKc8x8j/yKdspzzHyPyTGfWTO++4/JMZ9ZM777j/NjxRRTXjuPyZZD8ftKuo/JlkPx+0q6j8mWQ/H7SrqPyZZD8ftKuo/JlkPx+0q6j9uWQ/H7SrqPy1YE9fN8ew/+A+CQoQJ7j/yB6pVYXbvP4cEDEIxJ/A/QpfR8qsE8j/rsDP8xh3yP/Ip2ynPMfI/Q9d/Goe+8j8GLdzIeP3zP78I0kH5Ffc/vwjSQfkV9z8RV9GtB1n5P7Rp9JeZh/s/gzDeLH5nAEA="
raw_bytes = base64.b64decode(bdata)
array = np.frombuffer(raw_bytes, dtype='float64')
print("Decoded array length:", len(array))
print("Decoded array values:", list(array))
print("Is sorted?", all(array[i] <= array[i+1] for i in range(len(array)-1)))
