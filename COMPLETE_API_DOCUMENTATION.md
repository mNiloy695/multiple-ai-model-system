# Complete API Documentation

**Base URL:** `http://10.10.13.75:8082/api/v1/`

---

## Table of Contents
1. [Authentication](#authentication)
2. [AI Models](#ai-models)
3. [Chat Sessions](#chat-sessions)
4. [WebSocket Chat](#websocket-chat)
5. [Plans & Subscriptions](#plans--subscriptions)
6. [Invoices](#invoices)
7. [Ads & Rewards](#ads--rewards)

---

## Authentication

### 1. Register User
**Endpoint:** `POST /api/v1/accounts/register/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "username": "johndoe"
}
```

**Response (201):**
```json
{
  "message": "Registration successful. Please check your email to activate your account.",
  "user_id": 1
}
```

---

### 2. Activate Account
**Endpoint:** `POST /api/v1/accounts/activate/`

**Request Body:**
```json
{
  "token": "activation_token_from_email"
}
```

**Response (200):**
```json
{
  "message": "Account activated successfully."
}
```

---

### 3. Login
**Endpoint:** `POST /api/v1/accounts/login/`

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "subscribed": false,
    "api_limit": 100,
    "total_token_used": 0
  }
}
```

---

### 4. Google Login
**Endpoint:** `POST /api/v1/accounts/google/login/`

**Request Body:**
```json
{
  "token": "google_oauth_token"
}
```

**Response (200):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

---

### 5. Logout
**Endpoint:** `POST /api/v1/accounts/logout/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200):**
```json
{
  "message": "Logout successful."
}
```

---

### 6. Forgot Password
**Endpoint:** `POST /api/v1/accounts/forgot-password/`

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "message": "Password reset link sent to your email."
}
```

---

### 7. Reset Password
**Endpoint:** `POST /api/v1/accounts/reset-password/`

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "newSecurePassword123"
}
```

**Response (200):**
```json
{
  "message": "Password reset successful."
}
```

---

### 8. Get User Profile
**Endpoint:** `GET /api/v1/accounts/profile/{user_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "subscribed": false,
  "api_limit": 100,
  "total_token_used": 500,
  "credits": 10000
}
```

---

### 9. Update User Profile
**Endpoint:** `PATCH /api/v1/accounts/profile/{user_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "username": "newusername"
}
```

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "newusername",
  "subscribed": false
}
```

---

### 10. Credit Transaction History
**Endpoint:** `GET /api/v1/accounts/transactions/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "amount": -500,
      "transaction_type": "debit",
      "description": "AI model usage",
      "created_at": "2026-01-17T10:30:00Z"
    }
  ]
}
```

---

## AI Models

### 1. List All AI Models
**Endpoint:** `GET /api/v1/list/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `model_type` (optional): Filter by model type
  - `chat`
  - `text_to_image`
  - `text_to_video`
  - `image_to_video`
  - `text_or_image_to_video`
  - `image_editor`
  - `image_tool`
  - `video_upscaler`
  - `image_to_3d`
  - `video_effect`
  - `text_to_speech`
- `provider` (optional): Filter by provider (`openai`, `google`, `wavespeedai`, `deepseek`)

**Response (200):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "GPT-4",
      "model_id": "gpt-4",
      "description": "Advanced language model",
      "provider": "openai",
      "model_type": "chat",
      "base_cost": 500.00
    },
    {
      "id": 2,
      "name": "Gemini 2.0 Flash",
      "model_id": "gemini-2.0-flash-exp",
      "description": "Fast multimodal model",
      "provider": "google",
      "model_type": "chat",
      "base_cost": 500.00
    }
  ]
}
```

**Note:** API keys are NOT exposed in the response for security.

---

### 2. Get Single AI Model
**Endpoint:** `GET /api/v1/list/{model_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "name": "GPT-4",
  "model_id": "gpt-4",
  "description": "Advanced language model",
  "provider": "openai",
  "model_type": "chat",
  "base_cost": 500.00
}
```

---

## Chat Sessions

### 1. Create Chat Session
**Endpoint:** `POST /api/v1/chat/session/list/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "model_id": 1,
  "session_type": "chat"
}
```

**Session Types:**
- `chat` - Text conversation
- `text_to_image` - Image generation
- `text_to_video` - Video generation from text
- `image_to_video` - Video generation from image
- `text_or_image_to_video` - Video from text or image
- `image_editor` - Image editing
- `image_tool` - Image processing tools
- `video_upscaler` - Video upscaling
- `image_to_3d` - 3D model generation
- `video_effect` - Video effects
- `text_to_speech` - Speech synthesis

**Response (201):**
```json
{
  "id": 1,
  "model": {
    "id": 1,
    "name": "GPT-4",
    "model_id": "gpt-4",
    "description": "Advanced language model",
    "provider": "openai",
    "model_type": "chat",
    "base_cost": 500.00
  },
  "user": 1,
  "messages": [],
  "summary": null,
  "created_at": "2026-01-17T10:00:00Z",
  "updated_at": "2026-01-17T10:00:00Z",
  "session_type": "chat"
}
```

---

### 2. List User's Chat Sessions
**Endpoint:** `GET /api/v1/chat/session/list/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "model": {
        "id": 1,
        "name": "GPT-4",
        "model_id": "gpt-4",
        "provider": "openai",
        "model_type": "chat"
      },
      "user": 1,
      "messages": [
        {
          "id": 1,
          "sender": "user",
          "content": "Hello!",
          "images": [],
          "created_at": "2026-01-17T10:01:00Z"
        }
      ],
      "summary": null,
      "created_at": "2026-01-17T10:00:00Z",
      "updated_at": "2026-01-17T10:01:00Z",
      "session_type": "chat"
    }
  ]
}
```

---

### 3. Get Single Chat Session
**Endpoint:** `GET /api/v1/chat/session/list/{session_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "model": {
    "id": 1,
    "name": "GPT-4",
    "model_id": "gpt-4",
    "provider": "openai",
    "model_type": "chat"
  },
  "user": 1,
  "messages": [],
  "summary": null,
  "created_at": "2026-01-17T10:00:00Z",
  "updated_at": "2026-01-17T10:00:00Z",
  "session_type": "chat"
}
```

---

### 4. Update Chat Session
**Endpoint:** `PATCH /api/v1/chat/session/list/{session_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "summary": "Updated conversation summary"
}
```

**Response (200):**
```json
{
  "id": 1,
  "model": {...},
  "user": 1,
  "messages": [],
  "summary": "Updated conversation summary",
  "created_at": "2026-01-17T10:00:00Z",
  "updated_at": "2026-01-17T10:30:00Z",
  "session_type": "chat"
}
```

---

### 5. Delete Chat Session
**Endpoint:** `DELETE /api/v1/chat/session/list/{session_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204):** No content

---

## WebSocket Chat

### WebSocket Connection
**Endpoint:** `ws://10.10.13.75:8082/ws/chat/{session_id}/?token={jwt_token}`

**Connection URL Example:**
```
ws://10.10.13.75:8082/ws/chat/1/?token=eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

### Message Format by Model Type

#### 1. Chat Models (OpenAI, Google, DeepSeek)

**Send Message:**
```json
{
  "message": "Hello, how are you?",
  "images": []
}
```

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 1,
    "sender": "ai",
    "content": "I'm doing well, thank you!",
    "images": [],
    "timestamp": "2026-01-17T10:00:00Z"
  }
}
```

---

#### 2. Text-to-Image (OpenAI DALL-E, Wavespeed AI)

**Send Message:**
```json
{
  "message": "A beautiful sunset over mountains",
  "num_images": 1,
  "width": 1024,
  "height": 1024
}
```

**Parameters:**
- `message` (required): Image description
- `num_images` (optional): Number of images (default: 1)
- `width` (optional): Image width (default: 1024)
  - OpenAI: 1024, 1536 (with height 1024)
  - Wavespeed: Any size
- `height` (optional): Image height (default: 1024)
  - OpenAI: 1024, 1536 (with width 1024)
  - Wavespeed: Any size

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 2,
    "sender": "ai",
    "content": "1 image(s) generated",
    "images": [
      "https://example.com/media/generated_image.webp"
    ],
    "timestamp": "2026-01-17T10:01:00Z"
  }
}
```

---

#### 3. Text-to-Video (OpenAI Sora, Wavespeed AI, Google Veo)

**Send Message (OpenAI Sora):**
```json
{
  "message": "A cinematic drone shot of a futuristic city",
  "duration": "4",
  "width": 1280,
  "height": 720,
  "seed": 42
}
```

**Parameters:**
- `message` (required): Video description.
- `duration` (optional): Video duration in seconds (default: "4").
  - Allowed values: "4", "8", "12".
- `width` (optional): Video width.
- `height` (optional): Video height.
- `seed` (optional): Random seed (default: -1).

**Resolution Constraints (`width` x `height`):**
- **Sora-2 (`sora-2`):**
  - 1280x720 (Landscape)
  - 720x1280 (Portrait)
- **Sora-2 Pro (`sora-2-pro`):**
  - 1280x720 (Landscape)
  - 720x1280 (Portrait)
  - 1792x1024 (High Res Landscape)
  - 1024x1792 (High Res Portrait)

**Send Message (Wavespeed AI):**
```json
{
  "message": "A cat playing with a ball",
  "duration": 5,
  "resolution": "1080p",
  "generate_audio": false,
  "seed": 42
}
```

**Parameters:**
- `message` (required): Video description
- `duration` (optional): Video duration in seconds (default: 5)
- `resolution` (optional): Video resolution (default: "1080p")
  - Options: "480p", "720p", "1080p"
- `generate_audio` (optional): Generate audio (default: false)
- `seed` (optional): Random seed for reproducibility (default: 42)

**Send Message (Google Veo):**
```json
{
  "message": "A serene lake at sunrise",
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

**Parameters:**
- `message` (required): Video description
- `aspect_ratio` (optional): Video aspect ratio
  - Options: "16:9", "9:16", "1:1"
- `resolution` (optional): Video resolution (default: "720p")
  - Options: "480p", "720p", "1080p"

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 3,
    "sender": "ai",
    "content": "Video generated successfully.",
    "images": [
      "https://example.com/media/generated_video.mp4"
    ],
    "timestamp": "2026-01-17T10:05:00Z"
  }
}
```

---

#### 4. Image Editor (Wavespeed AI)

**Send Message:**
```json
{
  "message": "Make the sky more dramatic",
  "images": ["https://example.com/input_image.jpg"],
  "aspect_ratio": "16:9",
  "output_format": "jpeg"
}
```

**Parameters:**
- `message` (required): Editing instruction
- `images` (required): Array with one input image URL
- `aspect_ratio` (optional): Output aspect ratio (default: "1:1")
  - Options: "1:1", "16:9", "9:16", "4:3", "3:4"
- `output_format` (optional): Output format (default: "jpeg")
  - Options: "jpeg", "png", "webp"

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 4,
    "sender": "ai",
    "content": "Image edited successfully",
    "images": [
      "https://example.com/media/edited_image.webp"
    ],
    "timestamp": "2026-01-17T10:02:00Z"
  }
}
```

---

#### 5. Image Tool (Wavespeed AI)

**Send Message:**
```json
{
  "message": "Enhance this image",
  "images": ["https://example.com/input_image.jpg"],
  "style": "default",
  "target_language": "english",
  "target_resolution": "4k"
}
```

**Parameters:**
- `message` (required): Processing instruction
- `images` (required): Array with one input image URL
- `style` (optional): Processing style (default: "default")
- `target_language` (optional): Target language (default: "english")
- `target_resolution` (optional): Target resolution (default: "4k")
  - Options: "1080p", "2k", "4k", "8k"

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 5,
    "sender": "ai",
    "content": "Image processed successfully",
    "images": [
      "https://example.com/media/processed_image.webp"
    ],
    "timestamp": "2026-01-17T10:03:00Z"
  }
}
```

---

#### 6. Video Upscaler (Wavespeed AI)

**Send Message:**
```json
{
  "images": ["https://example.com/input_video.mp4"],
  "target_resolution": "4k"
}
```

**Parameters:**
- `images` (required): Array with one input video URL
- `target_resolution` (optional): Target resolution (default: "4k")
  - Options: "1080p", "2k", "4k", "8k"

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 6,
    "sender": "ai",
    "content": "Image upscaled successfully",
    "images": [
      "https://example.com/media/upscaled_video.mp4"
    ],
    "timestamp": "2026-01-17T10:04:00Z"
  }
}
```

---

#### 7. Image to 3D (Wavespeed AI)

**Send Message:**
```json
{
  "images": ["https://example.com/input_image.jpg"]
}
```

**Parameters:**
- `images` (required): Array with one input image URL

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 7,
    "sender": "ai",
    "content": "3d image successfully generated",
    "images": [
      "https://example.com/media/3d_model.glb"
    ],
    "timestamp": "2026-01-17T10:06:00Z"
  }
}
```

---

#### 8. Video Effect (Wavespeed AI)

**Send Message:**
```json
{
  "images": ["https://example.com/input_image.jpg"],
  "resolution": 480,
  "effect": "zoom",
  "duration": 5,
  "bgm": false,
  "template": "sexy_devil",
  "sound_effect_switch": false,
  "seed": 42
}
```

**Parameters:**
- `images` (required): Array with one input image URL
- `resolution` (optional): Video resolution (default: 480)
  - Options: 480, 720, 1080
- `effect` (optional): Video effect type
- `duration` (optional): Video duration in seconds (default: 5)
- `bgm` (optional): Add background music (default: false)
- `template` (optional): Effect template (default: "sexy_devil")
- `sound_effect_switch` (optional): Enable sound effects (default: false)
- `seed` (optional): Random seed (default: 42)

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 8,
    "sender": "ai",
    "content": "Video Generated successfully",
    "images": [
      "https://example.com/media/effect_video.mp4"
    ],
    "timestamp": "2026-01-17T10:07:00Z"
  }
}
```

---

#### 9. Text-to-Speech (Wavespeed AI)

**Send Message:**
```json
{
  "message": "Hello, this is a test of text to speech.",
  "voice_id": "Wise_Woman",
  "speed": 1.0,
  "pitch": 1.0,
  "volume": 1.0,
  "format": "mp3",
  "bitrate": null,
  "sample_rate": null,
  "emotion": null,
  "english_normalization": false,
  "language_boost": "auto",
  "channel": null
}
```

**Parameters:**
- `message` (required): Text to convert to speech
- `voice_id` (optional): Voice identifier (default: "Wise_Woman")
- `speed` (optional): Speech speed (default: 1.0)
- `pitch` (optional): Voice pitch (default: 1.0)
- `volume` (optional): Audio volume (default: 1.0)
- `format` (optional): Audio format (default: "mp3")
  - Options: "mp3", "wav", "ogg"
- `bitrate` (optional): Audio bitrate
- `sample_rate` (optional): Audio sample rate
- `emotion` (optional): Voice emotion
- `english_normalization` (optional): Normalize English text (default: false)
- `language_boost` (optional): Language boost (default: "auto")
- `channel` (optional): Audio channel configuration

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 9,
    "sender": "ai",
    "content": "Video Generated successfully",
    "images": [
      "https://example.com/media/speech.mp3"
    ],
    "timestamp": "2026-01-17T10:08:00Z"
  }
}
```

---

#### 10. Video Generation (OpenAI Sora)

**Send Message:**
```json
{
  "message": "A futuristic city at night",
  "duration": 4,
  "width": 1280,
  "height": 720
}
```

**Parameters:**
- `message` (required): Video description
- `duration` (optional): Video duration in seconds (default: 4)
- `width` (optional): Video width (default: 1280)
  - Valid combinations: 720x1280 or 1280x720
- `height` (optional): Video height (default: 720)
  - Valid combinations: 720x1280 or 1280x720

**Receive Response:**
```json
{
  "type": "new_message",
  "message": {
    "id": 10,
    "sender": "ai",
    "content": "Video generation started: job_123456",
    "images": [],
    "timestamp": "2026-01-17T10:09:00Z"
  }
}
```

---

### Error Responses

**Insufficient Credits:**
```json
{
  "type": "error",
  "message": "Insufficient credits. Required: 500"
}
```

**API Limit Exceeded:**
```json
{
  "type": "limit exceed",
  "message": "You exceed today limit watch ads or buy subscription for get more request"
}
```

**Free User Restriction:**
```json
{
  "type": "error",
  "message": "Only DeepSeek model is available for free users. Please upgrade to access OpenAI models."
}
```

**AI Processing Error:**
```json
{
  "type": "error",
  "message": "AI error: <error_details>"
}
```

---

## Plans & Subscriptions

### 1. List All Plans
**Endpoint:** `GET /api/v1/plan/list/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Basic Plan",
      "price": 9.99,
      "credits": 10000,
      "duration_days": 30,
      "description": "Basic monthly plan",
      "is_active": true
    }
  ]
}
```

---

### 2. Get Single Plan
**Endpoint:** `GET /api/v1/plan/list/{plan_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "name": "Basic Plan",
  "price": 9.99,
  "credits": 10000,
  "duration_days": 30,
  "description": "Basic monthly plan",
  "is_active": true
}
```

---

### 3. Verify Google Purchase
**Endpoint:** `POST /api/v1/plan/checkout/google-pay/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "purchase_token": "google_purchase_token",
  "product_id": "plan_basic_monthly",
  "package_name": "com.yourapp.ai"
}
```

**Response (200):**
```json
{
  "message": "Purchase verified successfully",
  "credits_added": 10000,
  "subscription_active": true
}
```

---

### 4. Get Total Revenue (Admin Only)
**Endpoint:** `GET /api/v1/plan/revenue/`

**Headers:**
```
Authorization: Bearer <admin_access_token>
```

**Response (200):**
```json
{
  "total_revenue": 15000.50,
  "monthly_revenue": 2500.00,
  "total_subscriptions": 150
}
```

---

## Invoices

### 1. List User Invoices
**Endpoint:** `GET /api/v1/invoices/list/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "plan": {
        "id": 1,
        "name": "Basic Plan",
        "price": 9.99
      },
      "amount": 9.99,
      "status": "paid",
      "created_at": "2026-01-17T10:00:00Z"
    }
  ]
}
```

---

### 2. Get Single Invoice
**Endpoint:** `GET /api/v1/invoices/list/{invoice_id}/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": 1,
  "user": 1,
  "plan": {
    "id": 1,
    "name": "Basic Plan",
    "price": 9.99
  },
  "amount": 9.99,
  "status": "paid",
  "created_at": "2026-01-17T10:00:00Z",
  "invoice_number": "INV-2026-001"
}
```

---

## Ads & Rewards

### 1. List Reward History
**Endpoint:** `GET /api/v1/ads/rewards/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "user": 1,
      "reward_type": "ad_watch",
      "credits_earned": 100,
      "created_at": "2026-01-17T10:00:00Z"
    }
  ]
}
```

---

### 2. Claim Ad Reward
**Endpoint:** `POST /api/v1/ads/rewards/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "ad_id": "ad_123456",
  "reward_type": "ad_watch"
}
```

**Response (201):**
```json
{
  "id": 2,
  "user": 1,
  "reward_type": "ad_watch",
  "credits_earned": 100,
  "created_at": "2026-01-17T10:30:00Z",
  "message": "100 credits added to your account"
}
```

---

## Model-Specific Parameters Summary

### Chat Models
**Providers:** OpenAI (GPT-4, GPT-3.5), Google (Gemini), DeepSeek

**Parameters:**
- `message` (required): Text message
- `images` (optional): Array of image URLs for multimodal chat

---

### Image Generation
**Providers:** OpenAI (DALL-E), Wavespeed AI

**Parameters:**
- `message` (required): Image description
- `num_images` (optional): 1-10
- `width` (optional): Image width in pixels
- `height` (optional): Image height in pixels

---

### Video Generation
**Providers:** OpenAI (Sora), Google (Veo), Wavespeed AI

**Parameters:**
- `message` (required): Video description
- `duration` (optional): 1-10 seconds
- `width` (optional): Video width
- `height` (optional): Video height
- `resolution` (optional): "480p", "720p", "1080p"
- `aspect_ratio` (optional): "16:9", "9:16", "1:1"
- `generate_audio` (optional): true/false

---

### Image Editing
**Provider:** Wavespeed AI

**Parameters:**
- `message` (required): Editing instruction
- `images` (required): Input image URL
- `aspect_ratio` (optional): Output aspect ratio
- `output_format` (optional): "jpeg", "png", "webp"

---

### Image Tools
**Provider:** Wavespeed AI

**Parameters:**
- `message` (required): Processing instruction
- `images` (required): Input image URL
- `style` (optional): Processing style
- `target_language` (optional): Target language
- `target_resolution` (optional): "1080p", "2k", "4k", "8k"

---

### Video Upscaling
**Provider:** Wavespeed AI

**Parameters:**
- `images` (required): Input video URL
- `target_resolution` (optional): "1080p", "2k", "4k", "8k"

---

### Image to 3D
**Provider:** Wavespeed AI

**Parameters:**
- `images` (required): Input image URL

---

### Video Effects
**Provider:** Wavespeed AI

**Parameters:**
- `images` (required): Input image URL
- `resolution` (optional): 480, 720, 1080
- `effect` (optional): Effect type
- `duration` (optional): 1-10 seconds
- `bgm` (optional): true/false
- `template` (optional): Effect template name
- `sound_effect_switch` (optional): true/false
- `seed` (optional): Random seed

---

### Text-to-Speech
**Provider:** Wavespeed AI

**Parameters:**
- `message` (required): Text to convert
- `voice_id` (optional): Voice identifier
- `speed` (optional): 0.5-2.0
- `pitch` (optional): 0.5-2.0
- `volume` (optional): 0.0-1.0
- `format` (optional): "mp3", "wav", "ogg"
- `bitrate` (optional): Audio bitrate
- `sample_rate` (optional): Sample rate
- `emotion` (optional): Voice emotion
- `english_normalization` (optional): true/false
- `language_boost` (optional): "auto" or language code
- `channel` (optional): Channel configuration

---

## Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `204 No Content` - Resource deleted successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Rate Limiting

- **Free Users:** 100 requests per day (DeepSeek only)
- **Subscribed Users:** Unlimited requests (based on credits)

---

## Credits System

- Credits are deducted based on:
  - Input text (words × base_cost)
  - Input images (count × base_cost)
  - Output text (words × base_cost)
  - Generated images/videos (count × base_cost)

- **Base Costs:**
  - OpenAI: 500 credits per unit
  - Google: 500 credits per unit
  - Wavespeed AI: 500 credits per unit
  - DeepSeek: 1 credit per unit

---

## Notes

1. All timestamps are in ISO 8601 format (UTC)
2. Image URLs in responses are publicly accessible
3. WebSocket connections require JWT token in query parameter
4. API keys are never exposed in API responses
5. Free users can only access DeepSeek models
6. Subscribed users have access to all models based on credits

---

**Last Updated:** January 17, 2026
