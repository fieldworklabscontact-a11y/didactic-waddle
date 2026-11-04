  eocd_index = content.rfind(b'\x50\x4b\x05\x06')
    if eocd_index == -1:
        raise ValueError("EOCD signature not found.")
    cd_offset = struct.unpack('<I', content[eocd_index + 16:eocd_index + 20])[0]
    cd_size = struct.unpack("<I", content[eocd_index + 12:eocd_index + 16])[0]
    cd_end = cd_offset + cd_size
    patched_content = bytearray(content)

    curr_ptr = cd_offset
    while curr_ptr < cd_end and curr_ptr + 46 < len(patched_content):
        if patched_content[curr_ptr:curr_ptr+4] != b"\x50\x4b\x01\x02":
            break
        local_off = struct.unpack('<I', patched_content[curr_ptr + 42:curr_ptr +46])[0]
        patched_content[curr_ptr + 42:curr_ptr+46] = struct.pack('<I', local_off - zip_start)

        fn_len = struct.unpack('<H', patched_content[curr_ptr+28:curr_ptr+30])[0]
        extra_len = struct.unpack('<H', patched_content[curr_ptr+30:curr_ptr+32])[0]
        comment_len = struct.unpack('<H', patched_content[curr_ptr+32:curr_ptr+34])[0]
        curr_ptr += 46 + fn_len + extra_len + comment_len
    patched_content[eocd_index+16:eocd_index+20] = struct.pack('<I', cd_offset - zip_start)