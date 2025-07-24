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
        {"lat": [(40, 42, 46), "N"], "lon": [(74, 0, 21), "W"]},
        {"lat": [(34, 3, 8), "N"], "lon": [(118, 14, 37), "W"]},
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
        piexif.GPSIFD.GPSLatitudeRef: city["lat"][1],
        piexif.GPSIFD.GPSLatitude: [(x, 1) for x in city["lat"][0]],
        piexif.GPSIFD.GPSLongitudeRef: city["lon"][1],
        piexif.GPSIFD.GPSLongitude: [(x, 1) for x in city["lon"][0]],
    }

    exif_dict = {"0th": zeroth, "Exif": exif, "GPS": gps}
    return piexif.dump(exif_dict)

def generate_lina_exif(width, height, description=None, keywords=None):
    now = datetime.now().strftime("%Y:%m:%d %H:%M:%S")
    current_year = datetime.now().year

    zeroth = {
        piexif.ImageIFD.Make: "Lina Creative Studio",
        piexif.ImageIFD.Model: "LinaVision 1.0",
        piexif.ImageIFD.Software: "LinaColor Touch",
        piexif.ImageIFD.DateTime: now,
        piexif.ImageIFD.Artist: "Lina Khelifi",
        piexif.ImageIFD.Copyright: f"© {current_year} Lina Creative Studio - Todos os direitos reservados",
    }

    if description:
        zeroth[piexif.ImageIFD.ImageDescription] = description.encode("utf-8")

    if keywords:
        zeroth[40094] = keywords.encode("utf-16le")  # XPKeywords

    exif = {
        piexif.ExifIFD.DateTimeOriginal: now,
        piexif.ExifIFD.PixelXDimension: width,
        piexif.ExifIFD.PixelYDimension: height,
    }

    exif_dict = {"0th": zeroth, "Exif": exif}
    return piexif.dump(exif_dict)

@app.route('/')
def index():
    return "WebP & EXIF API is running!"

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

@app.route('/convert-with-exif', methods=['POST'])
def convert_with_exif():
    try:
        img_array = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return "Invalid image", 400

        image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        exif_bytes = generate_fake_exif(image.width, image.height)

        output = io.BytesIO()
        image.save(output, format="JPEG", exif=exif_bytes, quality=95)
        output.seek(0)
        return send_file(output, mimetype="image/jpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/convert-with-lina-exif', methods=['POST'])
def convert_with_lina_exif():
    try:
        img_array = np.frombuffer(request.data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return "Invalid image", 400

        image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        description = request.headers.get("X-Image-Description")
        keywords = request.headers.get("X-Image-Keywords")

        exif_bytes = generate_lina_exif(image.width, image.height, description, keywords)

        output = io.BytesIO()
        image.save(output, format="JPEG", exif=exif_bytes, quality=95)
        output.seek(0)
        return send_file(output, mimetype="image/jpeg")

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
