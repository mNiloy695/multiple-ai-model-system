# API Documentation

Base URL: `/api/v1/`

## Authentication

Authentication is primarily Header-based using JWT (JSON Web Tokens).
**Header:** `Authorization: Bearer <access_token>`

### Register
**Endpoint:** `POST /accounts/register/`
**Input:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "confirm_password": "string",
  "first_name": "string",
  "last_name": "string"
}
```
**Output:**
```json
{
  "message": "User registered successfully. Please check your email for the verification code."
}
```

### Login
**Endpoint:** `POST /accounts/login/`
**Input:**
```json
{
  "email": "string",
  "password": "string"
}
```
**Output:**
```json
{
  "user": {
    "user_id": 1,
    "email": "user@example.com",
    "username": "user",
    "is_active": true,
    "subscribed": false,
    "credits_balance": 100,
    "total_token_used": 0
  },
  "refresh": "eyJ0...",
  "access": "eyJ0..."
}
```

### Google Login
**Endpoint:** `POST /accounts/google/login/`
**Input:**
```json
{
  "id_token": "string"
}
```
**Output:** (Returns JWT tokens)

### Logout
**Endpoint:** `POST /accounts/logout/`
**Input:**
```json
{
  "refresh": "string"
}
```
**Output:** `{"message": "User logged out successfully."}`

### Activate Account
**Endpoint:** `POST /accounts/activate/`
**Input:**
```json
{
  "email": "string",
  "code": "123456"
}
```
**Output:** `{"message": "Account activated successfully."}`

### Forgot Password
**Endpoint:** `POST /accounts/forgot-password/`
**Input:** `{"email": "string"}`

### Reset Password
**Endpoint:** `POST /accounts/reset-password/`
**Input:**
```json
{
  "email": "string",
  "code": "string",
  "password": "string"
}
```

---

## User Profile & Transactions

### Get/Update Profile
**Endpoint:** `GET /accounts/profile/` or `PATCH /accounts/profile/{id}/`
**Input (PATCH):** Multipart/form-data for `avatar`, plus `first_name`, `last_name`.
**Output:**
```json
{
    "id": 1,
    "user": 1,
    "user_details": {
        "id": 1,
        "username": "string",
        "email": "string",
        "total_token_used": 0,
        "words": 0
    },
    "first_name": "string",
    "last_name": "string",
    "avatar": "url"
}
```

### Transaction History
**Endpoint:** `GET /accounts/transactions/`
**Output:**
```json
[
  {
    "id": 1,
    "amount": 100,
    "transaction_type": "string",
    "message": "string",
    "created_at": "datetime"
  }
]
```

---

## AI Models (REST)

### List AI Models
**Endpoint:** `GET /list/`
**Query Params:**
- `model_type` (optional): `text_to_video`, `image_to_video` filtering.
**Output:**
```json
[
  {
    "id": 1,
    "name": "GPT-4",
    "model_id": "gpt-4",
    "description": "...",
    "base_cost": 10,
    "model_type": "chat",
    "provider": "openai"
  }
]
```

### List Chat Sessions
**Endpoint:** `GET /chat/session/list/`
**Output:**
```json
[
  {
    "id": 1,
    "model": 1,
    "messages": [], // List of messages
    "session_type": "chat",
    "summary": "..."
  }
]
```

### Create Chat Session
**Endpoint:** `POST /chat/session/list/`
**Input:**
```json
{
  "session_type": "chat",  // or "text_to_image", etc.
  "model": 1 // ID of the AI Model from /list/
}
```
**Output:** (Returns created Session object)

---

## Chat & AI Generation (WebSocket)

**URL:** `ws://<host>/ws/chat/<session_id>/?token=<ACCESS_TOKEN>`

### Events
**On Connect:**
Server sends history:
```json
{
  "type": "previous_messages",
  "messages": [ ... ]
}
```

**Send Message (Client to Server):**
Standard Chat:
```json
{
  "message": "Hello AI"
}
```

WaveSpeedAI & Advanced Models (Image/Video):
Parameters depend on the `model_type` of the session's model.
```json
{
  "message": "Prompt text",
  "images": ["url1", "url2"], // Optional
  "width": 1024,
  "height": 1024,
  "num_images": 1,
  "duration": 5, // For video
  "aspect_ratio": "16:9",
  "style": "cinematic", // For image tools
  "target_resolution": "4k" // For upscaler
}
```

**Receive Message (Server to Client):**
New Message:
```json
{
  "type": "new_message",
  "message": {
    "sender": "ai", // or "user"
    "content": "Response text",
    "images": ["url_to_generated_image"],
    "timestamp": "..."
  }
}
```
Error:
```json
{
  "type": "error", 
  "message": "..."
}
```

---

## Plans & Subscription

### List Plans
**Endpoint:** `GET /plan/list/`
**Output:**
```json
[
  {
    "id": 1,
    "name": "Standard Plan",
    "plan_code": "std_01",
    "description": "...",
    "words_or_credits": 1000,
    "amount": 9.99
  }
]
```

### Verify Google Purchase (Top-up)
**Endpoint:** `POST /plan/checkout/google-pay/`
**Input:**
```json
{
  "plan": 1, // Plan ID
  "purchase_token": "google_play_token"
}
```
**Output:** `{"status": "success", "credits_added": 1000}`

---

## Ads & Rewards

### Rewards History
**Endpoint:** `GET /ads/rewards/`
**Output:** List of reward history items.

### Add Reward
**Endpoint:** `POST /ads/rewards/`
**Input:**
```json
{
  "reward": 10 // Amount of credits/coins
}
```

## Invoices
**Endpoint:** `GET /invoices/list/`
**Output:** List of invoices (filtered by user).
