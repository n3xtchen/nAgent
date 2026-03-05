import pytest
import json
from pathlib import Path
from nagent_rag.validation import ValidationConfig, TestCase

@pytest.fixture
def sample_config_data():
    return {
        "name": "Validation Test",
        "description": "Test validation config",
        "version": "1.0",
        "rag_config": {
            "retriever": "vector_db",
            "k": 3
        },
        "rag_data": [
            {"id": "doc_1", "content": "Content 1"},
            {"id": "doc_2", "content": "Content 2"}
        ],
        "test_cases": [
            {
                "id": "tc_1",
                "user_input": "Question 1",
                "reference": "Answer 1",
                "docs_indices": [0],
                "description": "Test case 1"
            }
        ],
        "model_config": {"model": "gpt-4"},
        "metadata": {"author": "Test"}
    }

def test_validation_config_load(sample_config_data, tmp_path):
    config_file = tmp_path / "test_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(sample_config_data, f)

    config = ValidationConfig.from_json(config_file)

    assert config.name == "Validation Test"
    assert config.rag_config == sample_config_data["rag_config"]
    assert len(config.rag_data) == 2
    assert config.rag_data[0]["id"] == "doc_1"
    assert len(config.test_cases) == 1
    assert config.test_cases[0].id == "tc_1"

def test_validation_config_save(sample_config_data, tmp_path):
    config = ValidationConfig(
        name="Save Test",
        description="Test saving config",
        rag_config=sample_config_data["rag_config"],
        rag_data=sample_config_data["rag_data"],
        test_cases=[TestCase(id="tc_1", user_input="Q1", reference="A1")]
    )

    save_path = tmp_path / "saved_config.json"
    config.to_json(save_path)

    assert save_path.exists()

    with open(save_path, "r", encoding="utf-8") as f:
        loaded_data = json.load(f)

    assert loaded_data["rag_config"] == sample_config_data["rag_config"]
    assert len(loaded_data["rag_data"]) == 2
    assert loaded_data["rag_data"][0]["id"] == "doc_1"

def test_backward_compatibility(tmp_path):
    # Old config without rag_config/rag_data
    old_data = {
        "name": "Old Config",
        "description": "Old format",
        "test_cases": [
            {
                "id": "tc_1",
                "user_input": "Q1",
                "reference": "A1"
            }
        ]
    }

    config_file = tmp_path / "old_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(old_data, f)

    config = ValidationConfig.from_json(config_file)

    assert config.name == "Old Config"
    assert config.rag_config == {}
    assert config.rag_data == []
    assert len(config.test_cases) == 1
