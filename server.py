from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import re

app = Flask(__name__)
CORS(app)  # Разрешаем запросы с любого сайта

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        token = data.get('token')
        image_base64 = data.get('image')

        if not token:
            return jsonify({'error': 'Нет токена'}), 400
        if not image_base64:
            return jsonify({'error': 'Нет изображения'}), 400

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'inputs': {
                'image': image_base64,
                'prompt': """Проанализируй лицо человека на фото. Оцени по шкале от 0 до 10 пять параметров:
1) Hunter eyes — насколько взгляд хищный, как у охотника (узкие, направленные, уверенные).
2) Prey eyes — насколько глаза похожи на глаза добычи (широкие, круглые, открытые, как у травоядных).
3) Rizz — способность к флирту, харизма, горячие разговоры, привлекательность для общения.
4) Aura — социальная значимость, положение в иерархии, насколько высокая аура в обществе.
5) Mogg — насколько ты круче других по внешности (доминантность, внешняя конкурентоспособность).
Верни только JSON: {"hunter": X, "prey": X, "rizz": X, "aura": X, "mogg": X}"""
            },
            'parameters': {
                'max_new_tokens': 200,
                'temperature': 0.1
            }
        }

        response = requests.post(
            'https://api-inference.huggingface.co/models/llava-hf/llava-1.5-7b-hf',
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 401:
            return jsonify({'error': 'Неверный токен'}), 401
        if response.status_code == 503:
            return jsonify({'error': 'Модель загружается, попробуйте через 10 секунд'}), 503

        result = response.json()
        text = result[0]['generated_text'] if isinstance(result, list) else result.get('generated_text', '')

        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            return jsonify({'error': 'Модель не вернула JSON'}), 500

        scores = json.loads(json_match.group())
        return jsonify(scores)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
