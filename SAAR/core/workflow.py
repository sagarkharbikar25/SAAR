# core/workflow.py
import os
import json

WORKFLOW_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "workflows.json"
)

class WorkflowEngine:
    def __init__(self):
        self.workflows = self._load()

    def _load(self):
        if not os.path.exists(WORKFLOW_FILE):
            defaults = {
                "work mode": [
                    "set volume to 40",
                    "open vscode",
                    "open chrome"
                ],
                "relax mode": [
                    "set volume to 80",
                    "open spotify",
                    "play music"
                ]
            }
            self._save(defaults)
            return defaults
        with open(WORKFLOW_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}

    def _save(self, data):
        with open(WORKFLOW_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def get_workflow(self, text: str):
        text = text.lower()
        for name, commands in self.workflows.items():
            if name in text:
                return name, commands
        return None, None

workflow_engine = WorkflowEngine()
