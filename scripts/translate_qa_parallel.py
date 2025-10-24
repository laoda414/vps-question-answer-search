"""
Parallel Translation Script using OpenRouter API
Optimized for concurrent requests to maximize throughput
"""

import json
import os
import time
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tqdm.asyncio import tqdm as async_tqdm

# Load environment variables
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "normalized_qa_pairs.json"
OUTPUT_FILE = PROJECT_ROOT / "data" / "translated_qa_pairs.json"
CACHE_FILE = PROJECT_ROOT / "data" / "translation_cache.json"

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3-235b-a22b-2507")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
BATCH_SIZE = int(os.getenv("TRANSLATION_BATCH_SIZE", "10"))

# Parallel configuration
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "20"))  # Concurrent API calls
REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "180"))  # Conservative limit


class TranslationCache:
    """Simple cache for translations to avoid re-translating"""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict[str, str]:
        """Load cache from file"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_cache(self):
        """Save cache to file"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def get(self, text: str) -> Optional[str]:
        """Get translation from cache"""
        return self.cache.get(text)

    def set(self, text: str, translation: str):
        """Set translation in cache"""
        self.cache[text] = translation


class RateLimiter:
    """Token bucket rate limiter for API requests"""

    def __init__(self, requests_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.updated_at = time.monotonic()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token, waiting if necessary"""
        async with self.lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.updated_at

                # Refill tokens based on time elapsed
                self.tokens = min(
                    self.requests_per_minute,
                    self.tokens + elapsed * (self.requests_per_minute / 60.0)
                )
                self.updated_at = now

                if self.tokens >= 1:
                    self.tokens -= 1
                    return

                # Wait for next token
                wait_time = (1 - self.tokens) * (60.0 / self.requests_per_minute)
                await asyncio.sleep(wait_time)


async def translate_batch_async(
    session: aiohttp.ClientSession,
    texts: List[str],
    cache: TranslationCache,
    rate_limiter: RateLimiter,
    semaphore: asyncio.Semaphore
) -> List[str]:
    """Translate a batch of texts using OpenRouter API (async)"""

    # Check cache first
    translations = []
    texts_to_translate = []
    text_indices = []

    for idx, text in enumerate(texts):
        cached = cache.get(text)
        if cached:
            translations.append(cached)
        else:
            translations.append(None)
            texts_to_translate.append(text)
            text_indices.append(idx)

    # If all cached, return early
    if not texts_to_translate:
        return translations

    # Prepare prompt for batch translation
    prompt = """You are a professional Portuguese to English translator specializing in informal conversations and Brazilian slang.

Translate the following Portuguese texts to English. Preserve the meaning, context, tone, and any slang or colloquialisms. Return translations as a JSON array in the same order.

Portuguese texts:
"""
    for i, text in enumerate(texts_to_translate, 1):
        prompt += f"{i}. {text}\n"

    prompt += "\nReturn ONLY a JSON array of English translations, nothing else. Example: [\"translation 1\", \"translation 2\", ...]"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("HTTP_REFERER", "https://localhost"),
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS
    }

    # Acquire rate limit token and semaphore
    await rate_limiter.acquire()

    async with semaphore:
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with session.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60) as response:
                    response.raise_for_status()
                    result = await response.json()

                # Check if response has expected structure
                if not result or 'choices' not in result or len(result['choices']) == 0:
                    raise ValueError(f"Invalid API response structure: {result}")

                content = result['choices'][0]['message']['content'].strip()

                # Parse JSON response - be more robust
                if content.startswith("```"):
                    # Extract content between code blocks
                    parts = content.split("```")
                    if len(parts) >= 2:
                        content = parts[1]
                        if content.startswith("json"):
                            content = content[4:]
                    content = content.strip()

                # Try to parse JSON
                try:
                    translated_texts = json.loads(content)
                except json.JSONDecodeError as je:
                    # Try to fix common JSON issues
                    content = content.replace('\n', ' ').replace('\r', '')
                    # Try again
                    translated_texts = json.loads(content)

                # Validate we got a list with correct number of items
                if not isinstance(translated_texts, list):
                    raise ValueError(f"Expected list, got {type(translated_texts)}")

                if len(translated_texts) != len(texts_to_translate):
                    raise ValueError(f"Expected {len(texts_to_translate)} translations, got {len(translated_texts)}")

                # Store in cache and update translations list
                for idx, translated in zip(text_indices, translated_texts):
                    cache.set(texts[idx], translated)
                    translations[idx] = translated

                return translations

            except Exception as e:
                if attempt < max_retries - 1:
                    # Retry with exponential backoff
                    wait_time = 2 ** attempt
                    print(f"\n⚠️  Error on attempt {attempt + 1}/{max_retries}: {e}")
                    print(f"   Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed - use original texts as fallback
                    print(f"\n❌ Translation failed after {max_retries} attempts: {e}")
                    print(f"   Using original text as fallback for {len(texts_to_translate)} items")
                    for idx in text_indices:
                        translations[idx] = texts[idx]
                    return translations


async def translate_all_batches(
    texts: List[str],
    cache: TranslationCache,
    desc: str = "Translating"
) -> List[str]:
    """Translate all texts in batches with parallel processing"""

    # Split into batches
    batches = [texts[i:i + BATCH_SIZE] for i in range(0, len(texts), BATCH_SIZE)]

    # Initialize rate limiter and semaphore
    rate_limiter = RateLimiter(REQUESTS_PER_MINUTE)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    # Create async HTTP session
    async with aiohttp.ClientSession() as session:
        # Create tasks for all batches
        tasks = [
            translate_batch_async(session, batch, cache, rate_limiter, semaphore)
            for batch in batches
        ]

        # Execute tasks while maintaining order using gather()
        # This ensures results[i] corresponds to batches[i]
        print(f"Processing {len(tasks)} batches for {desc}...")

        # Track progress manually since gather doesn't provide progress updates
        completed = 0
        total = len(tasks)

        # Create a wrapper to track completion
        async def track_progress(task, index):
            nonlocal completed
            result = await task
            completed += 1
            if completed % 10 == 0 or completed == total:
                print(f"  Progress: {completed}/{total} batches ({completed/total*100:.1f}%)")
            return result

        # Wrap all tasks with progress tracking
        tracked_tasks = [track_progress(task, i) for i, task in enumerate(tasks)]
        results = await asyncio.gather(*tracked_tasks)

        print(f"✅ Completed all {len(results)} batches for {desc}")

    # Flatten results back into single list
    all_translations = []
    for result in results:
        all_translations.extend(result)

    return all_translations


async def translate_qa_pairs(qa_pairs: List[Dict[str, Any]], cache: TranslationCache) -> List[Dict[str, Any]]:
    """Translate all QA pairs with parallel processing"""

    total_pairs = len(qa_pairs)
    print(f"Translating {total_pairs} QA pairs in batches of {BATCH_SIZE}...")
    print(f"Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    print(f"Rate limit: {REQUESTS_PER_MINUTE} requests/minute")
    print()

    # Collect all texts to translate
    questions = [qa['question_pt'] for qa in qa_pairs]
    answers = [qa['answer_pt'] for qa in qa_pairs]
    contexts = [qa.get('context', '') if qa.get('context', '') else "N/A" for qa in qa_pairs]

    # Translate in parallel
    print("Translating questions...")
    translated_questions = await translate_all_batches(questions, cache, "Questions")

    # Save cache periodically
    cache.save_cache()

    print("\nTranslating answers...")
    translated_answers = await translate_all_batches(answers, cache, "Answers")

    cache.save_cache()

    print("\nTranslating contexts...")
    translated_contexts = await translate_all_batches(contexts, cache, "Contexts")

    cache.save_cache()

    # Update QA pairs with translations
    for idx, qa in enumerate(qa_pairs):
        qa['question_en'] = translated_questions[idx]
        qa['answer_en'] = translated_answers[idx]
        qa['context_en'] = translated_contexts[idx] if qa.get('context', '') else ''

    return qa_pairs


async def main_async():
    """Main async function"""
    print("=" * 60)
    print("QA Pairs Translation using OpenRouter (Parallel)")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Max concurrent requests: {MAX_CONCURRENT_REQUESTS}")
    print(f"Rate limit: {REQUESTS_PER_MINUTE} requests/minute")
    print()

    # Check for API key
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not found in .env file")
        print("Please set up your .env file with the API key")
        return

    # Load normalized data
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        print("Please run 'python scripts/process_data.py' first")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    qa_pairs = data['qa_pairs']
    print(f"Loaded {len(qa_pairs)} QA pairs\n")

    # Initialize cache
    cache = TranslationCache(CACHE_FILE)
    print(f"Cache loaded with {len(cache.cache)} entries")

    # Calculate estimated time
    total_batches = len(qa_pairs) * 3 // BATCH_SIZE  # questions + answers + contexts
    estimated_time_sequential = (total_batches * 2) / 60  # 2 seconds per batch
    estimated_time_parallel = (total_batches / MAX_CONCURRENT_REQUESTS) * 2 / 60

    print(f"\nEstimated time:")
    print(f"  Sequential: ~{estimated_time_sequential:.1f} minutes")
    print(f"  Parallel: ~{estimated_time_parallel:.1f} minutes")
    print(f"  Speedup: ~{estimated_time_sequential/estimated_time_parallel:.1f}x faster")
    print(f"\nEstimated API requests: {total_batches}")
    print(f"Note: This will consume API credits. Continue? (y/n): ", end='')

    response = input().strip().lower()
    if response != 'y':
        print("Translation cancelled.")
        return

    # Translate
    start_time = time.time()
    translated_qa_pairs = await translate_qa_pairs(qa_pairs, cache)
    elapsed_time = time.time() - start_time

    # Save translated data
    output_data = {
        'metadata': {
            **data['metadata'],
            'translated_at': datetime.now().isoformat(),
            'model_used': MODEL_NAME,
            'translation_time_seconds': elapsed_time,
            'translation_mode': 'parallel',
            'max_concurrent_requests': MAX_CONCURRENT_REQUESTS
        },
        'qa_pairs': translated_qa_pairs
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Translation complete!")
    print(f"Translated data saved to: {OUTPUT_FILE}")
    print(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    print(f"Average speed: {len(qa_pairs)*3/elapsed_time:.2f} texts/second")
    print(f"Cache saved with {len(cache.cache)} entries")
    print(f"\nNext step: Run 'python scripts/init_db.py' to initialize the database")


def main():
    """Entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\nTranslation interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
