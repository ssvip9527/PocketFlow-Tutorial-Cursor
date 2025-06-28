import os
import argparse
import logging
from flow import coding_agent_flow

# 设置日志记录
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('coding_agent.log')
    ]
)

logger = logging.getLogger('main')

def main():
    """
    运行编码代理来帮助进行代码操作
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Coding Agent - AI-powered coding assistant')
    parser.add_argument('--query', '-q', type=str, help='User query to process', required=False)
    parser.add_argument('--working-dir', '-d', type=str, default=os.path.join(os.getcwd(), "project"), 
                        help='Working directory for file operations (default: current directory)')
    args = parser.parse_args()
    
    # 如果没有通过命令行提供查询，则询问用户
    user_query = args.query
    if not user_query:
        user_query = input("What would you like me to help you with? ")
    
    # 初始化共享内存
    shared = {
        "user_query": user_query,
        "working_dir": args.working_dir,
        "history": [],
        "response": None
    }
    
    logger.info(f"Working directory: {args.working_dir}")
    
    # 运行流程
    coding_agent_flow.run(shared)

if __name__ == "__main__":
    main()