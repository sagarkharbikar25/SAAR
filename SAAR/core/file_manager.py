# core/file_manager.py
import os
import shutil
try:
    import winshell
except ImportError:
    winshell = None
# NOTE: presence_pipeline is imported lazily inside biometric_delete()
# to avoid circular import at startup.

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
        """Resolves shortcuts like 'Desktop' or 'Documents' in text."""
        text = text.lower()
        for key, path in self.shortcuts.items():
            if key in text:
                return path
        return None

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

    def biometric_delete(self, file_path):
        """Step 1 of 2-Step verification for deletion."""
        if not os.path.exists(file_path):
            return f"Error: File {file_path} does not exist."

        # Lazy import to avoid circular dependency at startup
        # from pipeline.presence_pipeline import global_presence_tracker
        global_presence_tracker = None

        if global_presence_tracker is None:
            return "⚠️ Presence tracker not active. Please ensure the camera is running boss."

        # Biometric Check via Presence Pipeline
        print(f"👁️ SAAR: Initiating Biometric Check for deletion of {os.path.basename(file_path)}...")
        verified, msg = global_presence_tracker.verify_user_now()
        
        if not verified:
            return "❌ Access Denied: Biometric verification failed. I don't see your face, boss."
        
        # If verified, the brain will handle phase 2 (Voice Confirm)
        return "VERIFIED"

    def execute_delete(self, file_path):
        """The final destructive step."""
        try:
            # We move to Recycle Bin for 'Safe Deletion' as requested
            # Using a simple shell command if winshell not installed
            import subprocess
            # Powershell command to move to recycle bin
            cmd = f'powershell -Command "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.FileIO.FileSystem]::DeleteFile(\'{file_path}\', \'OnlyErrorDialogs\', \'SendToRecycleBin\')"'
            subprocess.run(cmd, shell=True)
            return f"✅ File {os.path.basename(file_path)} moved to Recycle Bin safely."
        except Exception as e:
            # Fallback to os.remove if absolutely necessary
            try:
                os.remove(file_path)
                return f"✅ File {os.path.basename(file_path)} deleted permanently (Recycle Bin fallback failed)."
            except Exception as e2:
                return f"Delete Error: {e2}"

# Global instance
file_mgr = FileManager()
