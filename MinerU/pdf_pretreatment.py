from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from googletrans import Translator
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

#检测旋转页面并处理为统一竖向页面，便于MinerU识别图表
def detect_and_rotate(input_path, output_path):
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page_num, page in enumerate(reader.pages, start=1):
        rotation = page.get("/Rotate", 0)  # 获取当前页面的旋转角度
        width = page.mediabox.width
        height = page.mediabox.height

        # 计算实际显示尺寸（考虑旋转后的宽高）
        if rotation in (90, 270):
            display_width, display_height = height, width
        else:
            display_width, display_height = width, height

        # 如果是横向页面，则旋转90度:(rotation - 90)为逆时针，(rotation + 90)为顺时针
        if display_width > display_height:
            new_rotation = (rotation - 90) % 360
            page.rotate(new_rotation - rotation)  # 调整旋转角度
            print(f"第 {page_num} 页为横向，已旋转为纵向")

        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
        
#一般方式获取pdf中的英文文本
def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text
        
def create_pdf(text, output_path):
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    text_obj = c.beginText(40, height - 40)
    text_obj.setFont("Helvetica", 12)
    
    # 处理换行
    for line in text.split('\n'):
        text_obj.textLine(line)
    
    c.drawText(text_obj)
    c.save()



if __name__ == "__main__":
    # input_file = "MinerU\\6016B(1-4).pdf"    # 输入文件名
    # output_file = "MinerU\\6016B(1-4)_h.pdf" # 输出文件名
    # detect_and_rotate(input_file, output_file)
    # print(f"处理完成！结果已保存至 {output_file}")
    input_pdf = "MinerU\\6016B(1-4)_h.pdf"
    english_text = extract_text_from_pdf(input_pdf)
    translator = Translator()
    chinese_text = translator.translate(english_text, src='en', dest='zh-cn').text
    create_pdf(chinese_text, "MinerU\\output_chinese.pdf")