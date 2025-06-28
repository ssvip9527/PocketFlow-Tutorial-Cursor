from pocketflow import Node, Flow, BatchNode
import os
import yaml  # 添加YAML支持
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple

# 导入工具函数
from utils.call_llm import call_llm
from utils.read_file import read_file
from utils.delete_file import delete_file
from utils.replace_file import replace_file
from utils.search_ops import grep_search
from utils.dir_ops import list_dir

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('coding_agent.log')
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger('coding_agent')

def format_history_summary(history: List[Dict[str, Any]]) -> str:
    if not history:
        return "No previous actions."
    
    history_str = "\n"
    
    for i, action in enumerate(history):
        # 所有条目的标题 - 移除时间戳
        history_str += f"Action {i+1}:\n"
        history_str += f"- Tool: {action['tool']}\n"
        history_str += f"- Reason: {action['reason']}\n"
        
        # 添加参数
        params = action.get("params", {})
        if params:
            history_str += f"- Parameters:\n"
            for k, v in params.items():
                history_str += f"  - {k}: {v}\n"
        
        # 添加详细结果信息
        result = action.get("result")
        if result:
            if isinstance(result, dict):
                success = result.get("success", False)
                history_str += f"- Result: {'Success' if success else 'Failed'}\n"
                
                # 添加工具特定的详细信息
                if action['tool'] == 'read_file' and success:
                    content = result.get("content", "")
                    # 显示完整内容而不截断
                    history_str += f"- Content: {content}\n"
                elif action['tool'] == 'grep_search' and success:
                    matches = result.get("matches", [])
                    history_str += f"- Matches: {len(matches)}\n"
                    # 显示所有匹配项而不限制为前3个
                    for j, match in enumerate(matches):
                        history_str += f"  {j+1}. {match.get('file')}:{match.get('line')}: {match.get('content')}\n"
                elif action['tool'] == 'edit_file' and success:
                    operations = result.get("operations", 0)
                    history_str += f"- Operations: {operations}\n"
                    
                    # 如果可用则包含推理
                    reasoning = result.get("reasoning", "")
                    if reasoning:
                        history_str += f"- Reasoning: {reasoning}\n"
                elif action['tool'] == 'list_dir' and success:
                    # 获取树形可视化字符串
                    tree_visualization = result.get("tree_visualization", "")
                    history_str += "- Directory structure:\n"
                    
                    # 正确处理和格式化树形可视化
                    if tree_visualization and isinstance(tree_visualization, str):
                        # 首先，确保我们正确处理任何特殊的行结束字符
                        clean_tree = tree_visualization.replace('\r\n', '\n').strip()
                        
                        if clean_tree:
                            # 为每行添加适当的缩进
                            for line in clean_tree.split('\n'):
                                # 确保行正确缩进
                                if line.strip():  # 只包含非空行
                                    history_str += f"  {line}\n"
                        else:
                            history_str += "  (No tree structure data)\n"
                    else:
                        history_str += "  (Empty or inaccessible directory)\n"
                        logger.debug(f"Tree visualization missing or invalid: {tree_visualization}")
            else:
                history_str += f"- Result: {result}\n"
        
        # 在操作之间添加分隔符
        history_str += "\n" if i < len(history) - 1 else ""
    
    return history_str

#############################################
# 主决策代理节点
#############################################
class MainDecisionAgent(Node):
    def prep(self, shared: Dict[str, Any]) -> Tuple[str, List[Dict[str, Any]]]:
        # 获取用户查询和历史
        user_query = shared.get("user_query", "")
        history = shared.get("history", [])
        
        return user_query, history
    
    def exec(self, inputs: Tuple[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        user_query, history = inputs
        logger.info(f"MainDecisionAgent: Analyzing user query: {user_query}")

        # 使用工具函数格式化历史，使用'basic'详细级别
        history_str = format_history_summary(history)
        
        # 使用YAML而不是JSON为LLM创建提示
        prompt = f"""You are a coding assistant that helps modify and navigate code. Given the following request, 
decide which tool to use from the available options.

User request: {user_query}

Here are the actions you performed:
{history_str}

Available tools:
1. read_file: Read content from a file
   - Parameters: target_file (path)
   - Example:
     tool: read_file
     reason: I need to read the main.py file to understand its structure
     params:
       target_file: main.py

2. edit_file: Make changes to a file
   - Parameters: target_file (path), instructions, code_edit
   - Code_edit_instructions:
       - The code changes with context, following these rules:
       - Use "// ... existing code ..." to represent unchanged code between edits
       - Include sufficient context around the changes to resolve ambiguity
       - Minimize repeating unchanged code
       - Never omit code without using the "// ... existing code ..." marker
       - No need to specify line numbers - the context helps locate the changes
   - Example:
     tool: edit_file
     reason: I need to add error handling to the file reading function
     params:
       target_file: utils/read_file.py
       instructions: Add try-except block around the file reading operation
       code_edit: |
            // ... existing file reading code ...
            function newEdit() {{
                // new code here
            }}
            // ... existing file reading code ...

3. delete_file: Remove a file
   - Parameters: target_file (path)
   - Example:
     tool: delete_file
     reason: The temporary file is no longer needed
     params:
       target_file: temp.txt

4. grep_search: Search for patterns in files
   - Parameters: query, case_sensitive (optional), include_pattern (optional), exclude_pattern (optional)
   - Example:
     tool: grep_search
     reason: I need to find all occurrences of 'logger' in Python files
     params:
       query: logger
       include_pattern: "*.py"
       case_sensitive: false

5. list_dir: List contents of a directory
   - Parameters: relative_workspace_path
   - Example:
     tool: list_dir
     reason: I need to see all files in the utils directory
     params:
       relative_workspace_path: utils
   - Result: Returns a tree visualization of the directory structure

6. finish: End the process and provide final response
   - No parameters required
   - Example:
     tool: finish
     reason: I have completed the requested task of finding all logger instances
     params: {{}}

Respond with a YAML object containing:
```yaml
tool: one of: read_file, edit_file, delete_file, grep_search, list_dir, finish
reason: |
  detailed explanation of why you chose this tool and what you intend to do
  if you chose finish, explain why no more actions are needed
params:
  # parameters specific to the chosen tool
```

If you believe no more actions are needed, use "finish" as the tool and explain why in the reason.
"""
        
        # Call LLM to decide action
        response = call_llm(prompt)

        # Look for YAML structure in the response
        yaml_content = ""
        if "```yaml" in response:
            yaml_blocks = response.split("```yaml")
            if len(yaml_blocks) > 1:
                yaml_content = yaml_blocks[1].split("```")[0].strip()
        elif "```yml" in response:
            yaml_blocks = response.split("```yml")
            if len(yaml_blocks) > 1:
                yaml_content = yaml_blocks[1].split("```")[0].strip()
        elif "```" in response:
            # Try to extract from generic code block
            yaml_blocks = response.split("```")
            if len(yaml_blocks) > 1:
                yaml_content = yaml_blocks[1].strip()
        else:
            # If no code blocks, try to use the entire response
            yaml_content = response.strip()
        
        if yaml_content:
            decision = yaml.safe_load(yaml_content)
            
            # Validate the required fields
            assert "tool" in decision, "Tool name is missing"
            assert "reason" in decision, "Reason is missing"
            
            # For tools other than "finish", params must be present
            if decision["tool"] != "finish":
                assert "params" in decision, "Parameters are missing"
            else:
                decision["params"] = {}
            
            return decision
        else:
            raise ValueError("No YAML object found in response")
    
    def post(self, shared: Dict[str, Any], prep_res: Any, exec_res: Dict[str, Any]) -> str:
        logger.info(f"MainDecisionAgent: Selected tool: {exec_res['tool']}")
        
        # 如果不存在则初始化历史
        if "history" not in shared:
            shared["history"] = []
        
        # 将此操作添加到历史
        shared["history"].append({
            "tool": exec_res["tool"],
            "reason": exec_res["reason"],
            "params": exec_res.get("params", {}),
            "result": None,  # 将由操作节点填充
            "timestamp": datetime.now().isoformat()
        })
        
        # 返回要采取的操作
        return exec_res["tool"]

#############################################
# 读取文件操作节点
#############################################
class ReadFileAction(Node):
    def prep(self, shared: Dict[str, Any]) -> str:
        # 从最后的历史条目获取参数
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        file_path = last_action["params"].get("target_file")
        
        if not file_path:
            raise ValueError("Missing target_file parameter")
        
        # 确保路径相对于工作目录
        working_dir = shared.get("working_dir", "")
        full_path = os.path.join(working_dir, file_path) if working_dir else file_path
        
        # 使用原因进行日志记录而不是解释
        reason = last_action.get("reason", "No reason provided")
        logger.info(f"ReadFileAction: {reason}")
        
        return full_path
    
    def exec(self, file_path: str) -> Tuple[str, bool]:
        # 调用read_file工具，它返回(content, success)的元组
        return read_file(file_path)
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Tuple[str, bool]) -> str:
        # 解包read_file()返回的元组
        content, success = exec_res
        
        # 在最后的历史条目中更新结果
        history = shared.get("history", [])
        if history:
            history[-1]["result"] = {
                "success": success,
                "content": content
            }

#############################################
# Grep搜索操作节点
#############################################
class GrepSearchAction(Node):
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        # 从最后的历史条目获取参数
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        params = last_action["params"]
        
        if "query" not in params:
            raise ValueError("Missing query parameter")
        
        # 使用原因进行日志记录而不是解释
        reason = last_action.get("reason", "No reason provided")
        logger.info(f"GrepSearchAction: {reason}")
        
        # 确保路径相对于工作目录
        working_dir = shared.get("working_dir", "")
        
        return {
            "query": params["query"],
            "case_sensitive": params.get("case_sensitive", False),
            "include_pattern": params.get("include_pattern"),
            "exclude_pattern": params.get("exclude_pattern"),
            "working_dir": working_dir
        }
    
    def exec(self, params: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        # 如果未指定则使用当前目录
        working_dir = params.pop("working_dir", "")
        
        # 调用grep_search工具，它返回(success, matches)
        return grep_search(
            query=params["query"],
            case_sensitive=params.get("case_sensitive", False),
            include_pattern=params.get("include_pattern"),
            exclude_pattern=params.get("exclude_pattern"),
            working_dir=working_dir
        )
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Tuple[bool, List[Dict[str, Any]]]) -> str:
        matches, success = exec_res
        
        # 在最后的历史条目中更新结果
        history = shared.get("history", [])
        if history:
            history[-1]["result"] = {
                "success": success,
                "matches": matches
            }

#############################################
# 列出目录操作节点
#############################################
class ListDirAction(Node):
    def prep(self, shared: Dict[str, Any]) -> str:
        # 从最后的历史条目获取参数
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        path = last_action["params"].get("relative_workspace_path", ".")
        
        # 使用原因进行日志记录而不是解释
        reason = last_action.get("reason", "No reason provided")
        logger.info(f"ListDirAction: {reason}")
        
        # 确保路径相对于工作目录
        working_dir = shared.get("working_dir", "")
        full_path = os.path.join(working_dir, path) if working_dir else path
        
        return full_path
    
    def exec(self, path: str) -> Tuple[bool, str]:        
        # 调用list_dir工具，现在返回(success, tree_str)
        success, tree_str = list_dir(path)
        
        return success, tree_str
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Tuple[bool, str]) -> str:
        success, tree_str = exec_res
        
        # 用新结构更新最后历史条目中的结果
        history = shared.get("history", [])
        if history:
            history[-1]["result"] = {
                "success": success,
                "tree_visualization": tree_str
            }

#############################################
# 删除文件操作节点
#############################################
class DeleteFileAction(Node):
    def prep(self, shared: Dict[str, Any]) -> str:
        # 从最后的历史条目获取参数
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        file_path = last_action["params"].get("target_file")
        
        if not file_path:
            raise ValueError("Missing target_file parameter")
        
        # 使用原因进行日志记录而不是解释
        reason = last_action.get("reason", "No reason provided")
        logger.info(f"DeleteFileAction: {reason}")
        
        # 确保路径相对于工作目录
        working_dir = shared.get("working_dir", "")
        full_path = os.path.join(working_dir, file_path) if working_dir else file_path
        
        return full_path
    
    def exec(self, file_path: str) -> Tuple[bool, str]:
        # 调用delete_file工具，它返回(success, message)
        return delete_file(file_path)
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Tuple[bool, str]) -> str:
        success, message = exec_res

        # 在最后的历史条目中更新结果
        history = shared.get("history", [])
        if history:
            history[-1]["result"] = {
                "success": success,
                "message": message
            }

#############################################
# 读取目标文件节点（编辑代理）
#############################################
class ReadTargetFileNode(Node):
    def prep(self, shared: Dict[str, Any]) -> str:
        # 从最后的历史条目获取参数
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        file_path = last_action["params"].get("target_file")
        
        if not file_path:
            raise ValueError("Missing target_file parameter")
        
        # 确保路径相对于工作目录
        working_dir = shared.get("working_dir", "")
        full_path = os.path.join(working_dir, file_path) if working_dir else file_path
        
        return full_path
    
    def exec(self, file_path: str) -> Tuple[str, bool]:
        # 调用read_file工具，它返回(content, success)
        return read_file(file_path)
    
    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: Tuple[str, bool]) -> str:
        content, success = exec_res
        logger.info("ReadTargetFileNode: File read completed for editing")
        
        # 在历史条目中存储文件内容
        history = shared.get("history", [])
        if history:
            history[-1]["file_content"] = content
        
#############################################
# 分析和计划更改节点
#############################################
class AnalyzeAndPlanNode(Node):
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        # 获取历史
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        file_content = last_action.get("file_content")
        instructions = last_action["params"].get("instructions")
        code_edit = last_action["params"].get("code_edit")
        
        if not file_content:
            raise ValueError("File content not found")
        if not instructions:
            raise ValueError("Missing instructions parameter")
        if not code_edit:
            raise ValueError("Missing code_edit parameter")
        
        return {
            "file_content": file_content,
            "instructions": instructions,
            "code_edit": code_edit
        }
    
    def exec(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        file_content = params["file_content"]
        instructions = params["instructions"]
        code_edit = params["code_edit"]
        
        # 文件内容作为行
        file_lines = file_content.split('\n')
        total_lines = len(file_lines)
        
        # 使用YAML而不是JSON为LLM生成提示以分析编辑
        prompt = f"""
As a code editing assistant, I need to convert the following code edit instruction 
and code edit pattern into specific edit operations (start_line, end_line, replacement).

FILE CONTENT:
{file_content}

EDIT INSTRUCTIONS: 
{instructions}

CODE EDIT PATTERN (markers like "// ... existing code ..." indicate unchanged code):
{code_edit}

Analyze the file content and the edit pattern to determine exactly where changes should be made. 
Be very careful with start and end lines. They are 1-indexed and inclusive. These will be REPLACED, not APPENDED!
If you want APPEND, just copy that line as the first line of the replacement.
Return a YAML object with your reasoning and an array of edit operations:

```yaml
reasoning: |
  First explain your thinking process about how you're interpreting the edit pattern.
  Explain how you identified where the edits should be made in the original file.
  Describe any assumptions or decisions you made when determining the edit locations. 
  You need to be very precise with the start and end lines! Reason why not 1 line before or after the start and end lines.

operations:
  - start_line: 10
    end_line: 15
    replacement: |
      def process_file(filename):
          # New implementation with better error handling
          try:
              with open(filename, 'r') as f:
                  return f.read()
          except FileNotFoundError:
              return None
              
  - start_line: 25
    end_line: 25
    replacement: |
      logger.info("File processing completed")
```

For lines that include "// ... existing code ...", do not include them in the replacement.
Instead, identify the exact lines they represent in the original file and set the line 
numbers accordingly. Start_line and end_line are 1-indexed.

If the instruction indicates content should be appended to the file, set both start_line and end_line 
to the maximum line number + 1, which will add the content at the end of the file.
"""
        
        # 调用LLM分析
        response = call_llm(prompt)

        # 在响应中查找YAML结构
        yaml_content = ""
        if "```yaml" in response:
            yaml_blocks = response.split("```yaml")
            if len(yaml_blocks) > 1:
                yaml_content = yaml_blocks[1].split("```")[0].strip()
        elif "```yml" in response:
            yaml_blocks = response.split("```yml")
            if len(yaml_blocks) > 1:
                yaml_content = yaml_blocks[1].split("```")[0].strip()
        elif "```" in response:
            # 尝试从通用代码块中提取
            yaml_blocks = response.split("```")
            if len(yaml_blocks) > 1:
                yaml_content = yaml_blocks[1].strip()
        
        if yaml_content:
            decision = yaml.safe_load(yaml_content)
            
            # 验证必需字段
            assert "reasoning" in decision, "Reasoning is missing"
            assert "operations" in decision, "Operations are missing"
            
            # 确保操作是列表
            if not isinstance(decision["operations"], list):
                raise ValueError("Operations are not a list")
            
            # 验证操作
            for op in decision["operations"]:
                assert "start_line" in op, "start_line is missing"
                assert "end_line" in op, "end_line is missing"
                assert "replacement" in op, "replacement is missing"
                assert 1 <= op["start_line"] <= total_lines, f"start_line out of range: {op['start_line']}"
                assert 1 <= op["end_line"] <= total_lines, f"end_line out of range: {op['end_line']}"
                assert op["start_line"] <= op["end_line"], f"start_line > end_line: {op['start_line']} > {op['end_line']}"
            
            return decision
        else:
            raise ValueError("No YAML object found in response")
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        # 在共享中存储推理和编辑操作
        shared["edit_reasoning"] = exec_res.get("reasoning", "")
        shared["edit_operations"] = exec_res.get("operations", [])
        


#############################################
# 应用更改批处理节点
#############################################
class ApplyChangesNode(BatchNode):
    def prep(self, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 获取编辑操作
        edit_operations = shared.get("edit_operations", [])
        if not edit_operations:
            logger.warning("No edit operations found")
            return []
        
        # 按start_line降序排序编辑操作
        # 这确保当我们从底部到顶部编辑时，行号保持有效
        sorted_ops = sorted(edit_operations, key=lambda op: op["start_line"], reverse=True)
        
        # 从历史中获取目标文件
        history = shared.get("history", [])
        if not history:
            raise ValueError("No history found")
        
        last_action = history[-1]
        target_file = last_action["params"].get("target_file")
        
        if not target_file:
            raise ValueError("Missing target_file parameter")
        
        # 确保路径相对于工作目录
        working_dir = shared.get("working_dir", "")
        full_path = os.path.join(working_dir, target_file) if working_dir else target_file
        
        # 将文件路径附加到每个操作
        for op in sorted_ops:
            op["target_file"] = full_path
        
        return sorted_ops
    
    def exec(self, op: Dict[str, Any]) -> Tuple[bool, str]:
        # 调用replace_file工具，它返回(success, message)
        return replace_file(
            target_file=op["target_file"],
            start_line=op["start_line"],
            end_line=op["end_line"],
            content=op["replacement"]
        )
    
    def post(self, shared: Dict[str, Any], prep_res: List[Dict[str, Any]], exec_res_list: List[Tuple[bool, str]]) -> str:
        # 检查所有操作是否成功
        all_successful = all(success for success, _ in exec_res_list)
        
        # 为历史格式化结果
        result_details = [
            {"success": success, "message": message} 
            for success, message in exec_res_list
        ]
        
        # 在历史中更新编辑结果
        history = shared.get("history", [])
        if history:
            history[-1]["result"] = {
                "success": all_successful,
                "operations": len(exec_res_list),
                "details": result_details,
                "reasoning": shared.get("edit_reasoning", "")
            }
        
        # 处理完成后清除编辑操作和推理
        shared.pop("edit_operations", None)
        shared.pop("edit_reasoning", None)
        


#############################################
# 格式化响应节点
#############################################
class FormatResponseNode(Node):
    def prep(self, shared: Dict[str, Any]) -> List[Dict[str, Any]]:
        # 获取历史
        history = shared.get("history", [])
        
        return history
    
    def exec(self, history: List[Dict[str, Any]]) -> str:
        # 如果没有历史，返回通用消息
        if not history:
            return "No actions were performed."
        
        # 使用工具函数为LLM生成操作摘要
        actions_summary = format_history_summary(history)
        
        # 为LLM生成最终响应的提示
        prompt = f"""
You are a coding assistant. You have just performed a series of actions based on the 
user's request. Summarize what you did in a clear, helpful response.

Here are the actions you performed:
{actions_summary}

Generate a comprehensive yet concise response that explains:
1. What actions were taken
2. What was found or modified
3. Any next steps the user might want to take

IMPORTANT: 
- Focus on the outcomes and results, not the specific tools used
- Write as if you are directly speaking to the user
- When providing code examples or structured information, use YAML format enclosed in triple backticks
"""
        
        # 调用LLM生成响应
        response = call_llm(prompt)
        
        return response
    
    def post(self, shared: Dict[str, Any], prep_res: List[Dict[str, Any]], exec_res: str) -> str:
        logger.info(f"###### Final Response Generated ######\n{exec_res}\n###### End of Response ######")
        
        # 在共享中存储响应
        shared["response"] = exec_res
        
        return "done"

#############################################
# 编辑代理流程
#############################################
def create_edit_agent() -> Flow:
    # 创建节点
    read_target = ReadTargetFileNode()
    analyze_plan = AnalyzeAndPlanNode()
    apply_changes = ApplyChangesNode()
    
    # 使用默认操作连接节点（无命名操作）
    read_target >> analyze_plan
    analyze_plan >> apply_changes
    
    # 创建流程
    return Flow(start=read_target)

#############################################
# 主流程
#############################################
def create_main_flow() -> Flow:
    # 创建节点
    main_agent = MainDecisionAgent()
    read_action = ReadFileAction()
    grep_action = GrepSearchAction()
    list_dir_action = ListDirAction()
    delete_action = DeleteFileAction()
    edit_agent = create_edit_agent()
    format_response = FormatResponseNode()
    
    # 将主代理连接到操作节点
    main_agent - "read_file" >> read_action
    main_agent - "grep_search" >> grep_action
    main_agent - "list_dir" >> list_dir_action
    main_agent - "delete_file" >> delete_action
    main_agent - "edit_file" >> edit_agent
    main_agent - "finish" >> format_response
    
    # 使用默认操作将操作节点连接回主代理
    read_action >> main_agent
    grep_action >> main_agent
    list_dir_action >> main_agent
    delete_action >> main_agent
    edit_agent >> main_agent
    
    # 创建流程
    return Flow(start=main_agent)

# 创建主流程
coding_agent_flow = create_main_flow()