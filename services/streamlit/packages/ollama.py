import asyncio
import aiohttp
import logging
from config import global_config

logger = logging.getLogger(__name__)


class OllamaHandler:
    def __init__(self, base_url):
        self.base_url = base_url

    async def check_and_pull_model(self, model: str):
        """
        检查并拉取指定模型
        
        Args:
            model: 要检查的模型名称
            
        Returns:
            None
            
        Raises:
            Exception: 当模型检查或拉取失败时抛出异常
        """
        # 检查模型是否存在
        async with aiohttp.ClientSession() as session:
            # 获取本地模型列表
            try:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status != 200:
                        raise Exception(f"获取模型列表失败，状态码：{response.status}")
                    
                    data = await response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    
                    logger.info(f"已有模型 {data}")
                    if model in models:
                        logger.info(f"模型 {model} 已存在")
                        return
            except Exception as e:
                raise Exception(f"检查模型失败: {str(e)}")

            # 如果模型不存在，开始拉取
            logger.info(f"开始拉取模型 {model}")
            try:
                pull_data = {"model": model, "stream": False}
                async with session.post(f"{self.base_url}/api/pull", json=pull_data) as response:
                    if response.status != 200:
                        raise Exception(f"拉取模型失败，状态码：{response.status}")
                    
                    pull_result = await response.json()
                    while pull_result.get("status") != "success":
                        logger.info(f"模型拉取状态: {pull_result.get('status')}")
                        await asyncio.sleep(3)
                        async with session.post(f"{self.base_url}/api/pull", json=pull_data) as response:
                            pull_result = await response.json()
                    
                    logger.info(f"模型 {model} 拉取成功")
                    return
            except Exception as e:
                raise Exception(f"拉取模型失败: {str(e)}")
