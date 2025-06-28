from anthropic import AnthropicVertex
import os
import logging
import json
from datetime import datetime

# 配置日志记录
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log")

# 设置日志记录器
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# 简单缓存配置
cache_file = "llm_cache.json"

# 了解更多关于调用LLM的信息: https://the-pocket.github.io/PocketFlow/utility_function/llm.html
def call_llm(prompt: str, use_cache: bool = True) -> str:
    # 记录提示词
    logger.info(f"PROMPT: {prompt}")
    
    # 如果启用缓存则检查缓存
    if use_cache:
        # 从磁盘加载缓存
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                logger.warning(f"Failed to load cache, starting with empty cache")
        
        # 如果缓存中存在则返回
        if prompt in cache:
            logger.info(f"Cache hit for prompt: {prompt[:50]}...")
            return cache[prompt]
    
    # 如果不在缓存中或禁用缓存则调用LLM
    client = AnthropicVertex(
        region=os.getenv("ANTHROPIC_REGION", "us-east5"),
        project_id=os.getenv("ANTHROPIC_PROJECT_ID", "your-project-id")
    )
    response = client.messages.create(
        max_tokens=20000,
        thinking={
            "type": "enabled",
            "budget_tokens": 16000
        },
        messages=[{"role": "user", "content": prompt}],
        model="claude-3-7-sonnet@20250219"
    )
    response_text = response.content[1].text
    
    # 记录响应
    logger.info(f"RESPONSE: {response_text}")
    
    # 如果启用缓存则更新缓存
    if use_cache:
        # 重新加载缓存以避免覆盖
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                pass
        
        # 添加到缓存并保存
        cache[prompt] = response_text
        try:
            with open(cache_file, 'w') as f:
                json.dump(cache, f)
            logger.info(f"Added to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    return response_text

def clear_cache() -> None:
    """如果缓存文件存在则清除它。"""
    if os.path.exists(cache_file):
        os.remove(cache_file)
        logger.info("Cache cleared")

if __name__ == "__main__":
    test_prompt = "Hello, how are you?"
    
    # 第一次调用 - 应该调用API
    print("Making first call...")
    response1 = call_llm(test_prompt, use_cache=False)
    print(f"Response: {response1}")
    
    # 第二次调用 - 应该命中缓存
    print("\nMaking second call with same prompt...")
    response2 = call_llm(test_prompt, use_cache=True)
    print(f"Response: {response2}")
