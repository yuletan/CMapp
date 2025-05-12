from flask import Flask, request, jsonify, render_template
import math
import requests # <-- Added import
from deep_translator import GoogleTranslator # <-- Added import
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Replace with your actual Pexels API key
PEXELS_API_KEY = 'UneoipG2MW5UoXzIB99UD5A8LW84gcOjmEa7EXZlxsVsBwCMp0Krhefu' # Replace with your actual key

def calculate_effective_temperature(temp_c, humidity_percent, wind_kph):
    effective_temp = temp_c
    if temp_c > 20:
        if humidity_percent > 60:
            heat_adj = ((humidity_percent - 60) / 20) * ((temp_c - 20) / 10)
            effective_temp += max(0, heat_adj)
    if wind_kph > 5:
        if temp_c < 15:
            chill_factor = (wind_kph**0.16) * ((15 - temp_c) / 20)
            effective_temp -= max(0, chill_factor * 1.5)
        elif temp_c < 25:
            chill_factor = (wind_kph**0.16) * ((25 - temp_c) / 25)
            effective_temp -= max(0, chill_factor * 0.8)
    if temp_c < 10 and humidity_percent > 70:
        effective_temp -= (humidity_percent - 70) / 50
    return effective_temp

def get_clothing_recommendation(temperature_c, humidity_percent, uv_index, wind_speed_kph):
    # --- (Keep the existing recommendation logic the same) ---
    if not all(isinstance(i, (int, float)) for i in [temperature_c, humidity_percent, uv_index, wind_speed_kph]):
        return None
    if not (0 <= humidity_percent <= 100) or uv_index < 0 or wind_speed_kph < 0:
        return None

    eff_temp = calculate_effective_temperature(temperature_c, humidity_percent, wind_speed_kph)
    score = 0
    category = "Unknown"
    male_clothing = []
    female_clothing = []
    accessories = []

    VERY_HOT_THRESHOLD = 30
    HOT_THRESHOLD = 25
    WARM_THRESHOLD = 20
    MILD_THRESHOLD = 15
    COOL_THRESHOLD = 10
    COLD_THRESHOLD = 5
    VERY_COLD_THRESHOLD = 0

    if eff_temp >= VERY_HOT_THRESHOLD:
        score = 1
        category = "Very Hot"
        male_clothing = ["Tank top / Vest", "Shorts (lightweight)", "Sandals / Flip-flops"]
        female_clothing = ["Tank top / Sundress", "Shorts / Skirt (lightweight)", "Sandals / Flip-flops"]
    elif eff_temp >= HOT_THRESHOLD:
        score = 3
        category = "Hot"
        male_clothing = ["T-shirt", "Shorts / Light Trousers (Linen/Cotton)", "Sneakers / Sandals"]
        female_clothing = ["T-shirt / Blouse", "Shorts / Skirt / Light Trousers", "Sneakers / Sandals"]
    elif eff_temp >= WARM_THRESHOLD:
        score = 5
        category = "Warm"
        male_clothing = ["T-shirt / Polo Shirt", "Jeans / Chinos", "Sneakers / Loafers"]
        female_clothing = ["T-shirt / Blouse", "Jeans / Trousers / Skirt", "Flats / Sneakers"]
        accessories.append("Light Jacket/Cardigan (optional, evenings)")
    elif eff_temp >= MILD_THRESHOLD:
        score = 7
        category = "Mild"
        male_clothing = ["Long-sleeve Shirt / T-shirt + Light Jumper/Hoodie", "Jeans / Chinos", "Closed Shoes / Sneakers"]
        female_clothing = ["Long-sleeve Top / Blouse + Cardigan/Light Jumper", "Jeans / Trousers", "Closed Shoes / Ankle Boots"]
        accessories.append("Light Jacket recommended")
    elif eff_temp >= COOL_THRESHOLD:
        score = 9
        category = "Cool"
        male_clothing = ["Jumper / Sweater / Fleece", "Jeans / Trousers", "Jacket", "Closed Shoes / Boots"]
        female_clothing = ["Jumper / Sweater / Fleece", "Jeans / Trousers", "Jacket / Coat", "Boots / Closed Shoes"]
        accessories.append("Scarf (optional)")
    elif eff_temp >= COLD_THRESHOLD:
        score = 11
        category = "Cold"
        male_clothing = ["Warm Jumper / Fleece", "Warm Trousers", "Warm Jacket / Coat", "Boots"]
        female_clothing = ["Warm Jumper / Fleece", "Warm Trousers / Jeans", "Warm Coat", "Boots"]
        accessories.extend(["Scarf", "Hat (optional)"])
    elif eff_temp >= VERY_COLD_THRESHOLD:
        score = 13
        category = "Very Cold"
        male_clothing = ["Base Layer (Thermals)", "Heavy Jumper / Fleece", "Insulated Coat", "Warm Trousers", "Winter Boots"]
        female_clothing = ["Base Layer (Thermals)", "Heavy Jumper / Fleece", "Insulated Coat", "Warm Trousers", "Winter Boots"]
        accessories.extend(["Warm Hat", "Gloves", "Scarf"])
    else:
        score = 15
        category = "Freezing"
        male_clothing = ["Heavy Base Layer (Thermals)", "Fleece Mid-layer", "Heavy Insulated Parka/Coat", "Insulated Trousers", "Heavy Winter Boots"]
        female_clothing = ["Heavy Base Layer (Thermals)", "Fleece Mid-layer", "Heavy Insulated Parka/Coat", "Insulated Trousers", "Heavy Winter Boots"]
        accessories.extend(["Warm Hat (covering ears)", "Insulated Gloves", "Neck Gaiter / Heavy Scarf"])

    if uv_index >= 3:
        accessories.append("Consider Sunscreen")
    if uv_index >= 6:
        accessories.extend(["Sunglasses recommended", "Hat recommended (wide-brimmed if very sunny)"])
    if wind_speed_kph > 30:
        accessories.append("Windproof outer layer recommended")
    if wind_speed_kph > 50:
        accessories.append("Secure hat if worn")

    accessories = sorted(list(set(accessories)))

    return {
        "clothing_score": score,
        "category": category,
        "effective_temp_c": round(eff_temp, 1),
        "recommendations": {
            "male": male_clothing,
            "female": female_clothing,
            "accessories": accessories
        }
    }
    # --- (End of recommendation logic) ---

@app.route('/get_recommendations', methods=['POST'])
def get_recommendations():
    data = request.json
    temp_c = data.get('temperature')
    humidity = data.get('humidity')
    uv_index = data.get('uv_index')
    wind_speed = data.get('wind_speed')

    # Basic validation
    if None in [temp_c, humidity, uv_index, wind_speed]:
         return jsonify({'error': 'Missing weather data fields'}), 400

    recommendation = get_clothing_recommendation(float(temp_c), float(humidity), float(uv_index), float(wind_speed))

    if recommendation:
        images = {}
        # Combine all items needing images
        clothing_items = set(recommendation['recommendations']['male'] +
                             recommendation['recommendations']['female'] +
                             recommendation['recommendations']['accessories'])

        for item in clothing_items:
             # Clean up item name for better search results (optional but helpful)
            query_item = item.split('/')[0].split('(')[0].strip()
            try:
                response = requests.get(
                    f'https://api.pexels.com/v1/search?query={query_item}&per_page=5',
                    headers={'Authorization': PEXELS_API_KEY},
                    timeout=10 # Add a timeout
                )
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

                photos = response.json().get('photos', [])
                images[item] = [photo['src']['medium'] for photo in photos if 'src' in photo and 'medium' in photo['src']]

            except requests.exceptions.RequestException as e:
                print(f"Pexels API error for '{query_item}': {e}") # Log the error server-side
                images[item] = [] # Keep it as an empty list on error

        recommendation['images'] = images
        return jsonify(recommendation)
    else:
        return jsonify({'error': 'Invalid input for recommendations'}), 400


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("test.html")

@app.route('/translate', methods=['POST'])
def translate():
    if request.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON data'}), 400

    text = data.get('text')
    target_lang = data.get('target_lang')

    if not text or not target_lang:
        return jsonify({'error': 'Missing text or target_lang'}), 400

    try:
        # Ensure language code format if necessary (e.g., 'zh-CN' vs 'zh')
        # The library might handle variations, but check its docs if issues arise.
        translator = GoogleTranslator(source='auto', target=target_lang)
        translated = translator.translate(text)
        return jsonify({'translated': translated})
    except Exception as e:
        print(f"Translation error: {e}") # Log the error server-side
        return jsonify({'error': f'Translation failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)