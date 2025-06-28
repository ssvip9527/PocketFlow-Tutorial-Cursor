import os
from typing import Tuple
from utils.remove_file import remove_file
from utils. insert_file import insert_file

def replace_file(target_file: str, start_line: int, end_line: int, content: str) -> Tuple[str, bool]:
    """
    替换文件中指定行号之间的内容。
    
    Args:
        target_file: 要修改的文件路径
        start_line: 要替换的起始行号（从1开始）
        end_line: 要替换的结束行号（从1开始，包含）
        content: 用于替换指定行的新内容
    
    Returns:
        包含(结果消息, 成功状态)的元组
    """

    try:
        # 检查文件是否存在
        if not os.path.exists(target_file):
            return f"Error: File {target_file} does not exist", False
        
        # 验证行号
        if start_line < 1:
            return "Error: start_line must be at least 1", False
        
        if end_line < 1:
            return "Error: end_line must be at least 1", False
        
        if start_line > end_line:
            return "Error: start_line must be less than or equal to end_line", False
        
        # 首先，移除指定的行
        remove_result, remove_success = remove_file(target_file, start_line, end_line)
        
        if not remove_success:
            return f"Error during remove step: {remove_result}", False
        
        # 然后，在起始行插入新内容
        insert_result, insert_success = insert_file(target_file, content, start_line)
        
        if not insert_success:
            return f"Error during insert step: {insert_result}", False
        
        return f"Successfully replaced lines {start_line} to {end_line} in {target_file}", True
        
    except Exception as e:
        return f"Error replacing content: {str(e)}", False

if __name__ == "__main__":
    # 使用临时文件测试replace_file
    temp_file = "temp_replace_test.txt"
    
    # 创建带编号行的测试文件
    try:
        with open(temp_file, 'w') as f:
            for i in range(1, 11):
                f.write(f"This is line {i} of the test file.\n")
        print(f"Created test file with 10 lines: {temp_file}")
    except Exception as e:
        print(f"Error creating test file: {str(e)}")
        exit(1)
    
    # 显示初始内容
    with open(temp_file, 'r') as f:
        content = f.read()
    print(f"Initial file content:\n{content}")
    
    # 测试替换特定行（3-5）
    new_content = "This is the new line 3.\nThis is the new line 4.\nThis is the new line 5.\n"
    replace_result, replace_success = replace_file(temp_file, 3, 5, new_content)
    print(f"\nReplace lines 3-5 result: {replace_result}, success: {replace_success}")
    
    # 显示更新后的内容
    with open(temp_file, 'r') as f:
        content = f.read()
    print(f"Updated file content:\n{content}")
    
    # 测试用不同行数替换
    new_content = "This is the replacement text.\nIt has only two lines instead of three.\n"
    replace_result, replace_success = replace_file(temp_file, 7, 9, new_content)
    print(f"\nReplace lines 7-9 with 2 lines result: {replace_result}, success: {replace_success}")
    
    # 显示更新后的内容
    with open(temp_file, 'r') as f:
        content = f.read()
    print(f"Updated file content:\n{content}")
    
    # 清理 - 删除测试文件
    try:
        os.remove(temp_file)
        print(f"\nSuccessfully deleted {temp_file} for cleanup")
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
    
    # 示例：如何使用remove_file + insert_file追加内容
    print("\n=== APPEND EXAMPLE ===")
    
    # 创建新测试文件
    append_file_path = "append_test.txt"
    try:
        with open(append_file_path, 'w') as f:
            for i in range(1, 4):
                f.write(f"Original line {i}.\n")
        print(f"Created test file with 3 lines: {append_file_path}")
    except Exception as e:
        print(f"Error creating test file: {str(e)}")
        exit(1)
        
    # 显示初始内容
    with open(append_file_path, 'r') as f:
        content = f.read()
    print(f"Initial file content:\n{content}")
    
    # 统计文件行数以确定追加位置
    with open(append_file_path, 'r') as f:
        line_count = len(f.readlines())
    
    # 通过remove_file + insert_file追加
    # 步骤1：在文件末尾之后的位置移除不存在的行
    # 这不会删除任何内容，但为插入做准备
    remove_result, remove_success = remove_file(append_file_path, line_count + 1, line_count + 1)
    print(f"\nRemove step result: {remove_result}, success: {remove_success}")
    
    # 步骤2：在文件末尾之后插入新内容
    append_content = "This is appended line 1.\nThis is appended line 2.\n"
    insert_result, insert_success = insert_file(append_file_path, append_content, line_count + 1)
    print(f"Insert step result: {insert_result}, success: {insert_success}")
    
    # 显示追加后的内容
    with open(append_file_path, 'r') as f:
        content = f.read()
    print(f"Updated file content after append:\n{content}")
    
    # 再次追加测试
    # 首先获取新行数
    with open(append_file_path, 'r') as f:
        line_count = len(f.readlines())
    
    # 使用相同方法再追加一行
    remove_result, remove_success = remove_file(append_file_path, line_count + 1, line_count + 1)
    append_content = "This is another appended line.\n"
    insert_result, insert_success = insert_file(append_file_path, append_content, line_count + 1)
    
    # 显示最终内容
    with open(append_file_path, 'r') as f:
        content = f.read()
    print(f"\nFinal file content after second append:\n{content}")
    
    # 测试在特定位置追加而不是末尾
    # 例如，在line_count + 2位置追加（跳过一行）
    with open(append_file_path, 'r') as f:
        line_count = len(f.readlines())
    
    # 移除要替换的特定行（即使它不存在）
    remove_result, remove_success = remove_file(append_file_path, line_count + 2, line_count + 2)
    print(f"\nRemove at position {line_count + 2} result: {remove_result}, success: {remove_success}")
    
    # 在该特定位置插入内容
    # 这会自动在当前文件末尾和新内容之间添加一个空行
    append_content = "This line was inserted at line_count + 2, creating a blank line before it.\n"
    insert_result, insert_success = insert_file(append_file_path, append_content, line_count + 2)
    print(f"Insert at position {line_count + 2} result: {insert_result}, success: {insert_success}")
    
    # 显示最终内容
    with open(append_file_path, 'r') as f:
        content = f.read()
    print(f"\nFinal file content after inserting at line_count + 2:\n{content}")
    
    # 清理 - 删除测试文件
    try:
        os.remove(append_file_path)
        print(f"\nSuccessfully deleted {append_file_path} for cleanup")
    except Exception as e:
        print(f"Error deleting file: {str(e)}")