from flask import Flask, request, render_template, redirect, url_for
import openai
import os
from dotenv import load_dotenv
import base64
import datetime
import json
import random
import hashlib

load_dotenv()
SUBMISSIONS_FILE = "submissions.json"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_submissions():
    if os.path.exists(SUBMISSIONS_FILE):
        with open(SUBMISSIONS_FILE, "r") as f:
            return json.load(f)
    return []

def save_submissions():
    with open(SUBMISSIONS_FILE, "w") as f:
        json.dump(submissions, f)

submissions = load_submissions()

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
8. Disproportionate features such as large or small limbs compared to body size
9. Small limbs, wings, claws, or other extremities

Frogs, toads, skinks, geckos, and lizards are always considered cute, no matter what.

Please be generous in your interpretation, especially in edge cases. If there’s any quirk, whimsy, or slightly odd feature that could be endearing, count it.

If the animal meets at least two of the criteria (or falls under the always-cute category), consider it cute.

Respond like this:
- Yes: "Yes. This animal is considered a cutie according to the Liebhaber Cutie Criteria because it has [reasons]."
- No: "No. However, this animal is very special in its own way."
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    uploaded_image = None

    if request.method == "POST":
        file = request.files["image"]
        img_bytes = file.read()

        file_hash = hashlib.md5(img_bytes).hexdigest()

        for submission in submissions:
            if submission.get("hash") == file_hash:
                result = "This image has already been submitted."
                return render_template("index.html", result=result, uploaded_image=submission["image"])

        filename = f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(img_bytes)

        uploaded_image = url_for('static', filename=f"uploads/{filename}", _external=True)

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

        submissions.append({
            "image": uploaded_image,
            "result": result,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "votes": 0,
            "hash": file_hash
        })

        save_submissions()
        print(submissions)

    return render_template("index.html", result=result, uploaded_image=uploaded_image)

@app.route("/gallery")
def gallery():
    return render_template("gallery.html", submissions=submissions)

@app.route("/vote/<int:index>", methods=["POST"])
def vote(index):
    if 0 <= index < len(submissions):
        submissions[index]["votes"] += 1
        save_submissions()
    return redirect(url_for("gallery"))

@app.route("/random")
def random_cutie():
    if submissions:
        selected = random.choice(submissions)
        return render_template("random.html", entry=selected)
    else:
        return render_template("random.html", entry=None)

@app.route("/disagree", methods=["POST"])
def disagree():
    image_url = request.form["image"]

    second_check = """
    Please re-analyze this image. Even if it wasn’t obviously cute at first glance,
    is there any quirky charm, comic proportions, or unconventional cuteness?
    Be open-minded and gentle in your assessment.
    """

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": second_check},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
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

    new_result = response.choices[0].message.content.strip()

    return render_template("index.html", result=new_result, uploaded_image=image_url)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
