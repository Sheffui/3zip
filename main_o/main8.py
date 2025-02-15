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

    block_size = 16
    padding_length = block_size - (len(data) % block_size)
    data += bytes([padding_length] * padding_length)

    iv = secrets.token_bytes(block_size)
    cipher = camellia.CamelliaCipher(key.encode().ljust(32)[:32], mode=1, IV=iv)

    encrypted_data = cipher.encrypt(data)
    chunk_size = len(encrypted_data) // 2
    return iv, encrypted_data[:chunk_size], encrypted_data[chunk_size:]


def embed_in_images(image_files, encrypted_data, output_folder):
    """Embed data into multiple images."""
    iv, chunk1, chunk2 = encrypted_data

    image1 = image_files[0]
    image2 = image_files[1]

    secret_image1 = lsb.hide(image1, (iv + chunk1).hex())
    secret_image1.save(os.path.join(output_folder, os.path.basename(image1)))

    secret_image2 = lsb.hide(image2, chunk2.hex())
    secret_image2.save(os.path.join(output_folder, os.path.basename(image2)))
    print(f"Embedding data into {image1}: {len(iv + chunk1)} bytes")
    print(f"Embedding data into {image2}: {len(chunk2)} bytes")


def extract_from_images(image_files):
    """Extract and combine data from images."""
    if len(image_files) != 2:
        raise ValueError("Exactly 2 images are required for extraction.")

    try:
        # Extract data from each image
        data1 = lsb.reveal(image_files[0])
        data2 = lsb.reveal(image_files[1])

        # Debugging prints
        print(f"Data extracted from image 1: {data1[:100]}...") if data1 else print("No data in image 1")
        print(f"Data extracted from image 2: {data2[:100]}...") if data2 else print("No data in image 2")
    except Exception as e:
        raise ValueError(f"Error extracting from images: {e}")

    if data1 is None or data2 is None:
        raise ValueError("Unable to extract data from one or more images.")

    # Combine the data
    combined_data = bytes.fromhex(data1) + bytes.fromhex(data2)
    return combined_data


def decrypt_data(encrypted_data, key):
    """Decrypt combined data."""
    iv = encrypted_data[:16]
    encrypted_content = encrypted_data[16:]
    cipher = camellia.CamelliaCipher(key.encode().ljust(32)[:32], mode=1, IV=iv)

    decrypted_data = cipher.decrypt(encrypted_content)
    padding_length = decrypted_data[-1]
    return decrypted_data[:-padding_length]


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
        self._prepare_menu("Encrypt Files", self.secure_files)

    def decrypt_menu(self):
        # Clear the current UI
        for widget in self.root.winfo_children():
            widget.destroy()

        # Set up the decrypt menu UI
        self.image_files = []  # Reset image file list
        self.key = tk.StringVar()  # Input for encryption key

        tk.Label(self.root, text="Decrypt Files", font=("Arial", 16)).pack(pady=10)
        tk.Button(self.root, text="Select Images", command=self.browse_image_files).pack(pady=5)

        tk.Label(self.root, text="Currently Selected Images:").pack()
        self.selected_images_label = tk.Label(self.root, text="")
        self.selected_images_label.pack()

        tk.Label(self.root, text="Enter Key:").pack()
        tk.Entry(self.root, textvariable=self.key, show="*").pack(pady=5)

        # Single button for decryption
        tk.Button(self.root, text="Decrypt and Restore Files", command=self.restore_files).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack(pady=5)

    def _prepare_menu(self, title, command):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.input_files = []
        self.image_files = []
        self.key = tk.StringVar()

        tk.Label(self.root, text=title, font=("Arial", 16)).pack(pady=10)
        tk.Button(self.root, text="Select Files", command=self.browse_input_files).pack()
        tk.Button(self.root, text="Select Images", command=self.browse_image_files).pack()
        tk.Entry(self.root, textvariable=self.key, show="*").pack(pady=5)
        tk.Button(self.root, text="Submit", command=command).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def browse_input_files(self):
        self.input_files = filedialog.askopenfilenames()
        print(f"Selected files: {self.input_files}")

    def browse_image_files(self):
        self.image_files = filedialog.askopenfilenames()
        print(f"Selected images: {self.image_files}")

    def secure_files(self):
        if not self.input_files or not self.image_files or not self.key.get():
            messagebox.showerror("Error", "All fields are required!")
            return

        temp_dir = ".temp"
        os.makedirs(temp_dir, exist_ok=True)
        output_dir = ensure_output_folder("embedded_output")

        try:
            tarball_file = os.path.join(temp_dir, "files.tar")
            compressed_file = os.path.join(temp_dir, "compressed.lzma")
            create_tarball(self.input_files, tarball_file)
            compress_file(tarball_file, compressed_file)
            encrypted_data = encrypt_file(compressed_file, self.key.get())
            embed_in_images(self.image_files, encrypted_data, output_dir)
            messagebox.showinfo("Success", "Files encrypted and embedded successfully!")
        finally:
            cleanup_temp_folder(temp_dir)

    def restore_files(self):
        if not self.image_files or not self.key.get():
            messagebox.showerror("Error", "All fields are required!")
            return

        temp_dir = ".temp"
        os.makedirs(temp_dir, exist_ok=True)
        output_dir = ensure_output_folder("restored_output")

        try:
            encrypted_data = extract_from_images(self.image_files)
            decrypted_data = decrypt_data(encrypted_data, self.key.get())
            decompressed_file = os.path.join(temp_dir, "decompressed.tar")
            with open(decompressed_file, "wb") as f_out:
                f_out.write(decrypted_data)
            extract_tarball(decompressed_file, output_dir)
            messagebox.showinfo("Success", f"Files restored to {output_dir}!")
        finally:
            cleanup_temp_folder(temp_dir)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileSecurityApp(root)
    root.mainloop()
