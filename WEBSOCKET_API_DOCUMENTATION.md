# WebSocket API Documentation - Category Wise

This document details how the frontend should call various AI models via the WebSocket consumer and the exact JSON format for both requests and responses.

## 1. Connection Details
- **WebSocket URL:** `ws://<domain>/ws/chat/<session_id>/?token=<jwt_token>`
- **Authentication:** Requires a valid JWT token passed in the query string.
- **Initial Message:** Upon connection, the backend sends a `"type": "previous_messages"` payload.

---

## 2. General Response Format (Sent by Server)

All responses from the server include the user's `remaining_credits`.

### Successful AI Response
```json
{
  "type": "new_message",
  "message": {
    "id": 123,
    "sender": "ai",
    "content": "Text content from AI",
    "images": ["https://path-to-stored-image.webp"],
    "timestamp": "2026-01-22T05:00:00Z"
  },
  "remaining_credits": 1450.50
}
```

### Error Response
```json
{
  "type": "error",
  "message": "Description of the error",
  "remaining_credits": 1450.50
}
```

### Limit Exceeded
```json
{
  "type": "limit exceed",
  "message": "You have exceeded your daily limit...",
  "remaining_credits": 0.0
}
```

---

## 3. Model Categories & Request Formats (Sent by Frontend)

### A. WaveSpeed AI (Provider: `wavespeedai`)
The behavior depends on the `model_type` configured in the backend for the specific model.

#### **Text to Image**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | The image generation prompt |
| `height` | int | 1024 | | Image height |
| `width` | int | 1024 | | Image width |
| `seed` | int | -1 | | Seed for reproducibility |
| `num_images` | int | 1 | | Number of images to generate |

#### **Text to Video**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | The video generation prompt |
| `duration` | string | "4" | | Duration of the video |
| `height` | int | 1024 | | Video height |
| `width` | int | 1024 | | Video width |
| `seed` | int | 42 | | Seed for reproducibility |
| `resolution` | string | "1080p" | `"1080p"`, `"4k"`, `"720p"`, `"480p"` | Video resolution |
| `generate_audio` | bool | false | | Whether to generate audio |

#### **Image Tool (Vision/Understanding)**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Prompt or question |
| `images` | array | (Required) | | List with ONE image URL/Base64 |
| `style` | string | "default" | | Processing style |
| `target_language` | string | "english" | | Output language |
| `target_resolution` | string | "4k" | | Output resolution |

#### **Image Editor**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Edit instructions |
| `images` | array | (Required) | | List with ONE image URL/Base64 to edit |
| `output_format` | string | "jpeg" | `"jpeg"`, `"png"`, `"webp"` | Format of output |
| `aspect_ratio` | string | "1:1" | `"1:1"`, `"16:9"`, etc. | Final aspect ratio |

#### **Video Effect**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `images` | array | (Required) | | Source image for the effect |
| `effect` | string | null | | Name of the effect |
| `duration` | int | 5 | | Effect duration in seconds |
| `resolution` | int/str | 480 | | Output resolution |
| `bgm` | bool | false | | Background music toggle |
| `template` | string | "sexy_devil" | | Template name |
| `sound_effect_switch` | bool | false | | Sound effects toggle |
| `seed` | int | 42 | | Seed for consistent motion |

#### **Text to Speech**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Text to convert to speech |
| `voice_id` | string | "Wise_Woman" | | ID of the voice |
| `format` | string | "mp3" | `"mp3"`, `"wav"` | Audio format |
| `speed` | float | 1 | | Speech speed |
| `pitch` | float | 1 | | Speech pitch |
| `volume` | float | 1 | | Output volume |
| `emotion` | string | null | | Emotional tone |
| `language_boost` | string | "auto" | | Language optimization |
| `sample_rate` | int | null | | Audio sample rate |
| `bitrate` | int | null | | Audio bitrate |
| `channel` | string | null | | Mono/Stereo |

---

### B. Google Gemini (Provider: `google`)

#### **Chat & Image Understanding**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Text prompt or question |
| `images` | array | optional | | List of URLs or Base64 |
| `num_images` | int | 1 | | Internal control |

#### **Text to Video (Veo3)**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Video prompt |
| `aspect_ratio` | string | null | | Preferred ratio |
| `resolution` | string | null | | Video resolution |

---

### C. OpenAI (Provider: `openai`)

#### **Chat & Vision (GPT-4)**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Text prompt |
| `images` | array | optional | | List of URLs or Base64 |
| `num_images` | int | 1 | | Number of responses |
| `height` | int | 512 | | For gen tasks |
| `width` | int | 512 | | For gen tasks |
| `aspect_ratio` | string | null | | Preferred ratio |

#### **Text/Image to Video (Sora)**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Video prompt |
| `duration` | string | "4" | `"4"`, `"8"`, `"12"` | Duration |
| `width` | int | 1024 | | Video width |
| `height` | int | 1024 | | Video height |
| `seed` | int | -1 | | Reproducibility seed |

---

### D. Deepseek (Provider: `deepseek`)

#### **Chat**
| Field | Type | Default | Exact/Choices | Description |
| :--- | :--- | :--- | :--- | :--- |
| `message` | string | (Required) | | Text prompt for chat |

---

### E. Other Providers (Leonardo & FalAI)

#### **Leonardo AI**
- `message`: Prompt
- `num_images`: (default 1)
- `width`: (default 512)
- `height`: (default 512)

#### **FalAI**
- `message`: Prompt
- `num_images`: (default 1)
- `size`: (default "512x512")
- `steps`: (default 50)
- `cfg_scale`: (default 7.0)
- `seed`: (default 6252023)

---

## 4. Input Options Reference (Exact Matches)

### Video Durations
- OpenAI Sora: `"4"`, `"8"`, `"12"`
- WaveSpeed: (Any integer string, standard is `"4"`)

### Aspect Ratios
- Common: `"1:1"`, `"16:9"`, `"9:16"`, `"4:3"`, `"3:4"`

### Resolutions
- WaveSpeed: `"1080p"`, `"4k"`, `"720p"`, `"480p"`
- Google: `"720p"`

### Image Formats
- `output_format`: `"jpeg"`, `"png"`, `"webp"`

### Media Detection Logic
The consumer automatically detects if an entry in the `images` array is an image or video based on the URL extension or Base64 prefix.
- **Images:** `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `data:image/...`
- **Videos:** `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`
