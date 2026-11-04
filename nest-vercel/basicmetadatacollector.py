import ffmpeg
import os
import struct
import zipfile
import static_ffmpeg
import io
static_ffmpeg.add_paths()
while True:
    filename = input("Enter the file you put in this folder: ")
    if os.path.exists(filename):
        print("Successful! Please Wait.")
        break
    else:
        print("File not found.")
while True:
    videoname = input("Enter the video file you put in this folder (Webm is only accepted): ")
    if os.path.exists(videoname) and videoname.endswith(".webm"):
        print("Successful! Please Wait.")
        break
    else:
        print("File not found.")
output_name = input("Enter the name for the final output: ")
if not output_name.endswith('.webm'):
    output_name+='.webm'
while True:
    choice = input(f"Do you want to proceed with storing '{filename}' in '{videoname} named as {output_name}' ? (y/n)")
    if choice in ['y', 'yes']:
        print("analyzing video")
        break
    elif choice in ['n', 'no']:
        print("Analysis cancelled")
        exit()
print("Packaging and injecting payload")
with open(videoname, 'rb') as f:
    webm_data = f.read()
offset_shift = len(webm_data)
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
    if os.path.isdir(filename):
        for root, dirs, files in os.walk(filename):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, filename)
                zipf.write(file_path, arcname)
    else:
        zipf.write(filename, os.path.basename(filename))

zip_bytes = bytearray(zip_buffer.getvalue())
eocd_index = zip_bytes.rfind(b'\x50\x4b\x05\x06')
if eocd_index == -1:
    raise ValueError("Invalid ZIP generated.")
cd_offset = struct.unpack('<I', zip_bytes[eocd_index + 16:eocd_index + 20])[0]
cd_size = struct.unpack("<I", zip_bytes[eocd_index + 12:eocd_index + 16])[0]
curr_ptr = cd_offset
while curr_ptr < cd_offset + cd_size:
    if zip_bytes[curr_ptr:curr_ptr+4] != b"\x50\x4b\x05\x06":
        break
    local_offset = struct.unpack('<I', zip_bytes[curr_ptr + 42:curr_ptr +46])[0]
    new_local_offset = local_offset + offset_shift
    zip_bytes[curr_ptr + 42:curr_ptr+46] = struct.pack("<I", new_localoffset)
    fn_len, extra_len, comment_len = struct.unpack("<HHH", zip_bytes[curr_ptr + 28:curr_ptr + 34])
    curr_ptr += 46 + fn_len + extra_len + comment_len

new_cd_offset = cd_offset + offset_shift
zip_bytes[eocd_index + 16:eocd_index + 20] = struct.pack("I", new_cd_offset)
with open(output_name, "wb") as f:
    f.write(webm_data)
    f.write(zip_bytes)

print(f"Success! File is successfully nested as '{output_name}'.")
