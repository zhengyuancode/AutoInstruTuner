from docx import Document  # for DOCX files
import os
import re
#使用MinerU的pdf分析工具
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

# prepare env
local_image_dir, local_md_dir = "Output/images", "Output"

def read_pdf(file_path):
    mdFileName=pdfToMd(file_path)
    mdFilePath=local_md_dir+'\\'+mdFileName
    return read_md(mdFilePath)

def read_docx(file_path):
    document = Document(file_path)
    text = "\n".join([paragraph.text for paragraph in document.paragraphs])
    print("已读入")
    return text

def read_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    print("已读入")
    return text

def read_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    print("已读入")
    return text


#文本清洗规则
def preprocess_text(text):
    # 去除多余空格和换行符
    text = re.sub(r'\s+', ' ', text).strip()
    # 可以添加更多的文本清洗逻辑
    print("第一次清洗完成")
    
    return text

def pdfToMd(file_name):
    #TODO：xml构建
    # args
    pdf_file_name = file_name  # replace with the real pdf path
    name_without_suff = pdf_file_name.split(".")[0]

    # prepare env
    image_dir = str(os.path.basename(local_image_dir))

    os.makedirs(local_image_dir, exist_ok=True)

    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(
        local_md_dir
    )

    # read bytes
    reader1 = FileBasedDataReader("")
    pdf_bytes = reader1.read(pdf_file_name)  # read the pdf content

    # proc
    ## Create Dataset Instance
    ds = PymuDocDataset(pdf_bytes)

    ## inference
    if ds.classify() == SupportedPdfParseMethod.OCR:
        infer_result = ds.apply(doc_analyze, ocr=True)

        ## pipeline
        pipe_result = infer_result.pipe_ocr_mode(image_writer)

    else:
        infer_result = ds.apply(doc_analyze, ocr=False)

        ## pipeline
        pipe_result = infer_result.pipe_txt_mode(image_writer)

    ### draw model result on each page
    infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))

    ### get model inference result
    model_inference_result = infer_result.get_infer_res()

    ### draw layout result on each page
    pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))

    ### draw spans result on each page
    pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))

    ### get markdown content
    md_content = pipe_result.get_markdown(image_dir)

    ### dump markdown
    pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
    
    mdFileName=f"{name_without_suff}.md"
    
    ### get content list content
    content_list_content = pipe_result.get_content_list(image_dir)

    ### dump content list
    pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)

    ### get middle json
    middle_json_content = pipe_result.get_middle_json()

    ### dump middle json
    pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')
    
    return mdFileName