import os
import re
from typing import List, Dict, Any, Tuple, Optional

def grep_search(
    query: str,
    case_sensitive: bool = True,
    include_pattern: Optional[str] = None,
    exclude_pattern: Optional[str] = None,
    working_dir: str = ""
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    使用正则表达式在文件中搜索特定模式。
    
    Args:
        query: 要查找的正则表达式模式
        case_sensitive: 搜索是否区分大小写
        include_pattern: 要包含的文件的glob模式（如"*.py"）
        exclude_pattern: 要排除的文件的glob模式
        working_dir: 要搜索的目录（如果为空则为当前目录）
        
    Returns:
        包含(匹配项列表, 成功状态)的元组
        每个匹配项包含：
        {
            "file": 文件路径,
            "line_number": 行号（从1开始）,
            "content": 匹配的行内容
        }
    """
    results = []
    search_dir = working_dir if working_dir else "."
    
    try:
        # 编译正则表达式模式
        try:
            pattern = re.compile(query, 0 if case_sensitive else re.IGNORECASE)
        except re.error as e:
            print(f"Invalid regex pattern: {str(e)}")
            return [], False
        
        # 将glob模式转换为正则表达式用于文件匹配
        include_regexes = _glob_to_regex(include_pattern) if include_pattern else None
        exclude_regexes = _glob_to_regex(exclude_pattern) if exclude_pattern else None
        
        # 遍历目录并搜索文件
        for root, _, files in os.walk(search_dir):
            for filename in files:
                # 跳过不匹配包含模式的文件
                if include_regexes and not any(r.match(filename) for r in include_regexes):
                    continue
                
                # 跳过匹配排除模式的文件
                if exclude_regexes and any(r.match(filename) for r in exclude_regexes):
                    continue
                
                file_path = os.path.join(root, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if pattern.search(line):
                                results.append({
                                    "file": file_path,
                                    "line_number": i,
                                    "content": line.rstrip()
                                })
                                
                                # 最多限制50个结果
                                if len(results) >= 50:
                                    break
                except Exception:
                    # 跳过无法读取的文件
                    continue
                
                if len(results) >= 50:
                    break
            
            if len(results) >= 50:
                break
        
        return results, True
    
    except Exception as e:
        print(f"Search error: {str(e)}")
        return [], False

def _glob_to_regex(pattern_str: str) -> List[re.Pattern]:
    """将逗号分隔的glob模式转换为正则表达式模式。"""
    patterns = []
    
    for glob in pattern_str.split(','):
        glob = glob.strip()
        if not glob:
            continue
        
        # 将glob语法转换为正则表达式
        regex = (glob
                .replace('.', r'\.')  # 转义点
                .replace('*', r'.*')  # *变为.*
                .replace('?', r'.'))  # ?变为.
        
        try:
            patterns.append(re.compile(f"^{regex}$"))
        except re.error:
            # 跳过无效模式
            continue
    
    return patterns

if __name__ == "__main__":
    # 测试grep搜索函数
    print("Testing basic search for 'def' in Python files:")
    results, success = grep_search("def", include_pattern="*.py")
    print(f"Search success: {success}")
    print(f"Found {len(results)} matches")
    for result in results[:5]:  # 打印前5个结果
        print(f"{result['file']}:{result['line_number']}: {result['content'][:50]}...")
        
    # 用正则表达式测试CSS颜色搜索
    print("\nTesting CSS color search with regex:")
    css_query = r"background-color|background:|backgroundColor|light blue|#add8e6|rgb\(173, 216, 230\)"
    css_results, css_success = grep_search(
        query=css_query,
        case_sensitive=False,
        include_pattern="*.css,*.html,*.js,*.jsx,*.ts,*.tsx"
    )
    print(f"Search success: {css_success}")
    print(f"Found {len(css_results)} matches")
    for result in css_results[:5]:
        print(f"{result['file']}:{result['line_number']}: {result['content'][:50]}...") 