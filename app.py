from flask import Flask, request, send_file, jsonify
import io
import random
from datetime import datetime
from PIL import Image
import piexif

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
        {"lat": [40, 42, 46], "latRef": "N", "lon": [74, 0, 21], "lonRef": "W"},
        {"lat": [34, 3, 8], "latRef": "N", "lon": [118, 14, 37], "lonRef": "W"},
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

@app.route('/convert', methods=['POST'])
def convert():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    try:
        image = Image.open(file.stream).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Invalid image: {str(e)}"}), 400

    webp_image = convert_to_webp(image)
    return send_file(webp_image, mimetype="image/webp")

@app.route('/convert-with-exif', methods=['POST'])
def convert_with_exif():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    try:
        image = Image.open(file.stream).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Invalid image: {str(e)}"}), 400

    output = io.BytesIO()
    exif_bytes = generate_fake_exif(image.width, image.height)
    image.save(output, format="JPEG", exif=exif_bytes, quality=95)
    output.seek(0)
    return send_file(output, mimetype="image/jpeg")

if __name__ == "__main__":
    app.run(debug=True)
