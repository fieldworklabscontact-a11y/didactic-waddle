import zipfile
import os

while True:
    videoname = input("Enter the webm file containing your file: ")
    if os.path.exists(videoname):
        break
    print("File not found.")

output_dir = input("enter the folder name you want to extract files into: ")

try:
    with zipfile.ZipFile(videoname, 'r') as zipf:
        zipf.extractall(output_dir)
        print(f"Success! Output is in '{output_dir}'.")
except Exception as e:
    print(f"Extraction failed {e}")