import zipfile
import os
import io
import struct

videoname = input("Enter the webm file containing your file: ")
if os.path.exists(videoname):
    print("successful")
else:
    print("File not found.")

output_dir = input("enter the folder name you want to extract files into: ").strip()

try:
    with open(videoname, 'rb') as f:
        content = f.read()

    zip_start = content.find(b'\x50\x4b\x05\x06')
    if zip_start == -1:
        raise ValueError("No ZIP archive signature found in the file.")
    zip_stream = io.BytesIO(content[zip_start:])
    with zipfile.ZipFile(zip_stream, 'r') as zipf:
        os.makedirs(output_dir, exist_ok=True)
        zipf.extractall(output_dir)
        print(f"Success! Output is in '{output_dir}'.")
except Exception as e:
    print(f"Extraction failed {e}")