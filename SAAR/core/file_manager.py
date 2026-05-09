# core/file_manager.py
import os
import shutil
import subprocess
try:
    import winshell
except ImportError:
    winshell = None

class FileManager:
    def __init__(self):
        self.shortcuts = {
            "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
            "documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "music": os.path.join(os.path.expanduser("~"), "Music"),
            "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
            "videos": os.path.join(os.path.expanduser("~"), "Videos")
        }

    def resolve_path(self, text: str):
        """SmartPath: Resolves shortcuts, environment variables, and relative paths dynamically."""
        text = text.strip()
        
        # 1. Expand Environment Variables (e.g. %APPDATA%)
        text = os.path.expandvars(text)
        
        # 2. Check predefined shortcuts
        text_lower = text.lower()
        for key, path in self.shortcuts.items():
            if key in text_lower:
                return text.replace(key, path, 1) if not text_lower == key else path
                
        # 3. If it's an absolute path, return as is
        if os.path.isabs(text):
            return text
            
        # 4. Try joining with Desktop by default
        desktop_path = os.path.join(self.shortcuts["desktop"], text)
        if os.path.exists(desktop_path):
            return desktop_path
            
        return text

    def copy_file(self, source, target_folder):
        try:
            if not os.path.exists(source): return f"Error: Source file {source} not found."
            if not os.path.exists(target_folder): os.makedirs(target_folder)
            shutil.copy(source, target_folder)
            return f"Successfully copied {os.path.basename(source)} to {target_folder}"
        except Exception as e:
            return f"Copy Error: {e}"

    def move_file(self, source, target_folder):
        try:
            if not os.path.exists(source): return f"Error: Source file {source} not found."
            if not os.path.exists(target_folder): os.makedirs(target_folder)
            shutil.move(source, target_folder)
            return f"Successfully moved {os.path.basename(source)} to {target_folder}"
        except Exception as e:
            return f"Move Error: {e}"

    def shred_file(self, file_path: str):
        """Securely deletes a file by overwriting it with random data."""
        try:
            if not os.path.exists(file_path): return "File not found boss."
            size = os.path.getsize(file_path)
            with open(file_path, "ba+", buffering=0) as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(os.urandom(size))
            os.remove(file_path)
            return f"✅ File {os.path.basename(file_path)} has been shredded and is now unrecoverable."
        except Exception as e:
            return f"Shred Error: {e}"

    def zip_files(self, source_path: str):
        import zipfile
        try:
            if not os.path.exists(source_path): return "Source not found."
            output_zip = source_path + ".zip"
            if os.path.isdir(source_path):
                with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(source_path):
                        for file in files:
                            zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), os.path.join(source_path, '..')))
            else:
                with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(source_path, os.path.basename(source_path))
            return f"✅ Successfully zipped to {os.path.basename(output_zip)}"
        except Exception as e:
            return f"Zip Error: {e}"

    def unzip_file(self, zip_path: str):
        import zipfile
        try:
            if not zip_path.endswith(".zip"): return "Not a zip file boss."
            extract_path = zip_path.replace(".zip", "")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            return f"✅ Extracted to {os.path.basename(extract_path)}"
        except Exception as e:
            return f"Unzip Error: {e}"

    def set_file_hidden(self, path: str, hide: bool = True):
        try:
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            FILE_ATTRIBUTE_NORMAL = 0x80
            attrs = FILE_ATTRIBUTE_HIDDEN if hide else FILE_ATTRIBUTE_NORMAL
            ctypes.windll.kernel32.SetFileAttributesW(path, attrs)
            return f"✅ File is now {'HIDDEN' if hide else 'VISIBLE'} Sagar."
        except Exception as e:
            return f"Hide Error: {e}"

    def bulk_rename(self, directory: str, pattern: str, replacement: str):
        try:
            count = 0
            for filename in os.listdir(directory):
                if pattern in filename:
                    new_name = filename.replace(pattern, replacement)
                    os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))
                    count += 1
            return f"✅ Bulk rename complete! {count} files updated Sagar."
        except Exception as e:
            return f"Rename Error: {e}"

    def make_shortcut(self, target_path: str, shortcut_name: str):
        try:
            if not winshell: return "winshell module not found."
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, f"{shortcut_name}.lnk")
            with winshell.shortcut(shortcut_path) as shortcut:
                shortcut.path = target_path
                shortcut.description = f"Shortcut created by SAAR"
            return f"✅ Shortcut created on your desktop Sagar!"
        except Exception as e:
            return f"Shortcut Error: {e}"

    def quick_search(self, filename: str, search_dir: str = None):
        if not search_dir: search_dir = self.shortcuts["desktop"]
        found = []
        for root, dirs, files in os.walk(search_dir):
            for file in files:
                if filename.lower() in file.lower():
                    found.append(os.path.join(root, file))
                    if len(found) >= 5: break
            if len(found) >= 5: break
        return "I found these files:\n- " + "\n- ".join(found) if found else "No files found."

    def execute_delete(self, file_path: str):
        try:
            cmd = f'powershell -Command "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(\'{file_path}\', \'OnlyErrorDialogs\', \'SendToRecycleBin\')"'
            subprocess.run(cmd, shell=True)
            return f"✅ File {os.path.basename(file_path)} moved to Recycle Bin."
        except Exception as e:
            try:
                os.remove(file_path)
                return f"✅ File deleted permanently."
            except Exception as e2:
                return f"Delete Error: {e2}"

# Global instance
file_mgr = FileManager()
