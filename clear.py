import os
import shutil

# Empty the contents of log.json and tenants_data.json
def clear_file(file_path):
    with open(file_path, "w") as file:
        file.write("")

clear_file("./log.json")
clear_file("./tenants_data.json")

# Move all files in tenants to tenants_backup
def move_files(src_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
    
    for file_name in os.listdir(src_dir):
        src_file_path = os.path.join(src_dir, file_name)
        dest_file_path = os.path.join(dest_dir, file_name)
        
        if os.path.isfile(src_file_path):
            shutil.move(src_file_path, dest_file_path)

move_files("./tenants", "./tenants_backup")
