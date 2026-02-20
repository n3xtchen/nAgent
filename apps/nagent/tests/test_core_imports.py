import json
import pytest
from nagent.utils import is_retryable_error, robust_json_parse
from google.genai import errors

# Tests for utilities are now moved to libs/nagent-core/tests/test_utils.py
# Here we just keep a smoke test or rely on the core tests.

def test_imports_from_core():
    # Verify that the imports are working and they are indeed the functions we expect
    from nagent_core.utils import is_retryable_error as core_is_retryable
    from nagent_core.utils import robust_json_parse as core_robust_json_parse

    assert is_retryable_error is core_is_retryable
    assert robust_json_parse is core_robust_json_parse
