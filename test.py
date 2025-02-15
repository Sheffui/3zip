import os
import time
import random
import shutil

# Configuration
TEST_INPUT_FILES = ["test1.txt", "test2.pdf", "test3.mp4"]  # Add your test files here
TEST_IMAGE_FILES = ["image1.png", "image2.png"]  # Add your test image files here
TEST_PASSWORD = "testpassword123"  # Modify password here
TEMP_DIR = ".temp"
ENCRYPTED_DIR = "encrypted_output"
DECRYPTED_DIR = "decrypted_output"

# Helper Functions
def setup_test_files():
    """Create test files with random data for testing."""
    for file in TEST_INPUT_FILES:
        with open(file, "wb") as f:
            size = random.randint(1024 * 1024, 5 * 1024 * 1024)  # Files between 1MB and 5MB
            f.write(os.urandom(size))

def cleanup_test_files():
    """Clean up generated files after testing."""
    for file in TEST_INPUT_FILES + TEST_IMAGE_FILES:
        if os.path.exists(file):
            os.remove(file)
    if os.path.exists(TEMP_DIR):
        shutil.rmtree(TEMP_DIR)
    if os.path.exists(ENCRYPTED_DIR):
        shutil.rmtree(ENCRYPTED_DIR)
    if os.path.exists(DECRYPTED_DIR):
        shutil.rmtree(DECRYPTED_DIR)

# Test Functions
def encrypt_test():
    """Test the encryption process and measure performance."""
    print("Starting encryption test...")
    start_time = time.time()
    os.system(f"python3 program.py --encrypt --files {' '.join(TEST_INPUT_FILES)} --images {' '.join(TEST_IMAGE_FILES)} --password {TEST_PASSWORD}")
    end_time = time.time()

    # Calculate compression ratio
    original_size = sum(os.path.getsize(file) for file in TEST_INPUT_FILES)
    encrypted_size = sum(os.path.getsize(os.path.join(ENCRYPTED_DIR, f)) for f in os.listdir(ENCRYPTED_DIR))
    compression_ratio = encrypted_size / original_size

    print(f"Encryption completed in {end_time - start_time:.2f} seconds.")
    print(f"Compression ratio: {compression_ratio:.2f}")
    return compression_ratio

def decrypt_test():
    """Test the decryption process and measure performance."""
    print("Starting decryption test...")
    start_time = time.time()
    os.system(f"python3 program.py --decrypt --images {' '.join(TEST_IMAGE_FILES)} --password {TEST_PASSWORD}")
    end_time = time.time()

    print(f"Decryption completed in {end_time - start_time:.2f} seconds.")
    return end_time - start_time

def validate_files():
    """Validate that original and decrypted files match."""
    print("Validating files...")
    for original_file in TEST_INPUT_FILES:
        decrypted_file = os.path.join(DECRYPTED_DIR, os.path.basename(original_file))
        if not os.path.exists(decrypted_file):
            print(f"Error: Decrypted file {decrypted_file} not found!")
            return False
        with open(original_file, "rb") as orig, open(decrypted_file, "rb") as dec:
            if orig.read() != dec.read():
                print(f"Error: File {original_file} does not match {decrypted_file}!")
                return False
    print("All files validated successfully.")
    return True

# Main Test Runner
def main():
    setup_test_files()
    try:
        compression_ratio = encrypt_test()
        decrypt_time = decrypt_test()
        if validate_files():
            print("\nTest Results:")
            print(f"Compression Ratio: {compression_ratio:.2f}")
            print(f"Decryption Time: {decrypt_time:.2f} seconds")
        else:
            print("Test failed during validation.")
    finally:
        cleanup_test_files()

if __name__ == "__main__":
    main()
