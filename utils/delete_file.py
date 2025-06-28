import os
from typing import Tuple

def delete_file(target_file: str) -> Tuple[str, bool]:
    """
    从文件系统中删除文件。
    
    Args:
        target_file: 要删除的文件路径
    
    Returns:
        包含(结果消息, 成功状态)的元组
    """
    try:
        if not os.path.exists(target_file):
            return f"File {target_file} does not exist", False
        
        os.remove(target_file)
        return f"Successfully deleted {target_file}", True
            
    except Exception as e:
        return f"Error deleting file: {str(e)}", False


if __name__ == "__main__":
    # 使用临时文件测试delete_file
    temp_file = "temp_delete_test.txt"
    
    # 首先创建一个测试文件
    try:
        with open(temp_file, 'w') as f:
            f.write("This is a test file for deletion testing.")
        print(f"Created test file: {temp_file}")
    except Exception as e:
        print(f"Error creating test file: {str(e)}")
        exit(1)
    
    # 测试文件是否存在
    if os.path.exists(temp_file):
        print(f"Test file exists: {temp_file}")
    else:
        print(f"Error: Test file does not exist")
        exit(1)
    
    # 测试删除文件
    delete_result, delete_success = delete_file(temp_file)
    print(f"Delete result: {delete_result}, success: {delete_success}")
    
    # 验证文件已被删除
    if not os.path.exists(temp_file):
        print("File was successfully deleted")
    else:
        print("Error: File was not deleted")
    
    # 测试删除不存在的文件
    delete_result, delete_success = delete_file("non_existent_file.txt")
    print(f"\nDelete non-existent file result: {delete_result}, success: {delete_success}") 