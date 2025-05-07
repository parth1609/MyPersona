import os
import fitz  # PyMuPDF
import tabula
import pytesseract
from PIL import Image
from unstructured.partition.auto import partition
import io
import pandas as pd

# Ensure Tesseract is installed and pytesseract is configured if needed
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # Uncomment and set if needed

def extract_text_blocks(page):
    blocks = []
    for block in page.get_text("blocks"):
        text = block[4].strip()
        bbox = block[:4]
        if text:
            blocks.append({"text": text, "bbox": bbox})
    return blocks

def extract_images_with_ocr(page, page_number, temp_dir="temp_images"):
    images = []
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = page.parent.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_filename = f"image_p{page_number}_{img_index+1}.{image_ext}"
        image_path = os.path.join(temp_dir, image_filename)
        with open(image_path, "wb") as img_file:
            img_file.write(image_bytes)
        # OCR
        try:
            image = Image.open(io.BytesIO(image_bytes))
            ocr_text = pytesseract.image_to_string(image)
        except Exception as e:
            ocr_text = f"OCR error: {e}"
        images.append({
            "filename": image_filename,
            "ocr_text": ocr_text,
            "bbox": img[1:5]  # (x0, y0, x1, y1)
        })
    return images

def extract_tables(pdf_path):
    tables = []
    try:
        # Try Tabula first (as before)
        dfs = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True, lattice=True, stream=True)
        for df in dfs:
            if not df.empty:
                tables.append({
                    "data": df.to_dict(orient="split"),
                    "metadata": {"extraction_method": "tabula-lattice/stream"}
                })
        # Try Camelot for more robust extraction (if installed)
        try:
            import camelot
            camelot_tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')
            for i in range(camelot_tables.n):
                df = camelot_tables[i].df
                if not df.empty:
                    tables.append({
                        "data": df.to_dict(orient="split"),
                        "metadata": {"extraction_method": "camelot-lattice"}
                    })
            # Try stream flavor if lattice fails
            camelot_tables_stream = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
            for i in range(camelot_tables_stream.n):
                df = camelot_tables_stream[i].df
                if not df.empty:
                    tables.append({
                        "data": df.to_dict(orient="split"),
                        "metadata": {"extraction_method": "camelot-stream"}
                    })
        except Exception as ce:
            print(f"Camelot extraction error: {ce}")
        # Try pdfplumber for image-based or complex tables (if installed)
        try:
            import pdfplumber
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        import pandas as pd
                        df = pd.DataFrame(table)
                        if not df.empty:
                            tables.append({
                                "data": df.to_dict(orient="split"),
                                "metadata": {"extraction_method": "pdfplumber", "page": page_num+1}
                            })
        except Exception as pe:
            print(f"pdfplumber extraction error: {pe}")
    except Exception as e:
        print(f"Table extraction error: {e}")
    return tables

def extract_unstructured_elements(pdf_path):
    elements = []
    try:
        for el in partition(filename=pdf_path):
            el_type = el.category if hasattr(el, 'category') else type(el).__name__
            content = getattr(el, 'text', None) or getattr(el, 'image', None)
            page_num = getattr(el.metadata, 'page_number', None) if hasattr(el, 'metadata') else None
            elements.append({
                "type": el_type,
                "text": content,
                "page_number": page_num
            })
    except Exception as e:
        print(f"Unstructured extraction error: {e}")
    return elements

def process_pdf(pdf_path):
    print(f"Processing: {os.path.basename(pdf_path)}")
    doc = fitz.open(pdf_path)
    pdf_summary = {
        "filename": os.path.basename(pdf_path),
        "pages": []
    }
    for page_number in range(len(doc)):
        page = doc[page_number]
        text_blocks = extract_text_blocks(page)
        images = extract_images_with_ocr(page, page_number+1)
        page_summary = {
            "page_number": page_number+1,
            "text_blocks": text_blocks,
            "images": images,
            "tables": [],  # Will be filled below
            "unstructured_elements": []  # Will be filled below
        }
        pdf_summary["pages"].append(page_summary)
    # Table extraction (all pages)
    tables = extract_tables(pdf_path)
    if tables:
        for t in tables:
            # Assign to first page for simplicity, or enhance to map to correct page
            pdf_summary["pages"][0]["tables"].append(t)
    # Unstructured extraction
    unstructured_elements = extract_unstructured_elements(pdf_path)
    for el in unstructured_elements:
        page_num = el.get("page_number", 1)
        if 1 <= page_num <= len(pdf_summary["pages"]):
            pdf_summary["pages"][page_num-1]["unstructured_elements"].append(el)
        else:
            pdf_summary["pages"][0]["unstructured_elements"].append(el)
    print(f"Summary for {pdf_summary['filename']}:")
    for page in pdf_summary["pages"]:
        print(f"  Page {page['page_number']}: {len(page['text_blocks'])} text blocks, {len(page['images'])} images, {len(page['tables'])} tables, {len(page['unstructured_elements'])} unstructured elements")
    return pdf_summary

def process_pdf_directory(pdf_dir):
    for fname in os.listdir(pdf_dir):
        if fname.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_dir, fname)
            process_pdf(pdf_path)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_dir = sys.argv[1]
    else:
        pdf_dir = os.path.dirname(os.path.abspath(__file__))
    process_pdf_directory(pdf_dir)