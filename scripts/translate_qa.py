"""
Translation Script using OpenRouter API
Translates Portuguese QA pairs to English using AI models
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
from dotenv import load_dotenv
from tqdm import tqdm

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


def translate_batch(texts: List[str], cache: TranslationCache) -> List[str]:
    """Translate a batch of texts using OpenRouter API"""

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

    # Make API request
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

    try:
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        content = result['choices'][0]['message']['content'].strip()

        # Parse JSON response
        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        translated_texts = json.loads(content)

        # Store in cache and update translations list
        for idx, translated in zip(text_indices, translated_texts):
            cache.set(texts[idx], translated)
            translations[idx] = translated

        # Save cache after each batch
        cache.save_cache()

        return translations

    except Exception as e:
        print(f"\nError during translation: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'N/A'}")
        # Return original texts as fallback
        for idx in text_indices:
            translations[idx] = texts[idx]
        return translations


def translate_qa_pairs(qa_pairs: List[Dict[str, Any]], cache: TranslationCache) -> List[Dict[str, Any]]:
    """Translate all QA pairs with progress tracking"""

    total_pairs = len(qa_pairs)
    print(f"Translating {total_pairs} QA pairs in batches of {BATCH_SIZE}...")

    # Collect all texts to translate
    questions = [qa['question_pt'] for qa in qa_pairs]
    answers = [qa['answer_pt'] for qa in qa_pairs]
    contexts = [qa.get('context', '') for qa in qa_pairs]

    # Translate in batches
    translated_questions = []
    translated_answers = []
    translated_contexts = []

    # Translate questions
    print("\nTranslating questions...")
    for i in tqdm(range(0, len(questions), BATCH_SIZE)):
        batch = questions[i:i + BATCH_SIZE]
        translated = translate_batch(batch, cache)
        translated_questions.extend(translated)
        time.sleep(0.5)  # Rate limiting

    # Translate answers
    print("\nTranslating answers...")
    for i in tqdm(range(0, len(answers), BATCH_SIZE)):
        batch = answers[i:i + BATCH_SIZE]
        translated = translate_batch(batch, cache)
        translated_answers.extend(translated)
        time.sleep(0.5)  # Rate limiting

    # Translate contexts
    print("\nTranslating contexts...")
    for i in tqdm(range(0, len(contexts), BATCH_SIZE)):
        batch = contexts[i:i + BATCH_SIZE]
        # Skip empty contexts
        batch_filtered = [c if c else "N/A" for c in batch]
        translated = translate_batch(batch_filtered, cache)
        translated_contexts.extend(translated)
        time.sleep(0.5)  # Rate limiting

    # Update QA pairs with translations
    for idx, qa in enumerate(qa_pairs):
        qa['question_en'] = translated_questions[idx]
        qa['answer_en'] = translated_answers[idx]
        qa['context_en'] = translated_contexts[idx] if contexts[idx] else ''

    return qa_pairs


def main():
    print("=" * 60)
    print("QA Pairs Translation using OpenRouter")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    print(f"Batch size: {BATCH_SIZE}")
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
    print(f"Loaded {len(qa_pairs)} QA pairs")

    # Initialize cache
    cache = TranslationCache(CACHE_FILE)
    print(f"Cache loaded with {len(cache.cache)} entries")

    # Estimate cost
    total_texts = len(qa_pairs) * 3  # questions + answers + contexts
    estimated_requests = (total_texts // BATCH_SIZE) + 1
    print(f"\nEstimated API requests: {estimated_requests}")
    print(f"Note: This will consume API credits. Continue? (y/n): ", end='')

    response = input().strip().lower()
    if response != 'y':
        print("Translation cancelled.")
        return

    # Translate
    start_time = time.time()
    translated_qa_pairs = translate_qa_pairs(qa_pairs, cache)
    elapsed_time = time.time() - start_time

    # Save translated data
    output_data = {
        'metadata': {
            **data['metadata'],
            'translated_at': datetime.now().isoformat(),
            'model_used': MODEL_NAME,
            'translation_time_seconds': elapsed_time
        },
        'qa_pairs': translated_qa_pairs
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Translation complete!")
    print(f"Translated data saved to: {OUTPUT_FILE}")
    print(f"Time taken: {elapsed_time:.2f} seconds")
    print(f"Cache saved with {len(cache.cache)} entries")
    print(f"\nNext step: Run 'python scripts/init_db.py' to initialize the database")


if __name__ == "__main__":
    main()
