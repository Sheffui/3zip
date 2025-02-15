import os
import hashlib

def get_largest_restored_folder(base_folder="restored_output"):
    """Find the folder with the largest number in the series 'restored_output_#'."""
    folders = [f for f in os.listdir() if f.startswith(base_folder)]
    if not folders:
        return None
    folder_numbers = [int(f.split("_")[-1]) for f in folders]
    largest_number = max(folder_numbers)
    return f"{base_folder}_{largest_number}"

def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def compare_md5_checksums(input_folder="input", restored_folder=None):
    """Compare MD5 checksums of files in 'restored_folder' with those in 'input_folder'."""
    if restored_folder is None:
        print("No valid restored folder found.")
        return

    restored_files = {f: os.path.join(restored_folder, f) for f in os.listdir(restored_folder)}
    input_files = {f: os.path.join(input_folder, f) for f in os.listdir(input_folder)}

    for filename in restored_files:
        if filename in input_files:
            restored_md5 = calculate_md5(restored_files[filename])
            input_md5 = calculate_md5(input_files[filename])
            if restored_md5 == input_md5:
                print(f"\033[32m{filename}: MD5s match.\033[0m")  # Green
            else:
                print(f"\033[31m{filename}: MD5s do not match.\033[0m")  # Red
        else:
            print(f"{filename}: No matching file found in 'input'.")

def main():
    restored_folder = get_largest_restored_folder()
    if restored_folder:
        print(f"Using folder: {restored_folder}")
        compare_md5_checksums(restored_folder=restored_folder)
    else:
        print("No restored output folder found.")

if __name__ == "__main__":
    main()
