import pytest
import json
from pathlib import Path
from nagent_rag.validation import ValidationConfig, TestCase

@pytest.fixture
def sample_config_with_rag_data():
    return {
        "name": "Validation Test",
        "description": "Test validation config",
        "version": "1.0",
        "rag_data": [
            {"id": "doc_1", "content": "Content 1"},
            {"id": "doc_2", "content": "Content 2"}
        ],
        "test_cases": [
            {
                "id": "tc_1",
                "user_input": "Question 1",
                "reference": "Answer 1",
                "docs_indices": ["doc_1"], # Valid ID ref
                "description": "Test case with ID ref"
            },
            {
                "id": "tc_2",
                "user_input": "Question 2",
                "reference": "Answer 2",
                "docs_indices": [1], # Valid Index ref
                "description": "Test case with Index ref"
            }
        ]
    }

def test_validation_runner_logic(sample_config_with_rag_data, tmp_path):
    # 1. Save config file
    config_file = tmp_path / "test_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(sample_config_with_rag_data, f)

    # 2. Load config
    config = ValidationConfig.from_json(config_file)

    # 3. Simulate validation logic (from apps/agentic-rag/src/agentic_rag/validation_runner.py)
    all_docs = []
    if config.rag_data:
        all_docs = config.rag_data

    assert len(all_docs) == 2
    assert all_docs[0]["id"] == "doc_1"

    # 4. Validate references
    doc_ids = {str(d["id"]) for d in all_docs if "id" in d}
    missing_refs = []

    for tc in config.test_cases:
        for idx in tc.docs_indices:
            if isinstance(idx, str):
                if idx not in doc_ids:
                    missing_refs.append(f"{tc.id} -> {idx}")
            elif isinstance(idx, int):
                if idx < 0 or idx >= len(all_docs):
                    missing_refs.append(f"{tc.id} -> {idx}")

    assert len(missing_refs) == 0, f"Found missing references: {missing_refs}"

def test_invalid_reference(tmp_path):
    invalid_config = {
        "name": "Invalid Test",
        "rag_data": [{"id": "doc_1", "content": "C1"}],
        "test_cases": [
            {
                "id": "tc_invalid",
                "user_input": "Q",
                "reference": "A",
                "docs_indices": ["missing_id"] # Invalid ID ref
            }
        ]
    }

    config_file = tmp_path / "invalid_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(invalid_config, f)

    config = ValidationConfig.from_json(config_file)
    all_docs = config.rag_data
    doc_ids = {str(d["id"]) for d in all_docs}

    missing_refs = []
    for tc in config.test_cases:
        for idx in tc.docs_indices:
            if isinstance(idx, str) and idx not in doc_ids:
                missing_refs.append(idx)

    assert len(missing_refs) == 1
    assert missing_refs[0] == "missing_id"
