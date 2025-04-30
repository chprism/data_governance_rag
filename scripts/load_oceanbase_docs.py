"""
将OceanBase文档加载到知识库中。
"""
import os
import glob
from app.core.vector_store import get_vector_store
from app.utils.document_processor import process_document

DOCS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "oceanbase_docs")

def main():
    """主函数"""
    if not os.path.exists(DOCS_DIR):
        print(f"文档目录不存在: {DOCS_DIR}")
        print("请先运行 python scripts/download_oceanbase_docs.py 下载文档")
        return
    
    print("开始加载OceanBase文档到知识库...")
    
    vector_store = get_vector_store()
    
    md_files = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    print(f"找到 {len(md_files)} 个文档文件")
    
    for i, file_path in enumerate(md_files):
        filename = os.path.basename(file_path)
        print(f"处理文档 ({i+1}/{len(md_files)}): {filename}")
        
        try:
            document_chunks, document_id = process_document(file_path)
            
            document_data = {
                "id": document_id,
                "filename": filename,
                "content_type": "text/markdown",
                "size": os.path.getsize(file_path),
            }
            
            vector_store.add_document(document_data, document_chunks)
            print(f"文档 {filename} 已成功添加到知识库")
            
        except Exception as e:
            print(f"处理文档 {filename} 时出错: {str(e)}")
    
    print("OceanBase文档加载完成!")

if __name__ == "__main__":
    main()
