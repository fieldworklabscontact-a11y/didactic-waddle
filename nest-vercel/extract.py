import zipfile
import os
import io
import struct
while True:
    videoname = input("Enter the webm file containing your file: ")
    if os.path.exists(videoname):
        print("successful")
        break
    print("File not found.")

output_dir = input("enter the folder name you want to extract files into: ").strip()

try:
    with open(videoname, 'rb') as f:
        content = f.read()
    zip_start = content.find(b'\x50\x4b\x03\x04')
    if zip_start == -1:
        raise ValueError("No ZIP archive signature found in the file.")
    eocd_index = content.rfind(b'\x50\x4b\x05\x06')
    if eocd_index == -1:
        raise ValueError("EOCD signature not found.")
    cd_offset = struct.unpack('<I', content[eocd_index + 16:eocd_index + 20])[0]
    cd_size = struct.unpack('<I', content[eocd_index + 12:eocd_index + 16])[0]

    patched_content = bytearray(content)
    # 3. Smart check: Only patch if cd_offset is absolute (includes the video size)
    if cd_offset >= zip_start:
        print("[*] Absolute offsets detected. Normalizing pointers...")
        curr_ptr = cd_offset
        cd_end = cd_offset + cd_size

        while curr_ptr < cd_end and curr_ptr + 46 < len(patched_content):
            if patched_content[curr_ptr:curr_ptr+4] != b'\x50\x4b\x01\x02':
                break
            local_off = struct.unpack('<I', patched_content[curr_ptr + 42:curr_ptr + 46])[0]
            if local_off >= zip_start:
                patched_content[curr_ptr + 42:curr_ptr + 46] = struct.pack('<I', local_off - zip_start)

            fn_len = struct.unpack('<H', patched_content[curr_ptr+28:curr_ptr+30])[0]
            extra_len = struct.unpack('<H', patched_content[curr_ptr+30:curr_ptr+32])[0]
            comment_len = struct.unpack('<H', patched_content[curr_ptr+32:curr_ptr+34])[0]
            curr_ptr += 46 + fn_len + extra_len + comment_len
        patched_content[eocd_index+16:eocd_index+20] = struct.pack('<I', cd_offset - zip_start)
    else:
        print("[*] Relative offsets detected. Skipping manual patching.")

    zip_stream = io.BytesIO(patched_content[zip_start:])
    with zipfile.ZipFile(zip_stream, 'r') as zipf:
        os.makedirs(output_dir, exist_ok=True)
        zipf.extractall(output_dir)
        print(f"Success! Output is in '{output_dir}'.")
except Exception as e:
    print(f"Extraction failed {e}")
