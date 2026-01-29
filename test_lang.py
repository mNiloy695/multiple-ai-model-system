from langdetect import detect
text = "উমরনাম কী"
try:
    print(f"Detected: {detect(text)}")
except Exception as e:
    print(f"Error: {e}")
