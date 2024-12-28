import asyncio
from typing import List
from .openai import OpenAIHandler

class TextCorrector:
    def __init__(self, openai_handler: OpenAIHandler, batch_size: int = 50, context_size: int = 8):
        self.openai_handler = openai_handler
        self.batch_size = batch_size
        self.context_size = context_size

    def _create_sysprompt(self, common_errors: List[dict]) -> str:
        error_examples = "\n".join([f"- {error['from']} => {error['to']}" for error in common_errors])
        return (
            "You are a professional speech recognition text correction assistant. "
            "Please correct the errors in the following text while maintaining the original meaning and context.\n\n"
            "Rules:\n"
            "1. Only return the corrected sentences in the format: {index}: {text}\n"
            "2. If a sentence does not need correction, do not include it in the result.\n"
            "3. Maintain the original tone, expression style and speech characteristics.\n"
            "4. Do not modify repetitions, stutters or other speech features.\n"
            "5. Only correct obvious speech recognition errors.\n"
            "6. Use context from previous sentences for better correction.\n\n"
            "Common errors to watch for:\n"
            "同音字错误：\n"
            "- 我门（我们）、在见（再见）、以经（已经）、\n"
            "- 由与（由于）、在次（再次）、必需（必须）、\n"
            "- 做用（作用）、那理（那里）、知到（知道）\n\n"
            "近音字错误：\n"
            "- 他门（他们）、因该（应该）、到低（到底）、\n"
            "- 经长（经常）、在次（再次/在此）\n\n"
            "Another errors to watch for:\n"
            f"{error_examples}\n\n"
            "Example Input:\n"
            "0: 家人们，今天给大家介绍这款超级好用的面膜\n"
            "1: 我觉得还型，用了之后皮肤真的变得又白又嫩\n\n"
            "Example Output:\n"
            "1: 我觉得还行，用了之后皮肤真的变得又白又嫩"
        )

    async def fix_text(self, sentences: List[str], common_errors: List[dict]) -> List[str]:
        if not isinstance(sentences, list):
            raise ValueError("sentences must be a list of strings")

        results = []
        sysprompt = self._create_sysprompt(common_errors)

        for i in range(0, len(sentences), self.batch_size):
            batch = sentences[i:i + self.batch_size]
            context = sentences[max(0, i - self.context_size):i]
            
            user_prompt = "\n".join([f"{idx}: {text}" for idx, text in enumerate(batch, start=i)])
            if context:
                user_prompt = f"Context:\n" + "\n".join(context) + "\n\n" + user_prompt

            messages = [
                {"role": "system", "content": sysprompt},
                {"role": "user", "content": user_prompt}
            ]

            corrected_text = await self.openai_handler.request(
                messages=messages
            )

            # Parse the corrected results
            for line in corrected_text.split('\n'):
                if ':' in line:
                    idx, text = line.split(':', 1)
                    try:
                        idx = int(idx.strip())
                        if 0 <= idx < len(sentences):
                            results.append((idx, text.strip()))
                    except ValueError:
                        continue

        # Apply corrections to original sentences
        corrected_sentences = sentences.copy()
        for idx, text in results:
            corrected_sentences[idx] = text

        return corrected_sentences


class TitleGenerator:
    def __init__(self, openai_handler: OpenAIHandler, book_name: str, author: str, min_length: int = 5, max_length: int = 10):
        self.openai_handler = openai_handler
        self.book_name = book_name
        self.author = author
        self.min_length = min_length
        self.max_length = max_length

    def _create_sysprompt(self) -> str:
        return (
            f"You are a professional title generation expert responsible for creating concise section titles for the book '{self.book_name}' by {self.author}.\n\n"
            f"Task: Generate a section title with {self.min_length}-{self.max_length} Chinese characters based on the provided text content.\n"
            f"Requirements:\n"
            f"1. The title must accurately summarize the text content\n"
            f"2. The title length must strictly be between {self.min_length}-{self.max_length} Chinese characters\n"
            f"3. The title must not contain any punctuation marks\n"
            f"4. The title should be concise and highlight key points\n"
            f"5. The title must not contain '章' or '节' etc.\n\n"
            f"Examples of good titles:\n"
            f"- 林黛玉葬花\n"
            f"- 孙悟空大闹天宫\n"
            f"- 诸葛亮草船借箭\n"
            f"- 贾宝玉初会林黛玉\n"
            f"- 武松打虎\n"
            f"- 宋江怒杀阎婆惜\n"
            f"- 刘备三顾茅庐\n"
            f"- 黛玉焚稿断痴情\n"
            f"- 宝玉挨打\n"
            f"- 凤姐弄权铁槛寺\n\n"
            f"Please generate an appropriate section title for the following content:\n"
        )

    async def generate_title(self, content: str, max_length: int = 200) -> str:
        if not isinstance(content, str):
            raise ValueError("content 必须是字符串")
        
        # 如果内容超过最大长度，进行截取并添加省略号
        if len(content) > max_length:
            content = content[:max_length] + "..."

        sysprompt = self._create_sysprompt()
        messages = [
            {"role": "system", "content": sysprompt},
            {"role": "user", "content": content}
        ]

        title = await self.openai_handler.request(
            messages=messages
        )

        # 清理标题中的标点符号和多余空格，并确保适合作为文件名
        invalid_chars = ['。', '，', '！', '？', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            title = title.replace(char, '')
        title = title.strip()
        
        if len(title) > 100:
            title = title[:100] # windows 文件名称限制 260 字符，mac 和 linux 255个字符，太长也没有可读性
        return title
