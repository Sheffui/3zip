import os
import tarfile
import lzma
import stegano.lsb as lsb
import camellia
import secrets
import tkinter as tk
from tkinter import filedialog, messagebox


def ensure_output_folder(base_name):
    """Ensure an incremented output folder exists."""
    index = 0
    while True:
        folder_name = f"{base_name}_{index}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            return folder_name
        index += 1


def cleanup_temp_folder(temp_dir):
    """Remove the .temp folder and its contents."""
    if os.path.exists(temp_dir):
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)


def create_tarball(files, tarball_name):
    """Create a tarball from a list of files."""
    with tarfile.open(tarball_name, "w") as tar:
        for file in files:
            tar.add(file, arcname=os.path.basename(file))


def extract_tarball(tarball_name, output_dir):
    """Extract files from a tarball."""
    with tarfile.open(tarball_name, "r") as tar:
        tar.extractall(path=output_dir)


def compress_file(input_file, output_file):
    """Compress a file using LZMA."""
    with open(input_file, 'rb') as f_in:
        data = f_in.read()
    compressed_data = lzma.compress(data)
    with open(output_file, 'wb') as f_out:
        f_out.write(compressed_data)


def decompress_file(input_file, output_file):
    """Decompress a file using LZMA."""
    with open(input_file, 'rb') as f_in:
        compressed_data = f_in.read()
    data = lzma.decompress(compressed_data)
    with open(output_file, 'wb') as f_out:
        f_out.write(data)


def encrypt_file(input_file, key):
    """Encrypt a file using Camellia cipher with CBC mode."""
    with open(input_file, 'rb') as f_in:
        data = f_in.read()

    block_size = 16  # Camellia block size
    padding_length = block_size - (len(data) % block_size)
    data += bytes([padding_length] * padding_length)  # Padding with the length of padding

    iv = secrets.token_bytes(block_size)  # Generate a random 16-byte IV
    cipher = camellia.CamelliaCipher(key.encode().ljust(32)[:32], mode=1, IV=iv)

    encrypted_data = cipher.encrypt(data)

    # Split the encrypted data into chunks for embedding in images
    chunk_size = len(encrypted_data) // 2  # Split in half
    chunk1 = encrypted_data[:chunk_size]
    chunk2 = encrypted_data[chunk_size:]

    # Return IV and chunks
    return iv, chunk1, chunk2


def embed_in_images(image_files, encrypted_data, output_folder):
    """Embed data into multiple images."""
    iv, chunk1, chunk2 = encrypted_data  # Decompose the encrypted data

    # Embed the data into the images using LSB (Least Significant Bit) method
    image1 = image_files[0]
    image2 = image_files[1]

    # Embed `iv + chunk1` into the first image
    secret_image1 = lsb.hide(image1, (iv + chunk1).hex())
    secret_image1.save(os.path.join(output_folder, os.path.basename(image1)))

    # Embed `chunk2` into the second image
    secret_image2 = lsb.hide(image2, chunk2.hex())
    secret_image2.save(os.path.join(output_folder, os.path.basename(image2)))


def extract_from_images(image_files):
    """Extract and combine data from images."""
    if len(image_files) != 2:
        raise ValueError("Exactly 2 images are required for extraction.")

    # Extract data from each image
    try:
        data1 = lsb.reveal(image_files[0])
        data2 = lsb.reveal(image_files[1])
    except Exception as e:
        raise ValueError(f"Error extracting from images: {e}")

    # Combine the data: `data1` contains `iv + chunk1`, `data2` contains `chunk2`
    if data1 is None or data2 is None:
        raise ValueError("Unable to extract data from one or more images.")

    # Decode hex back to binary
    combined_data = bytes.fromhex(data1) + bytes.fromhex(data2)
    return combined_data


def decrypt_file(input_file, key, output_file):
    """Decrypt a file using Camellia cipher with CBC mode."""
    with open(input_file, 'rb') as f_in:
        file_data = f_in.read()

    iv = file_data[:16]  # Extract IV (first 16 bytes)
    encrypted_data = file_data[16:]  # Extract encrypted data

    cipher = camellia.CamelliaCipher(key.encode().ljust(32)[:32], mode=1, IV=iv)

    decrypted_data = cipher.decrypt(encrypted_data)

    # Check length of decrypted data
    print(f"Decrypted data length (including padding): {len(decrypted_data)}")

    # Remove padding (last byte indicates the padding length)
    padding_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-padding_length]  # Remove the padding

    with open(output_file, 'wb') as f_out:
        f_out.write(decrypted_data)  # Save the decrypted data

    print(f"Decrypted data length (after padding removal): {len(decrypted_data)}")


class FileSecurityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Security Application")
        self.main_menu()

    def main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="File Security Application", font=("Arial", 16)).pack(pady=20)
        tk.Button(self.root, text="Encrypt Files", command=self.encrypt_menu).pack(pady=10)
        tk.Button(self.root, text="Decrypt Files", command=self.decrypt_menu).pack(pady=10)

    def encrypt_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.input_files = []
        self.image_files = []
        self.key = tk.StringVar()
        tk.Label(self.root, text="Encrypt Files", font=("Arial", 16)).pack(pady=10)
        tk.Button(self.root, text="Select Files", command=self.browse_input_files).pack()
        tk.Button(self.root, text="Select Images", command=self.browse_image_files).pack()
        tk.Label(self.root, text="Currently Selected Files:").pack()
        self.selected_files_label = tk.Label(self.root, text="")
        self.selected_files_label.pack()
        tk.Label(self.root, text="Currently Selected Images:").pack()
        self.selected_images_label = tk.Label(self.root, text="")
        self.selected_images_label.pack()
        tk.Entry(self.root, textvariable=self.key, show="*").pack()
        tk.Button(self.root, text="Encrypt", command=self.secure_files).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def decrypt_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.image_files = []
        self.key = tk.StringVar()
        tk.Label(self.root, text="Decrypt Files", font=("Arial", 16)).pack(pady=10)
        tk.Button(self.root, text="Select Images", command=self.browse_image_files).pack()
        tk.Label(self.root, text="Currently Selected Images:").pack()
        self.selected_images_label = tk.Label(self.root, text="")
        self.selected_images_label.pack()
        tk.Entry(self.root, textvariable=self.key, show="*").pack()
        tk.Button(self.root, text="Decrypt", command=self.restore_files).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def browse_input_files(self):
        self.input_files = filedialog.askopenfilenames()
        self.update_selected_files()

    def browse_image_files(self):
        self.image_files = filedialog.askopenfilenames()
        self.update_selected_images()

    def update_selected_files(self):
        filenames = "\n".join([os.path.basename(f) for f in self.input_files])
        self.selected_files_label.config(text=filenames)

    def update_selected_images(self):
        image_names = "\n".join([os.path.basename(f) for f in self.image_files])
        self.selected_images_label.config(text=image_names)

    def secure_files(self):
        if not self.input_files or not self.image_files or not self.key.get():
            messagebox.showerror("Error", "All fields are required!")
            return
        temp_dir = os.path.join(os.getcwd(), ".temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Ensure the output folder for the embedded images
        output_dir = ensure_output_folder("embedded_output")

        try:
            tarball_file = os.path.join(temp_dir, "files.tar")
            compressed_file = os.path.join(temp_dir, "compressed.lzma")
            #encrypted_file = os.path.join(temp_dir, "encrypted.cam")
            create_tarball(self.input_files, tarball_file)
            compress_file(tarball_file, compressed_file)
            encrypted_data = encrypt_file(compressed_file, self.key.get())
            embed_in_images(self.image_files, encrypted_data, output_dir)
            messagebox.showinfo("Success", f"Files encrypted and embedded successfully in images!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            cleanup_temp_folder(temp_dir)

    def restore_files(self):
        if not self.image_files or not self.key.get():
            messagebox.showerror("Error", "All fields are required!")
            return
        temp_dir = os.path.join(os.getcwd(), ".temp")
        os.makedirs(temp_dir, exist_ok=True)

        # Ensure the output folder for restored files
        output_dir = ensure_output_folder("restored_output")

        try:
            extracted_file = os.path.join(temp_dir, "extracted.cam")
            decompressed_file = os.path.join(temp_dir, "decompressed.tar")

            # Extract combined encrypted data from images
            encrypted_data = extract_from_images(self.image_files)

            # Decrypt the extracted data
            decrypt_file(encrypted_data, self.key.get(), decompressed_file)

            # Decompress and extract files
            extract_tarball(decompressed_file, output_dir)
            messagebox.showinfo("Success", f"Data restored in {output_dir}")
        finally:
            cleanup_temp_folder(temp_dir)

        try:
            # Extract encrypted data from images
            extracted_file = os.path.join(temp_dir, "extracted.cam")
            extracted_file_decompressed = os.path.join(temp_dir, "extracted_decompressed.lzma")
            output_file = os.path.join(temp_dir, "restored_files")

            extract_from_images(self.image_files, extracted_file, 2)

            decrypt_file(extracted_file, self.key.get(), extracted_file_decompressed)
            decompress_file(extracted_file_decompressed, output_file)

            # Extract files from tarball
            extract_tarball(output_file, os.path.dirname(output_file))

            messagebox.showinfo("Success", f"Files decrypted and restored successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            cleanup_temp_folder(temp_dir)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileSecurityApp(root)
    root.mainloop()
