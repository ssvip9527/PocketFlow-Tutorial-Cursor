import os
from typing import Tuple

def insert_file(target_file: str, content: str, line_number: int = None) -> Tuple[str, bool]:
    """
    向目标文件写入或插入内容。
    
    Args:
        target_file: 要修改的文件路径
        content: 要写入或插入到文件中的内容
        line_number: 插入的行号（从1开始）。如果为None，则替换整个文件。
    
    Returns:
        包含(结果消息, 成功状态)的元组
    """
    try:
        # 如果目录不存在则创建
        os.makedirs(os.path.dirname(os.path.abspath(target_file)), exist_ok=True)
        
        file_exists = os.path.exists(target_file)
        
        # 完全文件替换或新文件创建
        if line_number is None:
            if file_exists:
                os.remove(target_file)
                operation = "replaced"
            else:
                operation = "created"
                
            # 创建包含新内容的文件
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(content)
                
            return f"Successfully {operation} {target_file}", True
        
        # 在特定行插入
        else:
            if not file_exists:
                # 如果文件不存在但指定了line_number，则用空行创建它
                lines = [''] * max(0, line_number - 1)
                operation = "created and inserted into"
            else:
                # 读取现有内容
                with open(target_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                operation = "inserted into"
                
            # 确保line_number有效
            if line_number < 1:
                return "Error: Line number must be at least 1", False
                
            # 计算插入位置，从1索引转换为0索引
            position = line_number - 1
            
            # 如果位置超出末尾，用换行符填充
            while len(lines) < position:
                lines.append('\n')
                
            # 在指定位置插入内容
            if position == len(lines):
                # 在末尾添加（如果最后一行不以换行符结尾，可能需要换行符）
                if lines and not lines[-1].endswith('\n'):
                    lines[-1] += '\n'
                lines.append(content)
            else:
                # 如果存在，在插入点分割行
                lines.insert(position, content)
                
            # 写入更新后的内容
            with open(target_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            return f"Successfully {operation} {target_file} at line {line_number}", True
            
    except Exception as e:
        return f"Error inserting file: {str(e)}", False


if __name__ == "__main__":
    # 使用临时文件测试insert_file
    temp_file = "temp_insert_test.txt"
    
    # 测试创建新文件（完全替换）
    new_content = "This is a test file.\nCreated for testing purposes."
    insert_result, insert_success = insert_file(temp_file, new_content)
    print(f"Create file result: {insert_result}, success: {insert_success}")
    
    # 验证文件已创建
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            content = f.read()
        print(f"File content:\n{content}")
    else:
        print("Error: File was not created")
    
    # 测试在特定行插入
    insert_content = "This line was inserted at position 2.\n"
    insert_result, insert_success = insert_file(temp_file, insert_content, line_number=2)
    print(f"\nInsert at line 2 result: {insert_result}, success: {insert_success}")
    
    # 验证插入
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            content = f.read()
        print(f"Updated file content:\n{content}")
    else:
        print("Error: File does not exist")
    
    # 测试在末尾插入（超出当前长度）
    insert_content = "This line was inserted at the end.\n"
    insert_result, insert_success = insert_file(temp_file, insert_content, line_number=10)
    print(f"\nInsert at line 10 result: {insert_result}, success: {insert_success}")
    
    # 验证插入
    if os.path.exists(temp_file):
        with open(temp_file, 'r') as f:
            content = f.read()
        print(f"Updated file content:\n{content}")
    else:
        print("Error: File does not exist")
    
    # 清理 - 删除临时文件
    try:
        os.remove(temp_file)
        print(f"\nSuccessfully deleted {temp_file}")
    except Exception as e:
        print(f"Error deleting file: {str(e)}") 