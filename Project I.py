import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt
import requests

class ProductInfoWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Product Info Scanner")
        self.setGeometry(100, 100, 375, 812)  # iPhone X resolution scaled down
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.label = QLabel('Enter Barcode or Food Name:', self)
        layout.addWidget(self.label)

        self.entry = QLineEdit(self)
        layout.addWidget(self.entry)

        self.button = QPushButton('Get Product Info', self)
        self.button.clicked.connect(self.on_click)
        layout.addWidget(self.button)

        self.result = QLabel('', self)
        self.result.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result)

        self.calories_label = QLabel('', self)
        self.calories_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.calories_label)

        self.nutrients_label = QLabel('', self)
        self.nutrients_label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.nutrients_label)

        self.setLayout(layout)

    def on_click(self):
        query = self.entry.text()
        if query.isdigit():
            product_info = self.get_product_info(query)
        else:
            product_info = self.search_usda_food(query)

        if product_info:
            product_name = product_info.get('product_name', 'N/A')
            nutri_score = product_info.get('nutrition_grades', 'N/A')
            nutriments = product_info.get('nutriments', {})
            nova_group = product_info.get('nova_group', 'N/A')

            self.result.setText(f"Product Name: {product_name}\nNutri-Score: {nutri_score}\nProcessed Food Level: {nova_group}")

            calories = nutriments.get('energy-kcal', 0)
            self.calories_label.setText(f"Calories: {calories}")

            nutrients_text = self.format_nutrients(nutriments)
            self.nutrients_label.setText(nutrients_text)

            self.update()
        else:
            self.result.setText("Product not found.")
            self.calories_label.setText("")
            self.nutrients_label.setText("")
            self.update()

    def get_product_info(self, barcode):
        # First try Open Food Facts API
        url = f"https://world.openfoodfacts.net/api/v2/product/{barcode}?fields=product_name,nutriscore_data,nutriments,nutrition_grades,nova_group"
        response = requests.get(url)
        data = response.json()
        if data['status'] == 1:
            return data['product']
        else:
            # Fallback to USDA API if not found
            product_info = self.search_usda_barcode(barcode)
            if not product_info:
                # Fallback to Nutritionix API if not found
                product_info = self.search_nutritionix_barcode(barcode)
            return product_info

    def search_usda_barcode(self, barcode):
        api_key = 'KDYl1AhaLLeiculekUziCbsKLgnAQTuWQ2a9yqYn'
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={barcode}&api_key={api_key}"
        response = requests.get(url)
        data = response.json()
        if data.get('foods'):
            food = data['foods'][0]
            return {
                'product_name': food.get('description', 'N/A'),
                'nutriments': self.extract_nutrients(food),
                'nutrition_grades': 'N/A',
                'nova_group': 'N/A'
            }
        return None

    def search_usda_food(self, name):
        api_key = 'KDYl1AhaLLeiculekUziCbsKLgnAQTuWQ2a9yqYn'
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={name}&api_key={api_key}"
        response = requests.get(url)
        data = response.json()
        if data.get('foods'):
            food = data['foods'][0]
            return {
                'product_name': food.get('description', 'N/A'),
                'nutriments': self.extract_nutrients(food),
                'nutrition_grades': 'N/A',
                'nova_group': 'N/A'
            }
        return None

    def search_nutritionix_barcode(self, barcode):
        api_key = '129cd1473db19c3d16463966d6f2aaed'
        app_id = '46383e01'
        url = f"https://trackapi.nutritionix.com/v2/search/item?upc={barcode}"
        headers = {
            'x-app-id': app_id,
            'x-app-key': api_key
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get('foods'):
            food = data['foods'][0]
            return {
                'product_name': food.get('food_name', 'N/A'),
                'nutriments': self.extract_nutritionix_nutrients(food),
                'nutrition_grades': 'N/A',
                'nova_group': 'N/A'
            }
        return None

    def extract_nutrients(self, food):
        nutriments = {}
        for nutrient in food.get('foodNutrients', []):
            name = nutrient.get('nutrientName', '').lower().replace(' ', '_')
            value = nutrient.get('value', 0)
            if value != 0:
                nutriments[name] = value
        return nutriments

    def extract_nutritionix_nutrients(self, food):
        nutriments = {}
        nutrients_map = {
            'nf_calories': 'energy-kcal',
            'nf_total_fat': 'fat',
            'nf_saturated_fat': 'saturated_fat',
            'nf_cholesterol': 'cholesterol',
            'nf_sodium': 'sodium',
            'nf_total_carbohydrate': 'carbohydrates',
            'nf_dietary_fiber': 'fiber',
            'nf_sugars': 'sugars',
            'nf_protein': 'proteins'
        }
        for key, value in nutrients_map.items():
            if key in food:
                nutriments[value] = food[key]
        return nutriments

    def format_nutrients(self, nutriments):
        formatted_text = "Nutrients:\n"
        keys_to_exclude = ['energy-kcal', 'energy', 'energy_unit', 'energy_value']
        grouped_nutrients = {}

        for key, value in nutriments.items():
            if key not in keys_to_exclude and value != 0:
                base_key = key.split('_')[0]
                if base_key not in grouped_nutrients:
                    grouped_nutrients[base_key] = {}
                grouped_nutrients[base_key][key] = value

        for base_key, values in grouped_nutrients.items():
            main_value = values.get(base_key, None)
            formatted_text += f"{base_key.capitalize()}: {main_value if main_value is not None else 'N/A'}\n"

        return formatted_text

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.calories_label.geometry()

        if rect.isValid() and self.calories_label.text():
            calories = int(self.calories_label.text().split(': ')[1])

            if calories < 100:
                color = QColor(0, 255, 0)  # Green for low calories
            elif 100 <= calories < 300:
                color = QColor(255, 165, 0)  # Orange for medium calories
            else:
                color = QColor(255, 0, 0)  # Red for high calories

            painter.setBrush(color)
            painter.drawEllipse(rect.x() + (rect.width() - 80) // 2, rect.y() + 20, 80, 80)

        nutri_score = self.result.text().split('Nutri-Score: ')[-1]
        if nutri_score:
            color = self.get_nutri_score_color(nutri_score)
            painter.setFont(QFont("Arial", 16, QFont.Bold))
            painter.setPen(color)
            painter.drawText(rect.x(), rect.y() + 130, f"Nutri-Score: {nutri_score}")

    def get_nutri_score_color(self, grade):
        color_map = {
            'a': QColor(0, 255, 0),
            'b': QColor(173, 255, 47),
            'c': QColor(255, 255, 0),
            'd': QColor(255, 140, 0),
            'e': QColor(255, 0, 0)
        }
        return color_map.get(grade.lower(), QColor(0, 0, 0))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ProductInfoWidget()
    ex.show()
    sys.exit(app.exec_())
