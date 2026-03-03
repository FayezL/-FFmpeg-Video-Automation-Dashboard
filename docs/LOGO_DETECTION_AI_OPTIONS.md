# Logo Detection: ChatGPT vs Gemini vs What Actually Works

You asked for **more accurate, fewer frames, and a more powerful AI** for logo detection. Here’s what to use and what to avoid.

---

## Don’t use ChatGPT or Gemini for this

- **ChatGPT (GPT-4 Vision)** and **Gemini** are **language models with vision**. They’re built for understanding and describing images, not for returning precise **bounding box coordinates** (x, y, width, height).
- In practice, vision APIs often **refuse or give vague answers** when you ask for exact logo coordinates, and they don’t output the pixel rectangles you need for the delogo filter.
- So: **not suitable** for “detect logo and give me a box to remove it.”

---

## What to use instead

You need a **logo/object detection** system that returns **bounding boxes**. Two good options:

| Option | Best for | Frames | Accuracy | Cost | Setup |
|--------|----------|--------|----------|------|--------|
| **Google Cloud Vision API (Logo Detection)** | Best balance of accuracy and simplicity | Few (e.g. 3–5) | High for known logos | Pay per image, free tier | GCP project + API key |
| **YOLO (local model)** | No cloud, no API key, fast | Few | Good (depends on model) | Free | Install Ultralytics, optional logo model |

---

## Recommended: Google Cloud Vision API

- **Purpose-built logo detection**: returns logo name + **bounding box** (then we convert to x, y, w, h for FFmpeg delogo).
- **Few frames**: we send only a few keyframes (e.g. 3–5) instead of scanning every 30th frame.
- **Strong accuracy** on common/brand logos.
- **Setup**: Google Cloud project → enable Vision API → create a service account key → set `GOOGLE_APPLICATION_CREDENTIALS` (or use the app’s AI backend setting).
- **Pricing**: per-image; free tier available. See [Cloud Vision pricing](https://cloud.google.com/vision/pricing).

You **do not** need ChatGPT or Gemini for this; the **Vision API** is the right Google product for logo detection with coordinates.

---

## Alternative: YOLO (local, no API)

- Run **YOLOv8** (Ultralytics) locally; use a model trained for “logo” or generic object detection and filter by class.
- **Few frames**: run inference on 3–5 keyframes only.
- **No cloud**, no API key, good speed on GPU or CPU.
- **Accuracy** depends on the model (generic COCO vs logo-specific).

---

## What we added in this project

1. **Optional Google Cloud Vision backend**  
   When configured, the app uses Vision API for logo detection: **only 5 keyframes** (fewer frames), higher accuracy, same “Apply” → delogo flow.

2. **Detection method selector**  
   In the Batch Processor → **AI Logo Detection** section you can choose:
   - **OpenCV (local)** – edge-based detection, no API, works offline.
   - **Google Cloud Vision (AI)** – appears in the dropdown only if the library is installed and credentials are set.

### How to enable Google Cloud Vision (AI)

1. **Install the optional dependency**
   ```bash
   pip install -r requirements-ai.txt
   ```
   or: `pip install google-cloud-vision`

2. **Google Cloud setup**
   - Create a [Google Cloud project](https://console.cloud.google.com/) and enable the [Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com).
   - Create a service account and download its JSON key.
   - Set the environment variable to the key file path:
     - Windows: `set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your-key.json`
     - macOS/Linux: `export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json`

3. **Restart the app.** The “Method” dropdown will show **Google Cloud Vision (AI)**. Select it and click **Detect Logo**.

You don’t need ChatGPT or Gemini; **Google Cloud Vision** is the right “powerful AI” option for logo detection with boxes. Use **YOLO** if you prefer a local, no-API solution.
