import sys
import asyncio
import numpy as np
from openai import AsyncOpenAI
from load_manual import load_manual
from stats_db import StatsDB
from config import AI_TOKEN
import tiktoken

INPUT_TOKEN_PRICE = 0.15 / 1_000_000
OUTPUT_TOKEN_PRICE = 0.60 / 1_000_000
EMBEDDING_TOKEN_PRICE = 0.02 / 1_000_000
MAX_INPUT_TOKENS = 4096  # Ограничение входных токенов


class AIbot:
    def __init__(self, manual_path="data/manual.txt", db_path="data/stats.db"):
        """Инициализация бота."""
        self.client = AsyncOpenAI(api_key=AI_TOKEN)
        self.stats_db = StatsDB(db_path)
        self.manual_content = load_manual(manual_path)
        if not self.manual_content:
            print("Ошибка: Методичка не загружена.")
            sys.exit(1)

        self.context_chunks = [chunk.strip() for chunk in self.manual_content.split("\n\n") if chunk.strip()]
        self.encoding = tiktoken.encoding_for_model("gpt-4o-mini")
        self.answer_cache = {}
        self.chunk_embeddings = None

    async def initialize(self):
        """Инициализация эмбеддингов и базы данных."""
        await self.stats_db.init_db()
        self.chunk_embeddings = await self._generate_embeddings(self.context_chunks)

        total_embedding_tokens = sum(len(self.encoding.encode(chunk)) for chunk in self.context_chunks)
        embedding_cost = total_embedding_tokens * EMBEDDING_TOKEN_PRICE
        print(f"Инициализировано: {total_embedding_tokens} эмбеддингов, стоимость=${embedding_cost:.6f}")

        await self.stats_db.add_entry(total_embedding_tokens, 0, embedding_cost)

    async def _generate_embeddings(self, chunks):
        """Параллельная генерация эмбеддингов."""
        responses = await asyncio.gather(*[
            self.client.embeddings.create(model="text-embedding-3-small", input=chunk)
            for chunk in chunks
        ])
        return np.array([res.data[0].embedding for res in responses])

    async def _get_relevant_context(self, question):
        """Поиск релевантного контекста."""
        embedding_response = await self.client.embeddings.create(
            model="text-embedding-3-small", input=question
        )
        question_embedding = np.array(embedding_response.data[0].embedding)
        embedding_tokens = len(self.encoding.encode(question))

        similarities = np.dot(self.chunk_embeddings, question_embedding) / (
                np.linalg.norm(self.chunk_embeddings, axis=1) * np.linalg.norm(question_embedding)
        )
        top_indices = np.argsort(similarities)[-1:]
        relevant_chunks = [self.context_chunks[i] for i in top_indices]

        if not relevant_chunks:
            return "Контекст не найден. Попробуйте уточнить вопрос.", embedding_tokens

        return "\n".join(relevant_chunks), embedding_tokens

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass  # Убрано закрытие клиента, так как оно не требуется

    async def answer(self, question):
        """Ответ на вопрос с кэшем и учётом стоимости токенов."""
        if question in self.answer_cache:
            cached_answer, input_tokens, output_tokens, total_cost = self.answer_cache[question]
            await self.stats_db.add_entry(input_tokens, output_tokens, total_cost)
            return cached_answer

        input_tokens = len(self.encoding.encode(question))
        if input_tokens > MAX_INPUT_TOKENS:
            return "Ошибка: Вопрос слишком длинный. Попробуйте сократить."

        try:
            relevant_context, embedding_tokens = await self._get_relevant_context(question)
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": f"Отвечай на русском, используя только этот контекст:\n{relevant_context}"},
                    {"role": "user", "content": question}
                ],
                max_tokens=500,
                temperature=0.7
            )
            answer = response.choices[0].message.content.strip()
            chat_input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens

            chat_input_cost = chat_input_tokens * INPUT_TOKEN_PRICE
            embedding_cost = embedding_tokens * EMBEDDING_TOKEN_PRICE
            output_cost = output_tokens * OUTPUT_TOKEN_PRICE
            total_cost = chat_input_cost + embedding_cost + output_cost

            total_input_tokens = chat_input_tokens + embedding_tokens

            await self.stats_db.add_entry(total_input_tokens, output_tokens, total_cost)

            token_info = (
                f"\n[Токены: входные={total_input_tokens} (chat={chat_input_tokens}, emb={embedding_tokens}), "
                f"выходные={output_tokens}, стоимость=${total_cost:.6f}]")
            full_answer = answer + token_info
            self.answer_cache[question] = (full_answer, total_input_tokens, output_tokens, total_cost)
            return full_answer
        except Exception as e:
            return f"Ошибка: {e}"

    async def get_stats(self):
        """Возвращает статистику."""
        messages_answered, total_input_tokens, total_output_tokens, total_cost = await self.stats_db.get_stats()
        return (f"Статистика:\n"
                f"- Сообщений отвечено: {messages_answered}\n"
                f"- Входных токенов: {total_input_tokens}\n"
                f"- Выходных токенов: {total_output_tokens}\n"
                f"- Общая стоимость: ${total_cost:.6f}")


async def main():
    async with AIbot() as bot:
        print("Бот готов! Введите вопрос ('exit' - выход, 'stats' - статистика):")
        bot.stats_db.start_cleaning()
        while True:
            try:
                question = input("> ")
                if question.lower() == "exit":
                    print(await bot.get_stats())
                    print("Выход.")
                    break
                elif question.lower() == "stats":
                    print(await bot.get_stats())
                else:
                    answer = await bot.answer(question)
                    print(answer)
            except KeyboardInterrupt:
                print("\nВыход по Ctrl+C")
                print(await bot.get_stats())
                break
            except Exception as e:
                print(f"Ошибка: {e}")


if __name__ == "__main__":
    asyncio.run(main())
