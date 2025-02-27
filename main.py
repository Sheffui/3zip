import os
import tarfile
import lzma
import stegano.lsb as lsb
import camellia
import secrets
import tkinter as tk
from tkinter import filedialog, messagebox, PhotoImage
from tkinter import font as tkFont


def verify_output_folder(base_name):
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

def embed_file(image_files, data_file, output_folder):
    """Embed encrypted data into multiple images."""
    with open(data_file, 'rb') as f:
        data = f.read()

    num_images = len(image_files)
    chunk_size = len(data) // num_images
    chunks = [data[i * chunk_size:(i + 1) * chunk_size] for i in range(num_images)]
    
    # Add any leftover bytes to the last chunk
    if len(data) % num_images != 0:
        chunks[-1] += data[num_images * chunk_size:]

    print(f"Total data size: {len(data)} bytes")
    for i, (chunk, image_file) in enumerate(zip(chunks, image_files)):
        print(f"Embedding chunk {i+1}/{num_images} - Size: {len(chunk)} bytes into {image_file}")

        file_name, ext = os.path.splitext(os.path.basename(image_file))
        output_image = os.path.join(output_folder, f"{file_name}.png")

        # Store chunk index to ensure correct order during extraction
        secret_message = f"{i}:{chunk.hex()}"
        secret_image = lsb.hide(image_file, secret_message)
        secret_image.save(output_image)

def extract_file(image_files, output_file):
    """Extract encrypted data from multiple images and reconstruct the original data."""
    extracted_data = {}

    for image_file in image_files:
        try:
            data_str = lsb.reveal(image_file)
            if data_str is None:
                raise ValueError("Missing or corrupted data in one of the images.")

            # Extract chunk index and data
            index, chunk_hex = data_str.split(":", 1)
            index = int(index)
            extracted_data[index] = bytes.fromhex(chunk_hex)

            print(f"Extracted chunk {index} from {image_file} - Size: {len(extracted_data[index])} bytes")

        except Exception:
            raise ValueError("Failed to extract data. Ensure all images are present and unaltered.")

    # Reassemble in correct order
    sorted_data = b"".join([extracted_data[i] for i in sorted(extracted_data.keys())])

    with open(output_file, 'wb') as f:
        f.write(sorted_data)

    print(f"Total extracted data size: {len(sorted_data)} bytes")


class ThreeZip:
    def __init__(self, root):
        self.root = root
        self.root.title("3zip")
        self.root.minsize(400, 300)

        font_path = os.path.join("assets", "JosefinSans-Bold.ttf")
        if os.path.exists(font_path):
            self.custom_font = tkFont.Font(family="JosefinSans", size=24)
            self.root.option_add("*Font", self.custom_font)
        else:
            self.custom_font = ("Arial", 24)

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            self.logo = PhotoImage(file=logo_path)
            self.root.iconphoto(True, self.logo)


        self.main_menu()
    def main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="3zip", font=self.custom_font).pack(pady=20)
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
        self.files_label = tk.Label(self.root, text="No files selected")
        self.files_label.pack()
        tk.Button(self.root, text="Select Images", command=self.browse_image_files).pack()
        self.images_label = tk.Label(self.root, text="No images selected")
        self.images_label.pack()
        tk.Entry(self.root, textvariable=self.key, show="*").pack()
        tk.Button(self.root, text="Encrypt", command=self.secure_files).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def decrypt_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.image_files = []
        self.key = tk.StringVar()
        tk.Button(self.root, text="Select Images", command=self.browse_image_files).pack()
        self.images_label = tk.Label(self.root, text="No images selected")
        self.images_label.pack()
        tk.Entry(self.root, textvariable=self.key, show="*").pack()
        tk.Button(self.root, text="Decrypt", command=self.restore_files).pack(pady=10)
        tk.Button(self.root, text="Back", command=self.main_menu).pack()

    def browse_input_files(self):
        self.input_files = filedialog.askopenfilenames()
        self.files_label.config(text=f"Selected Files: {', '.join(os.path.basename(f) for f in self.input_files)}")

    def browse_image_files(self):
        self.image_files = filedialog.askopenfilenames()
        self.images_label.config(text=f"Selected Images: {', '.join(os.path.basename(f) for f in self.image_files)}")

    def secure_files(self):
        if not self.input_files or not self.image_files or not self.key.get():
            messagebox.showerror("Error", "All fields are required!")
            return
        temp_dir = ".temp"
        os.makedirs(temp_dir, exist_ok=True)
        try:
            tarball_file = os.path.join(temp_dir, "files.tar")
            compressed_file = os.path.join(temp_dir, "compressed.lzma")
            encrypted_file = os.path.join(temp_dir, "encrypted.cam")
            create_tarball(self.input_files, tarball_file)
            compress_file(tarball_file, compressed_file)
            encrypt_file(compressed_file, self.key.get(), encrypted_file)
            output_folder = verify_output_folder("encrypted_output")
            embed_file(self.image_files, encrypted_file, output_folder)
            messagebox.showinfo("Success", f"Data secured in {output_folder}")
        finally:
            cleanup_temp_folder(temp_dir)

    def restore_files(self):
        if not self.image_files or not self.key.get():
            messagebox.showerror("Error", "All fields are required!")
            return
        temp_dir = ".temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            extracted_file = os.path.join(temp_dir, "extracted.cam")	
            decompressed_file = os.path.join(temp_dir, "decompressed.tar")
            output_dir = verify_output_folder("decrypted_output")
            extract_file(self.image_files, extracted_file)
            decrypt_file(extracted_file, self.key.get(), decompressed_file)
            extract_tarball(decompressed_file, output_dir)
            messagebox.showinfo("Success", f"Data restored in {output_dir}")
        finally:
            cleanup_temp_folder(temp_dir)

def main():
    root = tk.Tk()
    app = ThreeZip(root)
    root.mainloop()

if __name__ == "__main__":
    main()
