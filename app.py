from flask import Flask, request, send_file, jsonify
import cv2
import numpy as np
import io
from PIL import Image
import piexif
from datetime import datetime
import random

app = Flask(__name__)

def convert_to_webp(image: Image.Image, quality: int = 90):
    output = io.BytesIO()
    image.save(output, format="WEBP", quality=quality)
    output.seek(0)
    return output

def generate_fake_exif(width, height):
    camera_data = {
        "SONY": ["ILCE-7M3", "ILCE-9"],
        "Canon": ["Canon EOS R5", "Canon EOS Rebel T8i"],
    }
    cities = [
        {
            "lat": [(40, 1), (42, 1), (46, 1)],
            "latRef": "N",
            "lon": [(74, 1), (0, 1), (21, 1)],
            "lonRef": "W"
        },
        {
            "lat": [(34, 1), (3, 1), (8, 1)],
            "latRef": "N",
            "lon": [(118, 1), (14, 1), (37, 1)],
            "lonRef": "W"
        },
        {
            "lat": [(36, 1), (45, 1), (0, 1)],
            "latRef": "N",
            "lon": [(3, 1), (3, 1), (0, 1)],
            "lonRef": "E"
        }
    ]

    brand = random.choice(list(camera_data.keys()))
    model = random.choice(camera_data[brand])
    city = random.choice(cities)
    now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

    zeroth = {
        piexif.ImageIFD.Make: brand,
        piexif.ImageIFD.Model: model,
        piexif.ImageIFD.Software: "Adobe Lightroom",
        piexif.ImageIFD.DateTime: now,
    }
    exif = {
        piexif.ExifIFD.DateTimeOriginal: now,
        piexif.ExifIFD.PixelXDimension: width,
        piexif.ExifIFD.PixelYDimension: height,
    }
    gps = {
        piexif.GPSIFD.GPSLatitudeRef: city["latRef"],
        piexif.GPSIFD.GPSLatitude: city["lat"],
        piexif.GPSIFD.GPSLongitudeRef: city["lonRef"],
        piexif.GPSIFD.GPSLongitude: city["lon"],
    }

    exif_dict = {"0th": zeroth, "Exif": exif, "GPS": gps}
    return piexif.dump(exif_dict)

@app.route('/')
def index():
    return "WebP & EXIF API is running!"

@app.route('/convert-with-exif', methods=['POST'])
def convert_with_exif():
    try:
        # Step 1: Read the image
        img_array = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return "Invalid image", 400

        # Step 2: Convert to PIL and add EXIF
        image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        exif_bytes = generate_fake_exif(image.width, image.height)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", exif=exif_bytes, quality=95)
        buffer.seek(0)

        # Step 3: Read modified image again and pass to convert()
        img_with_exif = cv2.imdecode(np.frombuffer(buffer.read(), np.uint8), cv2.IMREAD_COLOR)
        pil_image = Image.fromarray(cv2.cvtColor(img_with_exif, cv2.COLOR_BGR2RGB))
        webp_image = convert_to_webp(pil_image)

        return send_file(webp_image, mimetype="image/webp")

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/convert', methods=['POST'])
def convert():
    try:
        img_array = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return "Invalid image", 400

        image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        webp_image = convert_to_webp(image)
        return send_file(webp_image, mimetype="image/webp")

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
