from flask import Flask, request, render_template
import openai
import os
from dotenv import load_dotenv
import base64
import datetime

load_dotenv()

app = Flask(__name__)
client = openai.OpenAI()  # For openai>=1.3.5

# Cuteness criteria
CRITERIA = """
Evaluate if the animal in the photo is cute based on the following criteria:
1. Big, round eyes
2. Soft, fluffy fur or feathers
3. Small, rounded body shape
4. Playful, curious, or gentle expression
5. Rounded features like a blunt, round snout or a rounded body
6. Cartoonish qualities like eyes that are very close together or far apart
7. Unusual charm — something endearing even if not conventionally cute

Frogs, toads, skinks, geckos, and lizards are always considered cute, no matter what.

If the animal meets at least two of the criteria (or falls under the always-cute category), consider it cute.

Respond like this:
- Yes: "Yes. This animal is considered a cutie according to the Liebhaber Cutie Criteria because it has [reasons]."
- No: "No. This animal is very cool and special in its own way, but it’s not bringing the cute vibes — [reasons]."
"""

# In-memory gallery store (will reset if app restarts)
gallery_items = []

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    uploaded_image = None
    if request.method == "POST":
        file = request.files["image"]
        img_bytes = file.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        uploaded_image = f"data:image/jpeg;base64,{img_base64}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CRITERIA},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": uploaded_image
                        }
                    }
                ]
            }
        ]

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()

        # Store in gallery
        gallery_items.append({
            "image": uploaded_image,
            "caption": result,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    return render_template("index.html", result=result, uploaded_image=uploaded_image)

@app.route("/gallery")
def gallery():
    return render_template("gallery.html", submissions=submissions)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
