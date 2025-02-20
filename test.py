import time
import os
from main import encrypt_file, decrypt_file, compress_file, decompress_file, create_tarball, extract_tarball, embed_file, extract_file

def measure_time(func, *args, **kwargs):
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    return result, end_time - start_time

def main():
    temp_dir = ".temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    input_files = ["input/text1.txt", "docx.docx"]
    image_files = ["input/000.png", "input/00.jpg", "input/0.webp"]
    image_files_e = [".temp/000.png", ".temp/00.png", ".temp/0.png"]
    key = "testkey1234567890"
    
    tarball_file = os.path.join(temp_dir, "test.tar")
    compressed_file = os.path.join(temp_dir, "test.lzma")
    encrypted_file = os.path.join(temp_dir, "test.cam")
    extracted_file = os.path.join(temp_dir, "extracted.cam")
    decompressed_file = os.path.join(temp_dir, "decompressed.tar")
    extracted_folder = os.path.join(temp_dir, "extracted")
    os.makedirs(extracted_folder, exist_ok=True)
    
    print("Testing encryption and embedding process...")
    _, tar_time = measure_time(create_tarball, input_files, tarball_file)
    _, compress_time = measure_time(compress_file, tarball_file, compressed_file)
    _, encrypt_time = measure_time(encrypt_file, compressed_file, key, encrypted_file)
    _, embed_time = measure_time(embed_file, image_files, encrypted_file, temp_dir)
    
    print(f"Tarball creation time: {tar_time:.4f} sec")
    print(f"Compression time: {compress_time:.4f} sec")
    print(f"Encryption time: {encrypt_time:.4f} sec")
    print(f"Embedding time: {embed_time:.4f} sec")
    
    print("Testing decryption and extraction process...")
    _, extract_time = measure_time(extract_file, image_files_e, extracted_file)
    _, decrypt_time = measure_time(decrypt_file, extracted_file, key, decompressed_file)
    _, untar_time = measure_time(extract_tarball, decompressed_file, extracted_folder)
    
    print(f"Extraction time: {extract_time:.4f} sec")
    print(f"Decryption time: {decrypt_time:.4f} sec")
    print(f"Untar time: {untar_time:.4f} sec")
    
    print("Test completed.")
    
if __name__ == "__main__":
    main()
