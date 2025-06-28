import os
from typing import Tuple, Optional

def read_file(
    target_file: str, 
    start_line_one_indexed: Optional[int] = None, 
    end_line_one_indexed_inclusive: Optional[int] = None, 
    should_read_entire_file: bool = False
) -> Tuple[str, bool]:
    """
    从文件中读取内容，支持行范围。
    在输出的每行前添加基于1的行号。
    
    Args:
        target_file: 文件路径（相对或绝对）
        start_line_one_indexed: 起始行号（基于1）。如果为None，默认读取整个文件。
        end_line_one_indexed_inclusive: 结束行号（基于1）。如果为None，默认读取整个文件。
        should_read_entire_file: 如果为True，忽略行参数并读取整个文件
    
    Returns:
        包含(带行号的文件内容, 成功状态)的元组
    """
    try:
        if not os.path.exists(target_file):
            return f"Error: File {target_file} does not exist", False
        
        # 如果只提供了target_file或任何行参数为None，则读取整个文件
        if start_line_one_indexed is None or end_line_one_indexed_inclusive is None:
            should_read_entire_file = True
        
        with open(target_file, 'r', encoding='utf-8') as f:
            if should_read_entire_file:
                lines = f.readlines()
                # 为每行添加行号
                numbered_lines = [f"{i+1}: {line}" for i, line in enumerate(lines)]
                return ''.join(numbered_lines), True
            
            # 验证行范围参数
            if start_line_one_indexed < 1:
                return "Error: start_line_one_indexed must be at least 1", False
            
            if end_line_one_indexed_inclusive < start_line_one_indexed:
                return "Error: end_line_one_indexed_inclusive must be >= start_line_one_indexed", False
            
            # 检查请求的范围是否超过250行限制
            if end_line_one_indexed_inclusive - start_line_one_indexed + 1 > 250:
                return "Error: Cannot read more than 250 lines at once", False
            
            # 读取指定的行
            lines = f.readlines()
            
            # 从1索引调整为0索引
            start_idx = start_line_one_indexed - 1
            end_idx = end_line_one_indexed_inclusive - 1
            
            # 检查请求的范围是否超出边界
            if start_idx >= len(lines):
                return f"Error: start_line_one_indexed ({start_line_one_indexed}) exceeds file length ({len(lines)})", False
            
            end_idx = min(end_idx, len(lines) - 1)
            
            # 为选定的行添加行号
            numbered_lines = [f"{i+1}: {lines[i]}" for i in range(start_idx, end_idx + 1)]
            
            return ''.join(numbered_lines), True
            
    except Exception as e:
        return f"Error reading file: {str(e)}", False

if __name__ == "__main__":
    # 创建虚拟文本文件的路径
    dummy_file = "dummy_text.txt"
    
    # 测试虚拟文件是否存在
    if not os.path.exists(dummy_file):
        print(f"Dummy file {dummy_file} not found. Please create it first.")
        exit(1)
    
    # 测试仅使用目标文件读取整个文件
    content, success = read_file(dummy_file)
    print(f"Read entire file with default parameters: success={success}")
    print(f"Content preview: {content[:150]}..." if len(content) > 150 else f"Content: {content}")
    
    # 测试显式读取整个文件
    content, success = read_file(dummy_file, should_read_entire_file=True)
    print(f"\nRead entire file explicitly: success={success}")
    print(f"Content preview: {content[:150]}..." if len(content) > 150 else f"Content: {content}")
    
    # 测试读取特定行
    content, success = read_file(dummy_file, 2, 4)
    print(f"\nRead lines 2-4: success={success}")
    print(f"Content:\n{content}")
    
    # 测试使用无效参数读取
    content, success = read_file(dummy_file, 0, 5)
    print(f"\nRead with invalid start line: success={success}")
    print(f"Message: {content}")
    
    # 测试读取不存在的文件
    content, success = read_file("non_existent_file.txt")
    print(f"\nRead non-existent file: success={success}")
    print(f"Message: {content}") 