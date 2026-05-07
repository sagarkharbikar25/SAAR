# core/code_intelligence.py
import os
import subprocess
import time

# Use deepseek-coder for debugging/analysis and qwen2.5 for writing tests
CODE_MODEL = "qwen2.5:7b"
EDIT_MODEL = "deepseek-coder:latest"

class CodeIntelligence:
    def __init__(self):
        pass

    def _run_ollama(self, model: str, prompt: str):
        try:
            result = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=180
            )
            return result.stdout.strip()
        except Exception as e:
            return f"Model error: {e}"

    def generate_unit_tests(self, file_path: str):
        if not os.path.exists(file_path):
            return f"File not found boss: {file_path}"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
            
            prompt = f"""You are SAAR, an expert software developer.
Write complete, professional unit tests for the following code.
Output ONLY the test code inside a markdown block. No explanations.

```
{code}
```"""
            print("\n🧠 SAAR is generating unit tests...")
            response = self._run_ollama(CODE_MODEL, prompt)
            
            # Extract code block
            test_code = response
            if "```" in response:
                import re
                blocks = re.findall(r"```(?:\w+)?\n(.*?)```", response, re.DOTALL)
                if blocks:
                    test_code = blocks[0]
            
            # Save the file
            dir_name = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            
            test_file_name = f"test_{name}{ext}" if ext == ".py" else f"{name}.test{ext}"
            test_file_path = os.path.join(dir_name, test_file_name)
            
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_code)
                
            return f"Unit tests generated and saved to {test_file_name} boss!"
        except Exception as e:
            return f"Failed to generate tests boss: {e}"

    def analyze_security(self, file_path: str):
        if not os.path.exists(file_path):
            return f"File not found boss: {file_path}"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
                
            prompt = f"""Analyze the following code for SECURITY vulnerabilities.
Look for SQL injections, hardcoded credentials, buffer overflows, path traversal, or bad practices.
Keep the report very concise, under 3 bullet points. Say "Code looks secure" if nothing is found.

```
{code}
```"""
            print("\n🛡️ SAAR is analyzing code security...")
            response = self._run_ollama(EDIT_MODEL, prompt)
            return f"Security Report for {os.path.basename(file_path)}:\n{response}"
        except Exception as e:
            return f"Failed to analyze security boss: {e}"

    def analyze_performance(self, file_path: str):
        if not os.path.exists(file_path):
            return f"File not found boss: {file_path}"
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()
                
            prompt = f"""Analyze the following code for PERFORMANCE.
What is the Big O time complexity? Identify bottlenecks and suggest how to make it execute faster.
Keep the report concise.

```
{code}
```"""
            print("\n⚡ SAAR is analyzing code performance...")
            response = self._run_ollama(EDIT_MODEL, prompt)
            return f"Performance Report for {os.path.basename(file_path)}:\n{response}"
        except Exception as e:
            return f"Failed to analyze performance boss: {e}"

# Global instance
code_intel = CodeIntelligence()
