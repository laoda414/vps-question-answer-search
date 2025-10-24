"""
Data Extraction and Normalization Script
Extracts QA pairs from JSON files and prepares them for translation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
PROCESSED_CHATS_DIR = PROJECT_ROOT / "data" / "add_contact_phrase" / "processed_chats"
OUTPUT_FILE = PROJECT_ROOT / "data" / "normalized_qa_pairs.json"


def extract_qa_pairs_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """Extract all QA pairs from a single JSON file"""
    qa_pairs = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        file_name = file_path.name

        # Extract metadata
        metadata = data.get('metadata', {})
        timeline = data.get('timeline_analysis', {})
        overall = data.get('overall_analysis', {})

        conversation_info = {
            'file_name': file_name,
            'start_date': timeline.get('start_date'),
            'end_date': timeline.get('end_date'),
            'total_messages': metadata.get('total_messages'),
            'conversation_duration': metadata.get('conversation_duration'),
            'overall_tone': overall.get('emotions', {}).get('overall_tone'),
            'potential_scam': overall.get('risk_assessment', {}).get('potential_scam'),
            'risk_explanation': overall.get('risk_assessment', {}).get('explanation'),
            'topics': overall.get('topics', [])
        }

        # Extract QA pairs from overall_analysis
        overall_qa = overall.get('qa_pairs', [])
        for qa in overall_qa:
            qa_pair = {
                'conversation': conversation_info,
                'question_pt': qa.get('question', ''),
                'answer_pt': qa.get('answer', ''),
                'context': qa.get('context', ''),
                'date': None,  # No specific date in overall analysis
                'source': 'overall_analysis'
            }
            qa_pairs.append(qa_pair)

        # Extract QA pairs from timeline progression
        progression = timeline.get('progression', {})
        for date_key, day_data in progression.items():
            day_qa_pairs = day_data.get('qa_pairs', [])
            emotion_tone = day_data.get('emotions', {}).get('overall_tone', '')

            for qa in day_qa_pairs:
                qa_pair = {
                    'conversation': conversation_info,
                    'question_pt': qa.get('question', ''),
                    'answer_pt': qa.get('answer', ''),
                    'context': qa.get('context', ''),
                    'date': date_key,
                    'emotion_tone': emotion_tone,
                    'source': 'timeline_progression'
                }
                qa_pairs.append(qa_pair)

        return qa_pairs

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return []


def process_all_files() -> List[Dict[str, Any]]:
    """Process all JSON files in the processed_chats directory"""
    all_qa_pairs = []

    if not PROCESSED_CHATS_DIR.exists():
        print(f"Error: Directory not found: {PROCESSED_CHATS_DIR}")
        return []

    json_files = list(PROCESSED_CHATS_DIR.glob("*.json"))
    print(f"Found {len(json_files)} JSON files to process")

    for file_path in json_files:
        print(f"Processing: {file_path.name}")
        qa_pairs = extract_qa_pairs_from_file(file_path)
        all_qa_pairs.extend(qa_pairs)
        print(f"  Extracted {len(qa_pairs)} QA pairs")

    return all_qa_pairs


def assign_unique_ids(qa_pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Assign unique IDs to each QA pair"""
    for idx, qa in enumerate(qa_pairs, start=1):
        qa['id'] = idx
    return qa_pairs


def save_normalized_data(qa_pairs: List[Dict[str, Any]]):
    """Save normalized data to JSON file"""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        'metadata': {
            'total_qa_pairs': len(qa_pairs),
            'extracted_at': datetime.now().isoformat(),
            'source_directory': str(PROCESSED_CHATS_DIR)
        },
        'qa_pairs': qa_pairs
    }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\nNormalized data saved to: {OUTPUT_FILE}")
    print(f"Total QA pairs extracted: {len(qa_pairs)}")


def main():
    print("=" * 60)
    print("QA Pairs Extraction and Normalization")
    print("=" * 60)
    print()

    # Process all files
    qa_pairs = process_all_files()

    if not qa_pairs:
        print("No QA pairs extracted. Exiting.")
        return

    # Assign unique IDs
    qa_pairs = assign_unique_ids(qa_pairs)

    # Save normalized data
    save_normalized_data(qa_pairs)

    # Print statistics
    print("\n" + "=" * 60)
    print("Statistics")
    print("=" * 60)

    # Count by source
    overall_count = sum(1 for qa in qa_pairs if qa['source'] == 'overall_analysis')
    timeline_count = sum(1 for qa in qa_pairs if qa['source'] == 'timeline_progression')

    print(f"From overall_analysis: {overall_count}")
    print(f"From timeline_progression: {timeline_count}")

    # Count unique conversations
    unique_files = set(qa['conversation']['file_name'] for qa in qa_pairs)
    print(f"Unique conversations: {len(unique_files)}")

    print("\n✅ Data extraction complete!")
    print(f"Next step: Run 'python scripts/translate_qa.py' to translate QA pairs")


if __name__ == "__main__":
    main()
