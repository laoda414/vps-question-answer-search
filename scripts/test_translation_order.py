"""
Test script to verify translation order is preserved
Tests with just 5 QA pairs to avoid wasting API credits
"""

import json
import asyncio
import aiohttp
import os
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "normalized_qa_pairs.json"

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen/qwen3-235b-a22b-2507")
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.3"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))


async def translate_single_text(session: aiohttp.ClientSession, text: str, delay: float = 0) -> str:
    """Translate a single text with optional delay to simulate different completion times"""

    # Add artificial delay to simulate varying API response times
    if delay > 0:
        await asyncio.sleep(delay)

    prompt = f"""Translate the following Portuguese text to English. Preserve the meaning, context, and tone.

Portuguese text: {text}

Return ONLY the English translation, nothing else."""

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

    try:
        async with session.post(OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60) as response:
            response.raise_for_status()
            result = await response.json()

        translation = result['choices'][0]['message']['content'].strip()
        # Remove quotes if present
        if translation.startswith('"') and translation.endswith('"'):
            translation = translation[1:-1]

        return translation

    except Exception as e:
        print(f"Error translating: {e}")
        return text  # Fallback to original


async def test_translation_order():
    """Test that translation order is preserved"""

    print("=" * 80)
    print("Translation Order Test")
    print("=" * 80)
    print()

    # Check for API key
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPENROUTER_API_KEY not found in .env file")
        return False

    # Load test data (first 5 QA pairs)
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    test_pairs = data['qa_pairs'][:5]
    test_questions = [qa['question_pt'] for qa in test_pairs]

    print(f"Testing with {len(test_questions)} questions:")
    for i, q in enumerate(test_questions, 1):
        print(f"{i}. {q[:70]}...")
    print()

    # Translate with varying delays to ensure they complete in different order
    delays = [0.5, 0.1, 0.3, 0.0, 0.2]  # Different delays to simulate varying response times

    print("Translating with artificial delays to test ordering...")
    print("(Delays: 0.5s, 0.1s, 0.3s, 0.0s, 0.2s)")
    print()

    async with aiohttp.ClientSession() as session:
        # Create tasks with delays
        tasks = [
            translate_single_text(session, q, delay)
            for q, delay in zip(test_questions, delays)
        ]

        # Use gather to maintain order
        print("Using asyncio.gather() to maintain order...")
        translations = await asyncio.gather(*tasks)

    # Verify results
    print("\n" + "=" * 80)
    print("Results")
    print("=" * 80)

    all_correct = True

    for i, (orig, trans) in enumerate(zip(test_questions, translations), 1):
        print(f"\n--- Pair {i} ---")
        print(f"PT: {orig}")
        print(f"EN: {trans}")

        # Simple verification: English should be different from Portuguese
        # and should not contain the exact Portuguese text
        if orig.lower() == trans.lower():
            print("⚠️  WARNING: Translation identical to original!")
            all_correct = False
        elif len(trans) < 5:
            print("⚠️  WARNING: Translation too short!")
            all_correct = False
        else:
            print("✅ Translation looks reasonable")

    print("\n" + "=" * 80)
    print("Order Preservation Test")
    print("=" * 80)

    # Manual verification prompt
    print("\n📋 Manual Verification Required:")
    print("Please check that the English translations above match the Portuguese text.")
    print("For example:")
    print("  - Question 1 (PT) should correspond to Translation 1 (EN)")
    print("  - Question 2 (PT) should correspond to Translation 2 (EN)")
    print("  etc.")
    print()
    print("Do the translations match the correct questions? (y/n): ", end='')

    user_input = input().strip().lower()

    if user_input == 'y':
        print("\n✅ Translation order test PASSED!")
        print("✅ It's safe to run the full translation: python scripts/translate_qa_parallel.py")
        return True
    else:
        print("\n❌ Translation order test FAILED!")
        print("❌ There's still an issue with the translation script.")
        print("Please review the code before running full translation.")
        return False


async def main():
    """Main entry point"""
    try:
        result = await test_translation_order()
        return result
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
