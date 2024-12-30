import asyncio
from typing import List
from .openai import OpenAIHandler


# 这是 qwen2.5 7b-q4_K_M 支持较好的语言
from_languages = [
    {"name": "中文", "code": "zh-CN"},
    {"name": "英语", "code": "en"},
    {"name": "日语", "code": "ja"},
    {"name": "法语", "code": "fr"},
    {"name": "德语", "code": "de"},
]
to_languages = from_languages[1:] + [from_languages[0]]

class OpenAITranslator:
    def __init__(self, openai_handler: OpenAIHandler):
        self.openai_handler = openai_handler
        self.batch_size = 1 # 本地模型只能每条翻译，可能输出太长，注意力不够？

    def _validate_translation(self, original_text: List[str]):
        def validator(translated_text: str):
            translated_lines = translated_text.split('\n')
            if len(translated_lines) != len(original_text):
                print("original_text", original_text)
                print("translated_lines", translated_lines)
                raise ValueError(f"翻译结果行数({len(translated_lines)})与原文行数({len(original_text)})不匹配")
        return validator

    async def translate(self, from_lang: str, to_lang: str, texts: List[str]) -> List[str]:
        if from_lang == to_lang:
            raise ValueError("源语言和目标语言不能相同")
        if not isinstance(texts, list):
            raise ValueError("texts 必须是字符串列表")
        
        sysprompt = (
            f"你是一位专业的翻译专家，擅长在不同语言之间进行翻译，特别是{from_lang}和{to_lang}之间的翻译。\n\n"
            f"任务：提供准确的{from_lang}到{to_lang}的翻译。\n"
            f"范围：专注于保持原文的含义和上下文。\n"
            f"语气：使用正式和专业的语气。\n"
            f"重要：请保持与原文相同的换行符，并逐行返回翻译结果。\n"
            f"注意：确保{to_lang}的翻译结果中不包含任何{from_lang}的字符或单词。\n\n"
        )

        results = []

        # 分批处理
        total_batches = (len(texts) + self.batch_size - 1) // self.batch_size
        for i in range(0, len(texts), self.batch_size):
            batch_num = i // self.batch_size + 1
            
            batch = texts[i:i + self.batch_size]
            # print(f"正在处理第 {batch_num}/{total_batches} 批，本批次翻译 {len(batch)} 条文本，共 {len(texts)} 行文本")
            user_prompt = "\n".join(batch)

            messages = [
                {"role": "system", "content": sysprompt},
                {"role": "user", "content": user_prompt}
            ]

            translated_text = await self.openai_handler.request(
                messages=messages,
                validator_callback=self._validate_translation(batch),
                temp=0.7
            )

            results.extend(translated_text.split('\n'))
            # print(f"第 {batch_num} 批处理完成，已处理 {min(i + self.batch_size, len(texts))} 行")

        return results
