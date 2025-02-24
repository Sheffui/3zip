import os
import hashlib

def get_largest_encrypted_folder(base_folder="encrypted_output_"):
    """Find the folder with the largest number in the series 'encrypted_output_#'."""
    folders = [f for f in os.listdir() if f.startswith(base_folder) and os.path.isdir(f)]
    if not folders:
        return None
    folder_numbers = [int(f.split("_")[-1]) for f in folders if f.split("_")[-1].isdigit()]
    if not folder_numbers:
        return None
    largest_number = max(folder_numbers)
    return f"{base_folder}{largest_number}"

def calculate_md5(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def remove_extension(filename):
    """Remove the file extension from a filename."""
    return os.path.splitext(filename)[0]

def compare_md5_checksums(input_folder="input", encrypted_folder=None):
    """Compare MD5 checksums of files in 'encrypted_folder' with those in 'input_folder', ignoring extensions."""
    if encrypted_folder is None:
        print("No valid encrypted folder found.")
        return

    encrypted_files = {remove_extension(f): os.path.join(encrypted_folder, f) for f in os.listdir(encrypted_folder)}
    input_files = {remove_extension(f): os.path.join(input_folder, f) for f in os.listdir(input_folder)}

    for filename in encrypted_files:
        if filename in input_files:
            encrypted_md5 = calculate_md5(encrypted_files[filename])
            input_md5 = calculate_md5(input_files[filename])
            if encrypted_md5 == input_md5:
                print(f"\033[31m{filename}: MD5s matcm.\033[0m")
            else:
                print(f"\033[32m{filename}: MD5s do not match.\033[0m")
        else:
            print(f"{filename}: No matching file found in 'input'.")

def main():
    encrypted_folder = get_largest_encrypted_folder()
    if encrypted_folder:
        print(f"Using folder: {encrypted_folder}")
        compare_md5_checksums(encrypted_folder=encrypted_folder)
    else:
        print("No encrypted output folder found.")

if __name__ == "__main__":
    main()
