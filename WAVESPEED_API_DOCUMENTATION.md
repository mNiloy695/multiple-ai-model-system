# Wavespeed AI Model API Documentation

This documentation provides detailed parameter specifications for each Wavespeed AI model type available in the system.

**Provider:** `wavespeedai`  
**WebSocket Endpoint:** `ws://your-domain/ws/chat/{session_id}/?token={jwt_token}`

---

## Overview

Wavespeed AI models are accessed through WebSocket connections. Each model type has specific parameters that must be sent in the JSON payload. The system automatically routes requests based on the `model_type` field in the database.

**Important Notes:**
- All Wavespeed models require a **subscription** (free users cannot access)
- Credits are deducted based on `base_cost` × usage (e.g., number of images)
- The `model_id` and `api_key` are retrieved from the database model configuration

---

## Common WebSocket Message Structure

```json
{
  "message": "Your prompt text",
  "images": ["image_url_or_base64"],
  "voice": "base64_or_url_audio_data",
  "width": 1024,
  "height": 1024,
  "num_images": 1,
  "seed": 42,
  "duration": 5,
  "resolution": "1080p",
  "aspect_ratio": "1:1",
  "output_format": "jpeg",
  "generate_audio": false,
  "num_inference_steps": 45,
  "guidance_scale": 7.5
}
```

---

## Model Type 1: Text to Image

**Database `model_type`:** `text_to_image`

Generates images from text prompts using Wavespeed AI's image generation models.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | string | ✅ Yes | - | Text prompt describing the image to generate |
| `width` | integer | ❌ No | `1024` | Width of generated image in pixels |
| `height` | integer | ❌ No | `1024` | Height of generated image in pixels |

### Backend Payload (Auto-constructed)

```json
{
  "enable_base64_output": false,
  "enable_sync_mode": false,
  "prompt": "{{message}}",
  "seed": -1,
  "size": "{{height}} * {{width}}"
}
```

### Example Request

```json
{
  "message": "A futuristic city skyline at sunset with flying cars",
  "width": 1024,
  "height": 768
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 123,
    "sender": "ai",
    "content": "Image generated successfully (1024*768) in 12.34 seconds.",
    "images": ["https://your-domain/media/ai_images/uuid.jpg"],
    "voice": null,
    "timestamp": "2026-01-27T23:00:00Z"
  },
  "remaining_credits": 9500
}
```

---

## Model Type 2: Text to Video

**Database `model_type`:** `text_to_video`

Generates videos from text prompts.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | string | ✅ Yes | - | Text prompt for video generation |
| `duration` | integer | ❌ No | - | Duration of video in seconds |
| `width` | integer | ❌ No | `1024` | Video width in pixels |
| `height` | integer | ❌ No | `1024` | Video height in pixels |
| `seed` | integer | ❌ No | `42` | Random seed for reproducibility |
| `resolution` | string | ❌ No | `"1080p"` | Video resolution (e.g., "1080p", "720p", "4k") |
| `generate_audio` | boolean | ❌ No | `false` | Whether to generate audio for the video |

### Example Request

```json
{
  "message": "A serene beach with waves crashing at sunset",
  "duration": 10,
  "resolution": "1080p",
  "generate_audio": true,
  "seed": 42
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 124,
    "sender": "ai",
    "content": "Video generated successfully.",
    "images": ["https://your-domain/media/videos/uuid.mp4"],
    "voice": null,
    "timestamp": "2026-01-27T23:05:00Z"
  },
  "remaining_credits": 8500
}
```

---

## Model Type 3: Image Tool

**Database `model_type`:** `image_tool`

Performs various processing operations on uploaded images.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | array | ✅ Yes | - | Array of image URLs or base64 strings (at least 1 required) |
| `message` | string | ❌ No | - | Optional prompt for processing instructions |
| `style` | string | ❌ No | `"default"` | Processing style to apply |
| `target_language` | string | ❌ No | `"english"` | Target language for text extraction/translation |
| `target_resolution` | string | ❌ No | `"4k"` | Target resolution for output |

### Example Request

```json
{
  "images": ["https://example.com/image.jpg"],
  "message": "Extract text and translate to Spanish",
  "style": "default",
  "target_language": "spanish",
  "target_resolution": "4k"
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 125,
    "sender": "ai",
    "content": "Image processed successfully",
    "images": ["https://your-domain/media/ai_images/uuid.jpg"],
    "voice": null,
    "timestamp": "2026-01-27T23:10:00Z"
  },
  "remaining_credits": 8000
}
```

---

## Model Type 4: Video Upscaler

**Database `model_type`:** `video_upscaler`

Upscales videos or images to higher resolutions.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | array | ✅ Yes | - | Array containing video/image URL or base64 (at least 1 required) |
| `target_resolution` | string | ❌ No | `"4k"` | Target resolution (e.g., "4k", "8k", "1080p") |

### Example Request

```json
{
  "images": ["https://example.com/video.mp4"],
  "target_resolution": "4k"
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 126,
    "sender": "ai",
    "content": "Image upscaled successfully",
    "images": ["https://your-domain/media/videos/uuid.mp4"],
    "voice": null,
    "timestamp": "2026-01-27T23:15:00Z"
  },
  "remaining_credits": 7500
}
```

---

## Model Type 5: Image Editor

**Database `model_type`:** `image_editor`

Edits existing images based on text prompts.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | array | ✅ Yes | - | Array of image URLs or base64 strings (at least 1 required) |
| `message` | string | ✅ Yes | - | Editing instructions/prompt |
| `output_format` | string | ❌ No | `"jpeg"` | Output format ("jpeg", "png", "webp") |
| `aspect_ratio` | string | ❌ No | `"1:1"` | Aspect ratio for output (e.g., "16:9", "1:1", "4:3") |

### Example Request

```json
{
  "images": ["https://example.com/photo.jpg"],
  "message": "Remove background and add sunset lighting",
  "output_format": "png",
  "aspect_ratio": "16:9"
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 127,
    "sender": "ai",
    "content": "Image edited successfully",
    "images": ["https://your-domain/media/ai_images/uuid.png"],
    "voice": null,
    "timestamp": "2026-01-27T23:20:00Z"
  },
  "remaining_credits": 7000
}
```

---

## Model Type 6: Image to 3D

**Database `model_type`:** `image_to_3d`

Converts 2D images into 3D models or representations.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | array | ✅ Yes | - | Array of image URLs or base64 strings (at least 1 required) |

### Example Request

```json
{
  "images": ["https://example.com/object.jpg"]
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 128,
    "sender": "ai",
    "content": "3d image succesfully genereated",
    "images": ["https://your-domain/media/ai_images/uuid.glb"],
    "voice": null,
    "timestamp": "2026-01-27T23:25:00Z"
  },
  "remaining_credits": 6500
}
```

---

## Model Type 7: Video Effect

**Database `model_type`:** `video_effect`

Applies special effects and transformations to videos.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `images` | array | ✅ Yes | - | Array containing video/image URL or base64 (at least 1 required) |
| `duration` | integer | ❌ No | `5` | Duration of output video in seconds |
| `resolution` | integer | ❌ No | `480` | Output resolution (e.g., 480, 720, 1080) |
| `effect` | string | ❌ No | `null` | Specific effect to apply |
| `bgm` | boolean | ❌ No | `false` | Whether to add background music |
| `seed` | integer | ❌ No | `42` | Random seed for reproducibility |
| `template` | string | ❌ No | `"sexy_devil"` | Effect template to use |
| `sound_effect_switch` | boolean | ❌ No | `false` | Whether to enable sound effects |

### Example Request

```json
{
  "images": ["https://example.com/video.mp4"],
  "duration": 10,
  "resolution": 1080,
  "effect": "cinematic",
  "bgm": true,
  "template": "sexy_devil",
  "sound_effect_switch": true,
  "seed": 42
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 129,
    "sender": "ai",
    "content": "Video Generated successfully",
    "images": ["https://your-domain/media/videos/uuid.mp4"],
    "voice": null,
    "timestamp": "2026-01-27T23:30:00Z"
  },
  "remaining_credits": 6000
}
```

---

## Model Type 8: Text to Speech

**Database `model_type`:** `text_to_speech`

Converts text into natural-sounding speech audio.

### Frontend Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | string | ✅ Yes | - | Text to convert to speech |
| `voice_id` | string | ❌ No | `"Wise_Woman"` | Voice identifier to use |
| `bitrate` | integer | ❌ No | `null` | Audio bitrate in kbps |
| `emotion` | string | ❌ No | `null` | Emotion to apply to voice |
| `english_normalization` | boolean | ❌ No | `false` | Whether to normalize English text |
| `format` | string | ❌ No | `"mp3"` | Output audio format (mp3, wav, ogg) |
| `language_boost` | string | ❌ No | `"auto"` | Language boost setting |
| `pitch` | float | ❌ No | `1` | Voice pitch multiplier |
| `sample_rate` | integer | ❌ No | `null` | Audio sample rate in Hz |
| `speed` | float | ❌ No | `1` | Speech speed multiplier |
| `volume` | float | ❌ No | `1` | Audio volume multiplier |
| `channel` | string | ❌ No | `null` | Audio channel configuration |

### Example Request

```json
{
  "message": "Hello, this is a test of the text to speech system.",
  "voice_id": "Wise_Woman",
  "format": "mp3",
  "speed": 1.0,
  "pitch": 1.0,
  "volume": 1.0,
  "emotion": "neutral"
}
```

### Response

```json
{
  "type": "new_message",
  "message": {
    "id": 130,
    "sender": "ai",
    "content": "Video Generated successfully",
    "images": ["https://your-domain/media/audio/uuid.mp3"],
    "voice": null,
    "timestamp": "2026-01-27T23:35:00Z"
  },
  "remaining_credits": 5500
}
```

---

## Error Handling

All Wavespeed models return errors in the following format:

```json
{
  "type": "error",
  "message": "Error description here",
  "remaining_credits": 5500
}
```

### Common Errors

| Error Message | Cause | Solution |
|--------------|-------|----------|
| `"Only free model is available for free users..."` | User not subscribed | Upgrade to premium subscription |
| `"Insufficient credits! TOP UP NOW!"` | Not enough credits | Purchase more credits |
| `"Image tool requires an image..."` | Missing required image | Upload at least one image |
| `"This model does not support chat"` | Wrong model type | Use appropriate chat model |
| `"Authentication failed: Invalid API key."` | Invalid API credentials | Check model configuration in admin |
| `"Request timed out after 10 minutes"` | Processing timeout | Try again or reduce complexity |

---

## Voice Chat Support (NEW)

All chat models now support voice input for voice-to-text processing.

### Voice Parameter

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `voice` | string | ❌ No | `null` | Base64-encoded audio or audio URL (MP3 format recommended) |

### Example with Voice

```json
{
  "message": "",
  "voice": "data:audio/mp3;base64,//uQxAAAAAAAAAAAAAAAAAAAAAAASW5mbw..."
}
```

The voice file will be:
1. Decoded from base64 (if applicable)
2. Saved to `/media/audio/` directory
3. Stored in the `ChatMessage.voice` field
4. Returned in message history with URL

---

## Credits & Billing

- **Text to Image:** `base_cost` × `num_images`
- **Text to Video:** `base_cost` × `duration` (seconds)
- **Image Processing:** `base_cost` per operation
- **Text to Speech:** `base_cost` per request

Default `base_cost` is **500 credits** if not configured in the model settings.

---

## WebSocket Connection Example

```javascript
const ws = new WebSocket('ws://your-domain/ws/chat/123/?token=your_jwt_token');

ws.onopen = () => {
  ws.send(JSON.stringify({
    message: "Generate a sunset landscape",
    width: 1024,
    height: 768
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
};
```

---

## Notes

1. All image/video inputs support both **URLs** and **base64** encoding
2. Base64 images are automatically detected and stored locally
3. The system handles image format conversion (PNG, JPEG, WEBP, SVG)
4. Video files are stored in `/media/videos/` directory
5. Audio files are stored in `/media/audio/` directory
6. All responses include `remaining_credits` field
7. Free users are blocked from accessing Wavespeed models
