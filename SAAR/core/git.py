# core/git.py
import subprocess
import os

class GitAgency:
    def __init__(self, project_path):
        self.path = project_path

    def run_git(self, args):
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return f"Git Error: {e.stderr.strip()}"
        except Exception as e:
            return f"Error: {str(e)}"

    def quick_push(self, message="SAAR Auto-Sync"):
        """Performs Add, Commit, and Push in one go."""
        print(f"🚀 [Git Agency] Syncing changes for Sagar...")
        add = self.run_git(["add", "."])
        commit = self.run_git(["commit", "-m", message])
        push = self.run_git(["push"])
        
        if "Git Error" in push:
            return push
        return f"✅ Project Synced! Commit: '{message}' and Pushed to remote."

    def check_status(self):
        return self.run_git(["status", "-s"])

    def create_branch(self, branch_name):
        return self.run_git(["checkout", "-b", branch_name])

# Global instance (assuming main project path)
git_agency = GitAgency(os.path.abspath('.'))
