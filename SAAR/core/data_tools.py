# core/data_tools.py
import requests
import os
from datetime import datetime

try:
    import pytesseract
    from PIL import Image
    # Set default tesseract path for Windows
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from PyPDF2 import PdfReader, PdfWriter
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False

class DataTools:
    def __init__(self):
        pass

    # ================= DICTIONARY & CONVERTERS =================
    def get_dictionary_definition(self, word: str):
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            response = requests.get(url).json()
            if isinstance(response, list):
                meanings = response[0].get('meanings', [])
                if meanings:
                    definition = meanings[0]['definitions'][0]['definition']
                    return f"{word.capitalize()}: {definition}"
            return f"Couldn't find a definition for {word} boss."
        except Exception as e:
            return f"Dictionary API Error: {e}"

    def convert_currency(self, amount: float, from_curr: str, to_curr: str):
        try:
            from_curr = from_curr.upper()
            to_curr = to_curr.upper()
            url = f"https://api.exchangerate-api.com/v4/latest/{from_curr}"
            response = requests.get(url).json()
            if "rates" in response and to_curr in response["rates"]:
                rate = response["rates"][to_curr]
                result = round(amount * rate, 2)
                return f"{amount} {from_curr} is {result} {to_curr} boss."
            return f"Couldn't find exchange rates for {from_curr} to {to_curr}."
        except Exception as e:
            return f"Currency Converter Error: {e}"

    def get_synonyms(self, word: str):
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            res = requests.get(url).json()
            syns = []
            if isinstance(res, list):
                for m in res[0].get('meanings', []):
                    for d in m.get('definitions', []):
                        syns.extend(d.get('synonyms', []))
            
            if syns:
                return f"Synonyms for {word}: {', '.join(list(set(syns))[:5])} boss."
            return f"I couldn't find any synonyms for {word} boss."
        except:
            return "Thesaurus API is currently unreachable boss."

    def convert_unit(self, value: float, from_unit: str, to_unit: str):
        # Conversion to base (meters, grams, celsius)
        factors = {
            "km": 1000, "m": 1, "cm": 0.01, "mm": 0.001, "mile": 1609.34, "ft": 0.3048, "inch": 0.0254,
            "kg": 1000, "g": 1, "mg": 0.001, "lb": 453.592, "oz": 28.3495
        }
        try:
            from_unit, to_unit = from_unit.lower(), to_unit.lower()
            
            # Temperature handling
            if from_unit == "c" and to_unit == "f": return f"{value}°C is {(value * 9/5) + 32}°F boss."
            if from_unit == "f" and to_unit == "c": return f"{value}°F is {(value - 32) * 5/9}°C boss."

            if from_unit in factors and to_unit in factors:
                base_val = value * factors[from_unit]
                result = base_val / factors[to_unit]
                return f"{value} {from_unit} is {result:.4f} {to_unit} boss."
            
            return "I don't support those units yet boss. Try km, m, mile, kg, lb, etc."
        except Exception as e:
            return f"Unit conversion error: {e}"

    # ================= OCR (Find text in image) =================
    def extract_text_from_image(self, image_path: str):
        if not OCR_AVAILABLE:
            return "OCR module is unavailable. Please install Tesseract-OCR software boss."
        try:
            if not os.path.exists(image_path):
                return f"Image not found at {image_path}"
            
            text = pytesseract.image_to_string(Image.open(image_path))
            if not text.strip():
                return "No text found in that image boss."
            
            # Save extracted text
            output_path = f"C:\\Users\\asus\\Desktop\\extracted_text_{int(datetime.now().timestamp())}.txt"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            return f"Extracted {len(text.split())} words. Saved to {output_path}."
        except Exception as e:
            return f"OCR Error: {e}. Is Tesseract-OCR installed at C:\\Program Files\\Tesseract-OCR?"

    # ================= INVOICE GENERATOR =================
    def generate_invoice(self, client_name: str, amount: str, description: str):
        if not PDF_AVAILABLE:
            return "PDF module unavailable boss. Run pip install reportlab"
        
        try:
            filename = f"C:\\Users\\asus\\Desktop\\Invoice_{client_name.replace(' ', '_')}.pdf"
            c = canvas.Canvas(filename, pagesize=letter)
            
            c.setFont("Helvetica-Bold", 24)
            c.drawString(50, 750, "INVOICE")
            
            c.setFont("Helvetica", 12)
            c.drawString(50, 710, f"Date: {datetime.now().strftime('%Y-%m-%d')}")
            c.drawString(50, 690, f"Billed To: {client_name}")
            
            c.drawString(50, 640, "Description:")
            c.drawString(50, 620, description)
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 580, f"Total Amount Due: {amount}")
            
            c.save()
            return f"Invoice generated and saved to {filename} boss."
        except Exception as e:
            return f"Invoice Error: {e}"

    # ================= PDF SIGNER =================
    def sign_pdf(self, pdf_path: str, signature_text: str):
        if not PDF_AVAILABLE:
            return "PDF module unavailable boss. Run pip install reportlab PyPDF2"
        
        try:
            if not os.path.exists(pdf_path):
                return f"PDF not found at {pdf_path}"
                
            # Create a temporary PDF with just the signature
            temp_sig = "temp_signature.pdf"
            c = canvas.Canvas(temp_sig, pagesize=letter)
            c.setFont("Helvetica-Oblique", 20)
            c.drawString(100, 100, f"Signed by: {signature_text}") # Arbitrary signature location
            c.save()
            
            # Merge with original
            original = PdfReader(pdf_path)
            signature = PdfReader(temp_sig)
            writer = PdfWriter()
            
            sig_page = signature.pages[0]
            
            for i, page in enumerate(original.pages):
                if i == 0: # Sign the first page
                    page.merge_page(sig_page)
                writer.add_page(page)
                
            out_path = pdf_path.replace(".pdf", "_signed.pdf")
            with open(out_path, "wb") as f:
                writer.write(f)
                
            os.remove(temp_sig)
            return f"PDF signed and saved as {out_path} boss."
        except Exception as e:
            return f"PDF Signing Error: {e}"

# Global instance
data_tools = DataTools()
