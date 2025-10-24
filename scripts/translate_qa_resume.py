"""
Resume-capable Translation Script using OpenRouter API
Only translates missing or failed translations when re-run
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
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "20"))
REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "180"))


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


def load_existing_translations() -> Optional[Dict[str, Any]]:
    """Load existing translations if available"""
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load existing translations: {e}")
    return None


def needs_translation(qa_pair: Dict[str, Any]) -> bool:
    """Check if a QA pair needs translation"""
    # Check if English translations are missing or same as Portuguese (failed translation)
    q_pt = qa_pair.get('question_pt', '')
    q_en = qa_pair.get('question_en', '')
    a_pt = qa_pair.get('answer_pt', '')
    a_en = qa_pair.get('answer_en', '')

    # Missing translation
    if not q_en or not a_en:
        return True

    # Failed translation (English same as Portuguese)
    if q_en == q_pt or a_en == a_pt:
        return True

    # Very short translation (likely failed)
    if len(q_en) < 3 or len(a_en) < 3:
        return True

    return False


def analyze_translation_status(qa_pairs: List[Dict[str, Any]]) -> Dict[str, int]:
    """Analyze which QA pairs need translation"""
    status = {
        'total': len(qa_pairs),
        'needs_translation': 0,
        'already_translated': 0,
        'missing_question': 0,
        'missing_answer': 0,
        'failed_translation': 0
    }

    for qa in qa_pairs:
        if needs_translation(qa):
            status['needs_translation'] += 1

            # Categorize the issue
            if not qa.get('question_en'):
                status['missing_question'] += 1
            if not qa.get('answer_en'):
                status['missing_answer'] += 1
            if qa.get('question_en') == qa.get('question_pt') or qa.get('answer_en') == qa.get('answer_pt'):
                status['failed_translation'] += 1
        else:
            status['already_translated'] += 1

    return status


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
        "messages": [{"role": "user", "content": prompt}],
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
                    raise ValueError(f"Invalid API response structure")

                content = result['choices'][0]['message']['content'].strip()

                # Parse JSON response - be more robust
                if content.startswith("```"):
                    parts = content.split("```")
                    if len(parts) >= 2:
                        content = parts[1]
                        if content.startswith("json"):
                            content = content[4:]
                    content = content.strip()

                # Try to parse JSON
                try:
                    translated_texts = json.loads(content)
                except json.JSONDecodeError:
                    content = content.replace('\n', ' ').replace('\r', '')
                    translated_texts = json.loads(content)

                # Validate
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
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    print(f"\n❌ Batch failed after {max_retries} attempts, using original text")
                    for idx in text_indices:
                        translations[idx] = texts[idx]
                    return translations


async def translate_missing_only(
    qa_pairs: List[Dict[str, Any]],
    cache: TranslationCache
) -> List[Dict[str, Any]]:
    """Translate only QA pairs that need translation"""

    # Identify which pairs need translation
    pairs_to_translate = []
    pair_indices = []

    for idx, qa in enumerate(qa_pairs):
        if needs_translation(qa):
            pairs_to_translate.append(qa)
            pair_indices.append(idx)

    if not pairs_to_translate:
        print("✅ All QA pairs already translated!")
        return qa_pairs

    print(f"\nTranslating {len(pairs_to_translate)} QA pairs that need translation...")
    print(f"(Skipping {len(qa_pairs) - len(pairs_to_translate)} already translated)")

    # Collect texts to translate
    questions = [qa['question_pt'] for qa in pairs_to_translate]
    answers = [qa['answer_pt'] for qa in pairs_to_translate]
    contexts = [qa.get('context', '') if qa.get('context') else "N/A" for qa in pairs_to_translate]

    # Split into batches
    def batch_list(lst, n):
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    q_batches = batch_list(questions, BATCH_SIZE)
    a_batches = batch_list(answers, BATCH_SIZE)
    c_batches = batch_list(contexts, BATCH_SIZE)

    # Initialize rate limiter and semaphore
    rate_limiter = RateLimiter(REQUESTS_PER_MINUTE)
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        # Translate questions
        print(f"\nTranslating questions ({len(q_batches)} batches)...")
        q_tasks = [translate_batch_async(session, batch, cache, rate_limiter, semaphore) for batch in q_batches]
        q_results = await asyncio.gather(*q_tasks)
        translated_questions = [item for batch in q_results for item in batch]
        cache.save_cache()

        # Translate answers
        print(f"\nTranslating answers ({len(a_batches)} batches)...")
        a_tasks = [translate_batch_async(session, batch, cache, rate_limiter, semaphore) for batch in a_batches]
        a_results = await asyncio.gather(*a_tasks)
        translated_answers = [item for batch in a_results for item in batch]
        cache.save_cache()

        # Translate contexts
        print(f"\nTranslating contexts ({len(c_batches)} batches)...")
        c_tasks = [translate_batch_async(session, batch, cache, rate_limiter, semaphore) for batch in c_batches]
        c_results = await asyncio.gather(*c_tasks)
        translated_contexts = [item for batch in c_results for item in batch]
        cache.save_cache()

    # Update only the pairs that were translated
    for i, idx in enumerate(pair_indices):
        qa_pairs[idx]['question_en'] = translated_questions[i]
        qa_pairs[idx]['answer_en'] = translated_answers[i]
        qa_pairs[idx]['context_en'] = translated_contexts[i] if pairs_to_translate[i].get('context') else ''

    return qa_pairs


async def main_async():
    """Main async function"""
    print("=" * 60)
    print("Resume-Capable QA Pairs Translation")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Batch size: {BATCH_SIZE}")
    print()

    # Check for API key
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not found in .env file")
        return

    # Load normalized data
    if not INPUT_FILE.exists():
        print(f"❌ Error: Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load existing translations if available
    existing_data = load_existing_translations()

    if existing_data:
        print("📂 Found existing translations, resuming from where we left off...")
        qa_pairs = existing_data['qa_pairs']
    else:
        print("📂 No existing translations found, starting fresh...")
        qa_pairs = data['qa_pairs']

    # Analyze status
    status = analyze_translation_status(qa_pairs)

    print(f"\nTranslation Status:")
    print(f"  Total QA pairs: {status['total']}")
    print(f"  ✅ Already translated: {status['already_translated']}")
    print(f"  ⏳ Need translation: {status['needs_translation']}")

    if status['needs_translation'] == 0:
        print("\n✅ All translations complete!")
        return

    print(f"\n  Details:")
    print(f"    - Missing question translation: {status['missing_question']}")
    print(f"    - Missing answer translation: {status['missing_answer']}")
    print(f"    - Failed translations: {status['failed_translation']}")

    # Initialize cache
    cache = TranslationCache(CACHE_FILE)
    print(f"\nCache loaded with {len(cache.cache)} entries")

    print(f"\nReady to translate {status['needs_translation']} QA pairs")
    print("Continue? (y/n): ", end='')

    response = input().strip().lower()
    if response != 'y':
        print("Translation cancelled.")
        return

    # Translate
    start_time = time.time()
    translated_qa_pairs = await translate_missing_only(qa_pairs, cache)
    elapsed_time = time.time() - start_time

    # Save translated data
    output_data = {
        'metadata': {
            **(existing_data['metadata'] if existing_data else data['metadata']),
            'last_updated': datetime.now().isoformat(),
            'model_used': MODEL_NAME,
            'last_translation_time_seconds': elapsed_time
        },
        'qa_pairs': translated_qa_pairs
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Translation complete!")
    print(f"Translated data saved to: {OUTPUT_FILE}")
    print(f"Time taken: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)")
    print(f"Cache saved with {len(cache.cache)} entries")


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
