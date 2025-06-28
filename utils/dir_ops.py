import os
from typing import List, Dict, Any, Tuple

def _build_tree_str(items: List[Dict[str, Any]], prefix: str = "", is_last: bool = True, show_all: bool = True) -> str:
    """
    辅助函数，构建目录结构的树形字符串表示。
    只显示一级目录并限制每个目录显示的文件数量。
    """
    tree_str = ""
    # 将项目分为目录和文件
    dirs = [item for item in items if item["type"] == "directory"]
    files = [item for item in items if item["type"] == "file"]
    
    # 首先处理目录
    for i, item in enumerate(dirs):
        is_last_item = i == len(dirs) == 0 and len(files) == 0
        connector = "└──" if is_last_item else "├──"
        tree_str += f"{prefix}{connector} {item['name']}/\n"
        
        # 对于目录，只显示内容数量
        if "children" in item:
            child_dirs = sum(1 for c in item["children"] if c["type"] == "directory")
            child_files = sum(1 for c in item["children"] if c["type"] == "file")
            next_prefix = prefix + ("    " if is_last_item else "│   ")
            if child_dirs > 0 or child_files > 0:
                summary = []
                if child_dirs > 0:
                    summary.append(f"{child_dirs} director{'y' if child_dirs == 1 else 'ies'}")
                if child_files > 0:
                    summary.append(f"{child_files} file{'s' if child_files != 1 else ''}")
                tree_str += f"{next_prefix}└── [{', '.join(summary)}]\n"
    
    # 然后处理文件
    if files:
        for i, item in enumerate(files[:10]):
            is_last_item = i == len(files) - 1 if (len(files) <= 10 or i == 9) else False
            connector = "└──" if is_last_item else "├──"
            size_str = f" ({item['size'] / 1024:.1f} KB)" if item.get("size", 0) > 0 else ""
            tree_str += f"{prefix}{connector} {item['name']}{size_str}\n"
            
        # 如果有超过10个文件，显示省略号
        if len(files) > 10:
            tree_str += f"{prefix}└── ... ({len(files) - 10} more files)\n"
    
    return tree_str

def list_dir(relative_workspace_path: str) -> Tuple[bool, str]:
    """
    列出目录内容（仅一级）。
    
    Args:
        relative_workspace_path: 要列出内容的路径，相对于工作区根目录
        
    Returns:
        包含(成功状态, 树形可视化字符串)的元组
    """
    def _list_dir_recursive(path: str, depth: int = 0) -> List[Dict[str, Any]]:
        items = []
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                is_dir = os.path.isdir(item_path)
                
                item_info = {
                    "name": item,
                    "path": item_path,
                    "type": "directory" if is_dir else "file"
                }
                
                if not is_dir:
                    try:
                        item_info["size"] = os.path.getsize(item_path)
                    except:
                        item_info["size"] = 0
                elif depth < 1:  # 只递归一级
                    # 递归列出目录内容
                    item_info["children"] = _list_dir_recursive(item_path, depth + 1)
                    
                items.append(item_info)
                
            # 排序：目录在前，然后文件（每组内按字母顺序）
            items.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"]))
            
        except Exception as e:
            pass
        return items

    try:
        path = os.path.normpath(relative_workspace_path)
        
        if not os.path.exists(path):
            return False, ""
            
        if not os.path.isdir(path):
            return False, ""
            
        items = _list_dir_recursive(path)
        tree_str = _build_tree_str(items)
        
        return True, tree_str
        
    except Exception as e:
        return False, ""

if __name__ == "__main__":
    # 测试list_dir函数
    success, tree_str = list_dir("..")
    print(f"Directory listing success: {success}")
    
    # 打印树形可视化
    print("\nDirectory Tree:")
    print(tree_str) 