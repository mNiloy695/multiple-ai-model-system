# QA Analysis & Improvement Plan

## 1. QA Test Scenarios

To ensure the stability and reliability of the `Google Gemini` integration and `consumers.py`, the following test scenarios should be executed.

### A. Functional Testing (Positive Flow)
1.  **Text Chat**: Send a standard text message to a Gemini-based session. Verify a text response is received and credits are deducted based on word count.
2.  **Image Generation**: Send a prompt specifically asking to "create an image" (or use a model tagged as image generation). Verify that:
    -   An image URL (or base64) is returned.
    -   Credits are deducted based on `base_cost * num_images`.
    -   The `is_image_generation` flag logic accurately detects the model type.
3.  **Image Understanding (Vision)**: Send a text prompt *with* an attached image URL. Verify the model analyzes the image and returns a description.

### B. Functional Testing (Negative Flow / Error Handling)
1.  **Insufficient Credits**: Set a user's credit balance to 0. Attempt to generate text or images. Verify the proper error message ("Insufficient credits") is returned and the database functions return early.
2.  **API Key Failure**: Use an invalid API Key. Verify the system catches the exception and returns a "Gemini request failed" error without crashing the WebSocket.
3.  **Model Not Found**: Request a non-existent `model_id`. Verify standard error handling.
4.  **Network/Timeout**: Simulate a network timeout. Verify the transaction rollback works (refund logic) so users aren't charged for failed requests.

### C. Concurrency / Load Testing
1.  **Simultaneous Requests**: Send multiple requests for the same user rapidly. Verify:
    -   `transaction.atomic()` and `select_for_update()` prevent race conditions.
    -   The user's balance does not go negative incorrectly.

## 2. Code Analysis & Potential Error Points

### `ai_model/google_func.py`

**Strengths:**
-   **Atomic Transactions**: The use of `transaction.atomic()` with `select_for_update()` is robust for credit safety.
-   **Refund Mechanism**: The `try...except` block correctly attempts to refund tokens if the API call crashes.

**Potential Risks / Errors:**
1.  **Image Download Failure**: The `download_and_store_webp(images)` function is external. If it fails or raises an exception *after* the API call succeeds, the code might fall into the `except` block and refund the user, even though the AI *did* generate the image (user gets free compute).
    -   *Mitigation*: Separate the "API Call" success from "Post-processing" success. Only refund if the *API Call* fails.
2.  **Unknown Model Types**: The `_detect_model_type` function relies on string matching (e.g., "image", "vision"). If a new Google model comes out with a weird name (e.g., "gemini-ultra-v2"), it defaults to "chat". This might be incorrect if it's actually an image model but doesn't have "image" in the ID.
3.  **Base64 Memory Usage**: For Image Understanding, `_read_image_to_base64` downloads the image into memory. If users upload 10MB+ images, this could spike server RAM.
    -   *Mitigation*: Stream files or enforce size limits before processing.

### `ai_model/consumers.py`

**Potential Risks / Errors:**
1.  **JSON Parsing**: `json.loads(text_data)` is wrapped in try/except, but if `text_data` is None (connection keep-alive), it returns early (good). However, `message_content` extraction could be more robust against missing keys.
2.  **WebSocket Disconnects**: If the user disconnects *during* the `await database_sync_to_async(gemini_response)` call, the server continues processing. The `await self.send()` will fail properly, but the credits are already deducted.
    -   *This is acceptable behavior* (user paid for the request), but technically they didn't receive the result.
3.  **Complex Provider Logic**: The `if provider == ... elif ...` chain is getting very long. This violates the "Open/Closed Principle".
    -   *Refactor Suggestion*: Use a Strategy Pattern or a Dispatcher (e.g., `PROVIDER_HANDLERS[provider](...)`) to route requests. This makes the file much smaller and easier to test.

## 3. Improvement Suggestions

### 1. Refactor `consumers.py` Provider Logic
Currently, `ChatConsumer.receive` is a massive function. Move provider logic into separate service files (which we started with `google_func` and `openai_func`), but genericize the interface.

**Example:**
```python
# Create a unified interface for all providers
async def get_ai_response(provider, **kwargs):
    if provider == 'google':
        return await gemini_response(**kwargs)
    elif provider == 'openai':
        return await gpt_response(**kwargs)
    # ...
```

### 2. Robust Logging
Add `logging` instead of `print()`. `print()` in production (Django/Channels) often gets lost or clogs stdout.
```python
import logging
logger = logging.getLogger(__name__)

# Replace print(ai_response) with:
logger.info(f"AI Response for user {user_id}: {ai_response}")
```

### 3. Strict Type Hinting
Add Python type hints (`def func(a: int) -> dict:`) to `google_func.py`. This helps with static analysis and preventing basic type errors (like passing a string "100" instead of integer 100 for cost).

### 4. Enhance `download_and_store_webp`
Ensure this function handles failures gracefully (retries) so a temporary network blip doesn't fail the entire user request after the expensive AI generation is done.

## 4. Proposed `tests.py` Snippet

You can add this to `ai_model/tests.py` to test the cost calculation logic without making real API calls.

```python
from django.test import TestCase
from decimal import Decimal
from .google_func import calculate_cost, _detect_model_type

class GoogleFuncTestCase(TestCase):
    def test_cost_calculation_chat(self):
        cost = calculate_cost("chat", base_cost=10, words=50)
        self.assertEqual(cost, Decimal("500")) # 50 words * 10

    def test_cost_calculation_image(self):
        cost = calculate_cost("image_generation", base_cost=100, num_images=2)
        self.assertEqual(cost, Decimal("200")) # 2 images * 100

    def test_detect_model_type(self):
        self.assertEqual(_detect_model_type("gemini-pro-vision"), "chat") # Default to chat/text based on current logic unless "image" is in name
        self.assertEqual(_detect_model_type("gemini-image-gen"), "image_generation")
```
