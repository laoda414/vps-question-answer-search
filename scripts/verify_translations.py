"""
Verification script to check if translations match the original text
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TRANSLATED_FILE = PROJECT_ROOT / "data" / "translated_qa_pairs.json"


def verify_translations():
    """Verify that translations are properly paired with originals"""

    if not TRANSLATED_FILE.exists():
        print("❌ Translated file not found!")
        return False

    with open(TRANSLATED_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    qa_pairs = data['qa_pairs']
    print(f"Total QA pairs: {len(qa_pairs)}")
    print("\n" + "=" * 80)
    print("Verifying Translation Quality")
    print("=" * 80)

    issues = []

    # Check first 10 for quick verification
    print("\nChecking first 10 QA pairs for obvious mismatches...")
    for i in range(min(10, len(qa_pairs))):
        qa = qa_pairs[i]

        q_pt = qa.get('question_pt', '')
        q_en = qa.get('question_en', '')
        a_pt = qa.get('answer_pt', '')
        a_en = qa.get('answer_en', '')

        # Simple heuristic checks
        q_len_ratio = len(q_en) / len(q_pt) if len(q_pt) > 0 else 0
        a_len_ratio = len(a_en) / len(a_pt) if len(a_pt) > 0 else 0

        print(f"\n--- QA Pair {i+1} ---")
        print(f"Q PT: {q_pt[:100]}")
        print(f"Q EN: {q_en[:100]}")
        print(f"Length ratio: {q_len_ratio:.2f}")

        # Flag suspicious translations
        if q_len_ratio < 0.3 or q_len_ratio > 3.0:
            issues.append(f"QA {i+1}: Suspicious length ratio {q_len_ratio:.2f}")
            print("⚠️  WARNING: Length ratio suspicious!")

        # Check for common Portuguese words in English translation
        pt_words = ['você', 'que', 'para', 'com', 'não', 'mais']
        if any(word in q_en.lower() for word in pt_words):
            issues.append(f"QA {i+1}: Portuguese words found in English translation")
            print("⚠️  WARNING: Portuguese words in English translation!")

    print("\n" + "=" * 80)
    print("Verification Summary")
    print("=" * 80)

    if issues:
        print(f"\n❌ Found {len(issues)} potential issues:")
        for issue in issues[:5]:  # Show first 5
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more")
        return False
    else:
        print("\n✅ All checked translations look good!")
        return True


if __name__ == "__main__":
    verify_translations()
