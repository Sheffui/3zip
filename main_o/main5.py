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


def encrypt_file(input_file, key, output_file):
    """Encrypt a file using Camellia cipher with CBC mode."""
    with open(input_file, 'rb') as f_in:
        data = f_in.read()
    iv = secrets.token_bytes(16)  # Generate a random 16-byte IV
    cipher = camellia.CamelliaCipher(key.encode().ljust(32)[:32], mode=1, IV=iv)
    padding_length = 16 - (len(data) % 16)
    data += bytes([padding_length] * padding_length)
    encrypted_data = cipher.encrypt(data)
    with open(output_file, 'wb') as f_out:
        f_out.write(iv + encrypted_data)


def decrypt_file(input_file, key, output_file):
    """Decrypt a file using Camellia cipher with CBC mode."""
    with open(input_file, 'rb') as f_in:
        file_data = f_in.read()
    iv = file_data[:16]
    encrypted_data = file_data[16:]
    cipher = camellia.CamelliaCipher(key.encode().ljust(32)[:32], mode=1, IV=iv)
    decrypted_data = cipher.decrypt(encrypted_data)
    padding_length = decrypted_data[-1]
    decrypted_data = decrypted_data[:-padding_length]
    with open(output_file, 'wb') as f_out:
        f_out.write(decrypted_data)


def embed_in_images(image_files, data_file, output_folder):
    """Embed split data into multiple images."""
    with open(data_file, 'rb') as f:
        data = f.read()

    # Split data into chunks to fit into the available image files
    chunk_size = len(data) // len(image_files)
    chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

    # If there is any leftover data, append it to the last chunk
    if len(chunks) < len(image_files):
        chunks[-1] += data[len(chunks) * chunk_size:]

    for i, image_file in enumerate(image_files):
        # Get the current chunk and embed it into the image
        chunk_data = chunks[i].hex()
        output_image = os.path.join(output_folder, os.path.basename(image_file))
        secret_image = lsb.hide(image_file, chunk_data)
        secret_image.save(output_image)


def extract_from_images(image_files, output_file):
    """Extract and combine data from multiple images."""
    extracted_chunks = []
    for image_file in image_files:
        try:
            data_str = lsb.reveal(image_file)
            if data_str:
                extracted_chunks.append(bytes.fromhex(data_str))
            else:
                print(f"[Debug] No data found in image: {image_file}")
        except Exception as e:
            print(f"[Debug] Failed to extract data from {image_file}: {e}")
            continue  # Skip if extraction fails on the current image

    # If no data is extracted, notify the user
    if not extracted_chunks:
        print("[Debug] No chunks were extracted.")
        return

    # Combine the extracted chunks into the final data
    extracted_data = b''.join(extracted_chunks)

    # Write the combined data to the output file
    with open(output_file, 'wb') as f:
        f.write(extracted_data)
    print(f"[Debug] Data extracted and saved to {output_file}")


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
            encrypted_file = os.path.join(temp_dir, "encrypted.cam")
            create_tarball(self.input_files, tarball_file)
            compress_file(tarball_file, compressed_file)
            encrypt_file(compressed_file, self.key.get(), encrypted_file)
            embed_in_images(self.image_files, encrypted_file, output_dir)
            messagebox.showinfo("Success", f"Data secured in {output_dir}")
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
            extract_from_images(self.image_files, extracted_file)
            decrypt_file(extracted_file, self.key.get(), decompressed_file)
            extract_tarball(decompressed_file, output_dir)
            messagebox.showinfo("Success", f"Data restored in {output_dir}")
        finally:
            cleanup_temp_folder(temp_dir)


def main():
    root = tk.Tk()
    app = FileSecurityApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
