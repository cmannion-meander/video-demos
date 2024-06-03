import fitz  # PyMuPDF

def read_text_file(file_path, as_lines=False):
    """
    Reads a text file and returns its content.
    
    Parameters:
    file_path (str): The path to the text file.
    as_lines (bool): If True, returns the content as a list of lines. If False, returns the content as a single string.
    
    Returns:
    str or list: The content of the text file as a single string or a list of lines.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            if as_lines:
                return file.readlines()
            else:
                return file.read()
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")

def read_pdf(file_path):
    """
    Reads a PDF file and returns its content as a single string.
    
    Parameters:
    file_path (str): The path to the PDF file.
    
    Returns:
    str: The content of the PDF file as a single string.
    """
    try:
        pdf_document = fitz.open(file_path)
        text = ""
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
        return text
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
