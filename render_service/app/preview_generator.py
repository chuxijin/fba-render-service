import fitz  # PyMuPDF
from pathlib import Path

def generate_pdf_previews(pdf_path: Path | str, output_dir: Path | str, max_pages: int = 5, dpi: int = 150) -> list[Path]:
    """
    将 PDF 的前几页截取为高质量图片，用于前端预览
    :param pdf_path: PDF 文件的绝对路径
    :param output_dir: 输出图片的存储目录
    :param max_pages: 最大截取页数
    :param dpi: 渲染分辨率，越大越清晰，文件也会越大
    :return: 截取后的图片完整路径列表
    """
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    if not pdf_path.exists():
        return []
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    doc = fitz.open(str(pdf_path))
    preview_paths = []
    
    num_to_render = min(len(doc), max_pages)
    
    zoom_x = dpi / 72.0
    zoom_y = dpi / 72.0
    mat = fitz.Matrix(zoom_x, zoom_y)
    
    # 获取 PDF 文件名（不含后缀），防止重名覆盖
    base_name = pdf_path.stem
    
    for page_num in range(num_to_render):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        output_path = output_dir / f"{base_name}_preview_{page_num + 1}.jpg"
        pix.save(str(output_path))
        preview_paths.append(output_path)
        
    doc.close()
    return preview_paths
