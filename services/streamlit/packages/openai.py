import asyncio
import json
import aiohttp

class OpenAIHandler:
    def __init__(self, model: str, openai_url: str, openai_key: str, max_retries: int = 5, use_ollama: bool = True, retry_delay: float = 1.0):
        """
        初始化 OpenAIHandler
        
        Args:
            model: 默认模型名称
            openai_url: OpenAI API 地址
            openai_key: OpenAI API 密钥
            max_retries: 最大重试次数，默认5次
            retry_delay: 初始重试延迟(秒)，默认1秒
        """
        self.model = model
        self.openai_url = openai_url
        self.openai_key = openai_key
        self.use_ollama = use_ollama
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    def get_config(self) -> dict:
        """
        获取当前配置
        
        返回:
            dict: 包含模型、API地址和API密钥的字典
        """
        return {
            "model": self.model,
            "openai_url": self.openai_url,
            "openai_key": self.openai_key,
            "use_ollama": self.use_ollama,
        }

    async def request(self, messages: list, model: str = None, temp: float = 0.7, validator_callback=None) -> str:
        """
        异步发送请求到OpenAI API
        
        Args:
            messages: 消息列表
            model: 模型名称,默认使用初始化时设置的模型
            temp: 温度参数,控制随机性,默认0.7
            validator_callback: 可选的验证回调函数 (对响应内容进行验证)
            
        Returns:
            str: OpenAI的响应文本
            
        Raises:
            Exception: 当API调用失败或验证失败时抛出异常
        """
        url = f"{self.openai_url}/v1/chat/completions"
        model = model or self.model
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temp
        }
        
        retry_delay = self.retry_delay
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.post(url, headers=headers, json=data, timeout=60) as response:
                        result = await response.json()

                        if "error" in result:
                            raise Exception(f"OpenAI API错误: {result['error']}")

                        content = result["choices"][0]["message"]["content"]

                        if validator_callback:
                            validator_callback(content)

                        return content

                except Exception as e:
                    print(f"openai request 第 {attempt + 1} 次重试，错误信息: {str(e)}")
                    if attempt == self.max_retries - 1:  # 最后一次重试
                        raise Exception(f"请求OpenAI失败(重试{self.max_retries}次): {str(e)}")
                    await asyncio.sleep(retry_delay)

    async def request_json(self, messages: list, model: str = None, temp: float = 0.7, validator_callback=None) -> dict:
        """
        异步发送JSON模式的请求到OpenAI API
        
        Args:
            messages: 消息列表
            model: 模型名称,默认使用初始化时设置的模型
            temp: 温度参数,控制随机性,默认0.7
            validator_callback: 可选的JSON验证回调函数
            
        Returns:
            dict: OpenAI的JSON响应
            
        Raises:
            Exception: 当API调用失败或JSON验证失败时抛出异常
        """
        url = f"{self.openai_url}/v1/chat/completions"
        model = model or self.model
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temp,
            "response_format": { "type": "json_object" }
        }
        
        retry_delay = self.retry_delay
        
        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.post(url, headers=headers, json=data, timeout=60) as response:
                        result = await response.json()

                        if "error" in result:
                            raise Exception(f"OpenAI API错误: {result['error']}")

                        json_response_str = result["choices"][0]["message"]["content"]

                        try:
                            json_response = json.loads(json_response_str)

                            # 如果提供了验证回调,则进行验证
                            if validator_callback:
                                validator_callback(json_response)

                            return json_response
                        except json.JSONDecodeError as e:
                            raise Exception(f"解析 OpenAI JSON 响应失败: {str(e)}: {json_response_str}")

                except Exception as e:
                    print(f"openai json request 第 {attempt + 1} 次重试，错误信息: {str(e)}")
                    if attempt == self.max_retries - 1:  # 最后一次重试
                        raise Exception(f"请求OpenAI JSON失败(重试{self.max_retries}次): {str(e)}")
                    await asyncio.sleep(retry_delay)
