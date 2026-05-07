# core/dev_tools.py
import os
import subprocess
import sqlite3

class DevTools:
    def __init__(self):
        # Default project path for git operations
        self.project_path = r"C:\Users\asus\OneDrive\Desktop\personal_ai"

    def set_project_path(self, path: str):
        if os.path.exists(path):
            self.project_path = path
            return f"Project path updated to {path} boss."
        return "That path does not exist boss."

    # ================= GIT SUITE =================
    def git_status(self):
        try:
            result = subprocess.run(["git", "status"], cwd=self.project_path, capture_output=True, text=True)
            if "not a git repository" in result.stderr.lower():
                return "This folder is not a Git repository boss."
            # Summarize the status to be concise
            if "nothing to commit, working tree clean" in result.stdout:
                return "Working tree is clean boss. Nothing to commit."
            return f"Git Status summary: You have uncommitted changes. Run 'git status' in terminal for full details."
        except Exception as e:
            return f"Git error: {e}"

    def git_commit_push(self, message: str = "Auto-commit by SAAR"):
        try:
            # Add all
            subprocess.run(["git", "add", "."], cwd=self.project_path, check=True)
            # Commit
            commit_res = subprocess.run(["git", "commit", "-m", message], cwd=self.project_path, capture_output=True, text=True)
            if "nothing to commit" in commit_res.stdout:
                return "Nothing to commit boss. Your code is already up to date."
            
            # Push
            push_res = subprocess.run(["git", "push"], cwd=self.project_path, capture_output=True, text=True)
            return f"Code committed and pushed successfully boss! Message: '{message}'"
        except subprocess.CalledProcessError as e:
            return f"Failed to commit/push boss. Make sure your remote is set up. Error: {e}"
        except Exception as e:
            return f"Git error: {e}"

    def git_branch(self, branch_name: str):
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.project_path, check=True)
            return f"Switched to a new branch: {branch_name} boss."
        except subprocess.CalledProcessError:
            try:
                subprocess.run(["git", "checkout", branch_name], cwd=self.project_path, check=True)
                return f"Switched to existing branch: {branch_name} boss."
            except Exception as e:
                return f"Failed to switch branch: {e}"

    # ================= DOCKER HELPER =================
    def docker_ps(self):
        try:
            result = subprocess.run(["docker", "ps", "--format", "{{.Names}} ({{.Status}})"], capture_output=True, text=True)
            if not result.stdout.strip():
                return "No Docker containers are currently running boss."
            return f"Running containers:\n{result.stdout.strip()}"
        except FileNotFoundError:
            return "Docker is not installed or not running boss."

    def docker_action(self, action: str, container_name: str):
        try:
            if action not in ["start", "stop", "rm", "restart"]:
                return "Invalid Docker action boss."
            subprocess.run(["docker", action, container_name], check=True)
            return f"Docker container {container_name} {action}ed successfully boss."
        except subprocess.CalledProcessError:
            return f"Failed to {action} container {container_name} boss."
        except FileNotFoundError:
            return "Docker is not installed boss."

    # ================= DB HELPER =================
    def execute_sqlite_query(self, db_path: str, query: str):
        if not os.path.exists(db_path):
            return "Database file not found boss."
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                conn.close()
                return f"Query returned {len(rows)} rows. Sample: {rows[:3]}"
            else:
                conn.commit()
                conn.close()
                return "Query executed successfully boss."
        except Exception as e:
            return f"Database error: {e}"

    # ================= API TESTER =================
    def test_api(self, url: str, method: str = "GET", data: dict = None):
        import requests
        try:
            method = method.upper()
            if method == "GET":
                res = requests.get(url, timeout=10)
            elif method == "POST":
                res = requests.post(url, json=data, timeout=10)
            else:
                return "Unsupported method boss."
            
            return f"API Response ({res.status_code}): {res.text[:200]}..."
        except Exception as e:
            return f"API Test Error: {e}"

    # ================= MOBILE VIEW =================
    def open_mobile_view(self, url: str):
        try:
            # Launch Chrome in mobile emulation mode
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if not os.path.exists(chrome_path):
                return "Chrome not found boss."
            
            # Use specific window size for iPhone 12/13 style
            cmd = f'"{chrome_path}" --window-size=390,844 --user-agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1" {url}'
            subprocess.Popen(cmd, shell=True)
            return f"Opening {url} in Mobile Emulation mode boss."
        except Exception as e:
            return f"Mobile View Error: {e}"

# Global instance
dev_tools = DevTools()
