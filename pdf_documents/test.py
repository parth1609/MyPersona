import os
import sys
sys.path.append(os.path.abspath('.'))
from pdf_documents import extract_text_blocks, extract_images_with_ocr, extract_tables, extract_unstructured_elements, process_pdf

# Path to a sample PDF file (update this if needed)
pdf_path = os.path.join(os.getcwd(), '1page.pdf')

def test_extract_tables():
    try:
        tables = extract_tables(pdf_path)
        print('Tables:', tables)
    except Exception as e:
        print('extract_tables error:', e)

def test_extract_unstructured_elements():
    try:
        elements = extract_unstructured_elements(pdf_path)
        print('Unstructured elements:', elements)
    except Exception as e:
        print('extract_unstructured_elements error:', e)

def test_extract_images_with_ocr():
    try:
        from pdf_documents import extract_images_with_ocr
        import fitz
        doc = fitz.open(pdf_path)
        for page_number in range(len(doc)):
            page = doc[page_number]
            images = extract_images_with_ocr(page, page_number+1)
            print(f'Page {page_number+1} Images:')
            for img in images:
                print(f"  Filename: {img['filename']}")
                print(f"  OCR Text: {img['ocr_text']}")
                print(f"  BBox: {img['bbox']}")
    except Exception as e:
        print('extract_images_with_ocr error:', e)

def test_process_pdf():
    try:
        summary = process_pdf(pdf_path)
        print('PDF Summary:', summary)
    except Exception as e:
        print('process_pdf error:', e)

def main():
    print('Testing extract_tables...')
    test_extract_tables()
    print('\nTesting extract_unstructured_elements...')
    test_extract_unstructured_elements()
    print('\nTesting extract_images_with_ocr...')
    test_extract_images_with_ocr()
    print('\nTesting process_pdf...')
    test_process_pdf()

if __name__ == "__main__":
    main()