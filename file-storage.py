# File Storage System (For Raspberry PI devices)

from flask import Flask, request, render_template, jsonify, send_from_directory, redirect
from datetime import datetime
import os
import socket
import fcntl
import struct
import psutil
import hashlib

# wlan0 is getting the IP address of the network interface.
def get_ip_address(ifname="wlan0"):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
      return socket.inet_ntoa(
              fcntl.ioctl(
              s.fileno(),
              0x8915,  # SIOCGIFADDR
              struct.pack('256s', "wlan0"[:15].encode('utf-8'))
          )[20:24]
      )
    except OSError:
      return "127.0.0.1"  # If network interface is not created, start from localhost

app = Flask(__name__)
upload_folder = os.getcwd()+'/files_storage'
CHUNK_FOLDER = os.getcwd()+'/chunks'
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(CHUNK_FOLDER, exist_ok=True)


# Index
@app.route('/')
def index():
    return render_template('index.html')


# Uploads incoming files to the server
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = request.form['filename']
    custom_name = request.form.get('custom_name')
    save_as = custom_name if custom_name else filename
    total_chunks = int(request.form['total_chunks'])
    chunk_index = int(request.form['chunk_index'])
    # Save chunk file
    chunk_path = os.path.join(CHUNK_FOLDER, f"{save_as}_part{chunk_index}")  # File fragments are named by adding numbers to the end, starting with 1.
    file.save(chunk_path)
    # Check all chunks
    uploaded_chunks = [f for f in os.listdir(CHUNK_FOLDER) if f.startswith(save_as)]
    if len(uploaded_chunks) == total_chunks:
        # Merge sequentially
        uploaded_chunks = sorted(uploaded_chunks, key=lambda x: int(x.split("_part")[-1]))
        final_path = os.path.join(upload_folder, save_as)
        with open(final_path, 'wb') as final_file:
            for part_file_name in uploaded_chunks:
                part_path = os.path.join(CHUNK_FOLDER, part_file_name)
                with open(part_path, 'rb') as part_file:
                    while True:
                        chunk = part_file.read(1024*1024)  # Read in 1MB blocks
                        if not chunk:
                            break
                        final_file.write(chunk)
                os.remove(part_path)  # delete chunk
    return jsonify({'status': 'ok'})


# Get upload files list
@app.route('/files')
def files():
    def md5sum(path, chunk_size=8192):  # get uploaded files md5sum value function
       h = hashlib.md5()
       with open(path, 'rb') as f:
          for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
       return h.hexdigest()

    files = []  # uploaded files metadata
    for fname in os.listdir(upload_folder):
        path = os.path.join(upload_folder, fname)
        stat = os.stat(path)
        files.append({
            "name": fname,  # file name
            "size": stat.st_size,  # file size (byte type)
            "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y--%H:%M:%S"),  # last modification date
            "md5": md5sum(path)  # file md5sum
        })
    return jsonify(files)


# Downloading uploaded files
@app.route('/getfile/<path:filename>')
def getfile(filename):
    return send_from_directory(upload_folder, filename, as_attachment=True)  # get selected file


# Downloading uploaded files
@app.route('/deletefile/<filename>', methods=["POST"])
def deletefile(filename):
    os.remove(upload_folder+"/"+filename)
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True, port=1033, host=get_ip_address())
