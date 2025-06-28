import os
from typing import Tuple

def remove_file(target_file: str, start_line: int = None, end_line: int = None) -> Tuple[str, bool]:
    """
    根据行号从文件中移除内容。
    start_line或end_line至少要指定一个。
    
    Args:
        target_file: 要修改的文件路径
        start_line: 要移除的起始行号（从1开始）
        end_line: 要移除的结束行号（从1开始，包含）
                  如果为None，则移除到文件末尾
    
    Returns:
        包含(结果消息, 成功状态)的元组
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(target_file):
            return f"Error: File {target_file} does not exist", False
        
        # 要求至少指定start_line或end_line其中一个
        if start_line is None and end_line is None:
            return "Error: At least one of start_line or end_line must be specified", False
        
        # 读取文件内容
        with open(target_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 验证行号
        if start_line is not None and start_line < 1:
            return "Error: start_line must be at least 1", False
        
        if end_line is not None and end_line < 1:
            return "Error: end_line must be at least 1", False
        
        if start_line is not None and end_line is not None and start_line > end_line:
            return "Error: start_line must be less than or equal to end_line", False
        
        # 从1索引调整为0索引
        start_idx = start_line - 1 if start_line is not None else 0
        end_idx = end_line - 1 if end_line is not None else len(lines) - 1
        
        # 如果start_line超出文件长度，不报错
        # 只返回成功，提示没有移除任何行
        if start_idx >= len(lines):
            return f"No lines removed: start_line ({start_line}) exceeds file length ({len(lines)})", True
        
        # 如果end_line超出文件长度，只移除到文件末尾
        end_idx = min(end_idx, len(lines) - 1)
        
        # 移除指定的行
        del lines[start_idx:end_idx + 1]
        
        # 将更新后的内容写回文件
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # 根据移除内容准备消息
        if start_line is None:
            message = f"Successfully removed lines 1 to {end_line} from {target_file}"
        elif end_line is None:
            message = f"Successfully removed lines {start_line} to end from {target_file}"
        else:
            message = f"Successfully removed lines {start_line} to {end_line} from {target_file}"
        
        return message, True
        
    except Exception as e:
        return f"Error removing content: {str(e)}", False


if __name__ == "__main__":
    # 使用临时文件测试remove_file
    temp_file = "temp_remove_test.txt"
    
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
    
    # 测试移除特定行（3-5）
    remove_result, remove_success = remove_file(temp_file, 3, 5)
    print(f"\nRemove lines 3-5 result: {remove_result}, success: {remove_success}")
    
    # 显示更新后的内容
    with open(temp_file, 'r') as f:
        content = f.read()
    print(f"Updated file content:\n{content}")
    
    # 测试从开头到指定行移除
    remove_result, remove_success = remove_file(temp_file, None, 2)
    print(f"\nRemove lines 1-2 result: {remove_result}, success: {remove_success}")
    
    # 显示更新后的内容
    with open(temp_file, 'r') as f:
        content = f.read()
    print(f"Updated file content:\n{content}")
    
    # 测试从指定行到末尾移除
    remove_result, remove_success = remove_file(temp_file, 3, None)
    print(f"\nRemove lines 3 to end result: {remove_result}, success: {remove_success}")
    
    # 显示更新后的内容
    with open(temp_file, 'r') as f:
        content = f.read()
    print(f"Updated file content:\n{content}")
    
    # 测试尝试删除整个文件（现在应失败）
    remove_result, remove_success = remove_file(temp_file)
    print(f"\nAttempt to delete entire file result: {remove_result}, success: {remove_success}")
    
    # 清理 - 手动删除测试文件
    try:
        os.remove(temp_file)
        print(f"\nManually deleted {temp_file} for cleanup")
    except Exception as e:
        print(f"Error deleting file: {str(e)}") 