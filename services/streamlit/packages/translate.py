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
        self.batch_size = 50

    def _validate_translation(self, original_text: List[str]):
        def validator(translated_text: str):
            translated_lines = translated_text.split('\n')
            if len(translated_lines) != len(original_text):
                raise ValueError(f"翻译结果行数({len(translated_lines)})与原文行数({len(original_text)})不匹配")
        return validator

    async def translate(self, from_lang: str, to_lang: str, texts: List[str]) -> List[str]:
        if from_lang == to_lang:
            raise ValueError("源语言和目标语言不能相同")
        if not isinstance(texts, list):
            raise ValueError("texts 必须是字符串列表")
        
        sysprompt = (
            f"You are a translation expert that creates translations for different speech levels, especially in {from_lang} and {to_lang}.\n\n"
            f"Task: Provide an accurate {from_lang} to {to_lang} translation.\n"
            f"Scope: Focus on maintaining the original meaning and context.\n"
            f"Format: Provide the translation in a multi paragraph.\n"
            f"Tone: Use a formal and professional tone.\n"
            f"Key Information: Ensure all technical terms are accurately translated.\n"
            f"Note: Please keep the same line break format as the original text and return the translation line by line.\n"
            f"Important: Please do not add punctuation marks that are not in the original text.\n"
            f"Important: Be sure not to add punctuation at the end of each line\n"
            f"Note: Ensure that the {to_lang} translation does not contain any {from_lang} characters or words.\n\n"
            f"Translate the following text from {from_lang} to {to_lang}:\n"
        )

        results = []

        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            user_prompt = "\n".join(batch)

            messages = [
                {"role": "system", "content": sysprompt},
                {"role": "user", "content": user_prompt}
            ]

            translated_text = await self.openai_handler.request(
                messages=messages,
                validator_callback=self._validate_translation(batch),
                temp=0.4
            )

            results.extend(translated_text.split('\n'))

        return results
