import os
import logging
import pandas as pd
import pypdf
from datetime import datetime

def configure_logging():
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f'ghs_report_{time_stamp}.log'
    logging.basicConfig(filename=log_file_name, level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

configure_logging()



def read_pdf_text(pdf_path):
    try:
        with open(pdf_path, "rb") as pdf_file:
            pdf_reader = pypdf.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        logging.error(f'Error reading text from {pdf_path}: {e}')
        return None


def get_list_files(ext='pdf', dir_input=''):
    list_files = []
    ext = ext.strip('.')
    for root, dirs, files in os.walk(dir_input):
        for file in files:
            if file.endswith(f".{ext}"):
                list_files.append(os.path.join(root, file))
    list_files = [x.replace('\\', '/') for x in list_files]
    print(f'Total files: {len(list_files)}')
    logging.info(f'Total files: {len(list_files)}')
    return list_files


def main():
    dir_path = input('Enter the directory path: ')
    pdf_list = get_list_files(ext='pdf', dir_input=dir_path)

    df = pd.DataFrame(data = {'FILE_PATH': pdf_list})
    df['TEXT'] = df['FILE_PATH'].apply(read_pdf_text)
    df.to_pickle('./test_pdf.pkl', protocol=4)
    df.to_csv('./test_pdf.csv', encoding='utf-8', index=False)
    print(df)

if __name__ == "__main__":
    main()


