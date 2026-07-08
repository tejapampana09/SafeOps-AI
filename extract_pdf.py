import pypdf
import sys

def extract_text(pdf_path, txt_path):
    print(f"Reading {pdf_path}...")
    reader = pypdf.PdfReader(pdf_path)
    text = ""
    for i, page in enumerate(reader.pages):
        text += f"\n--- Page {i+1} ---\n"
        text += page.extract_text() or ""
    
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Successfully extracted text to {txt_path}")

if __name__ == "__main__":
    pdf_file = "6a38ce305640d_ET_AI_Hackathon_2026_Problem_Statements.pdf"
    txt_file = "ET_AI_Hackathon_2026_Problem_Statements.txt"
    extract_text(pdf_file, txt_file)
