import telebot
import os
import json
import random
from telebot import types


TOKEN = os.environ.get("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, "smoothe.json")

try:
    with open(file_path, 'r', encoding='utf-8') as f:
        smoothie_recipes = json.load(f)
except FileNotFoundError:
    print(f"Ошибка: Файл '{file_path}' не найден.")
    smoothie_recipes = {}
    

def create_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    fruit_button = types.InlineKeyboardButton("Фрукт", callback_data="fruit")
    additive_button = types.InlineKeyboardButton("Добавка", callback_data="additive")
    size_button = types.InlineKeyboardButton("Размер", callback_data="size")
    keyboard.add(fruit_button, additive_button, size_button)
    recommendation_button = types.InlineKeyboardButton("Хочу рекомендацию!", callback_data="recommendation")
    keyboard.add(recommendation_button)
    weight_recommendation_button = types.InlineKeyboardButton("Рекомендация по весу", callback_data="weight_recommendation")
    keyboard.add(weight_recommendation_button)

    return keyboard

@bot.callback_query_handler(func=lambda call: call.data == "weight_recommendation")
def weight_recommendation_callback(call):
    handle_weight_recommendation(call.message)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Выберите, какое смузи вы хотите:", reply_markup=create_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "fruit")
def fruit_callback(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for fruit in smoothie_recipes.get("fruits", []):
        keyboard.add(types.InlineKeyboardButton(fruit, callback_data=f"fruit_{fruit}"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                         text="Выберите фрукт:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "additive")
def additive_callback(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for additive in smoothie_recipes.get("additives", []):
        keyboard.add(types.InlineKeyboardButton(additive, callback_data=f"additive_{additive}"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                         text="Выберите добавку:", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "size")
def size_callback(call):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for size in smoothie_recipes.get("sizes", []):
        keyboard.add(types.InlineKeyboardButton(size, callback_data=f"size_{size}"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                         text="Выберите размер:", reply_markup=keyboard)

selected_params = {}
last_recommended_smoothie = None

@bot.callback_query_handler(func=lambda call: call.data.startswith("fruit_"))
def fruit_selected(call):
    fruit = call.data.split("_")[1]
    selected_params["fruit"] = fruit
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                         text=f"Вы выбрали фрукт: {fruit}\nВыберите добавку:", 
                         reply_markup=get_additive_keyboard())

def get_additive_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for additive in smoothie_recipes.get("additives", []):
        keyboard.add(types.InlineKeyboardButton(additive, callback_data=f"additive_{additive}"))
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data.startswith("additive_"))
def additive_selected(call):
    additive = call.data.split("_")[1]
    selected_params["additive"] = additive
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                         text=f"Вы выбрали добавку: {additive}\nВыберите размер:", 
                         reply_markup=get_size_keyboard())

def get_size_keyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for size in smoothie_recipes.get("sizes", []):
        keyboard.add(types.InlineKeyboardButton(size, callback_data=f"size_{size}"))
    return keyboard

@bot.callback_query_handler(func=lambda call: call.data.startswith("size_"))
def size_selected(call):
    size = call.data.split("_")[1]
    selected_params["size"] = size
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                         text=f"Вы выбрали размер: {size}")
    check_and_recommend(call.message.chat.id)

def check_and_recommend(chat_id):
    global last_recommended_smoothie

    if "fruit" in selected_params and "additive" in selected_params and "size" in selected_params:
        fruit = selected_params["fruit"]
        additive = selected_params["additive"]
        size = selected_params["size"]

        matching_smoothies = []
        for smoothie in smoothie_recipes.get("smoothies", []):
            if (smoothie["fruit"] == fruit and 
                additive in smoothie["additives"] and  
                smoothie["size"] == size):
                matching_smoothies.append(smoothie)

        if matching_smoothies:
            smoothie = random.choice(matching_smoothies)
            response = f"Ваш смузи: {smoothie['name']}\nРецепт: {smoothie['recipe']}"
            bot.send_message(chat_id, response)
            
            if "image" in smoothie:  
                bot.send_photo(chat_id, smoothie['image'])
                
            last_recommended_smoothie = smoothie
            selected_params.clear()
        else:
            bot.send_message(chat_id, "К сожалению, рецепт для выбранных параметров не найден.")
            selected_params.clear()

@bot.callback_query_handler(func=lambda call: call.data == "recommendation")
def recommend_smoothie(call):
    global last_recommended_smoothie

    if last_recommended_smoothie is None:
        bot.send_message(call.message.chat.id, "Сначала выберите смузи, чтобы я мог дать рекомендацию.")
        return

    available_smoothies = [s for s in smoothie_recipes.get("smoothies", []) if s != last_recommended_smoothie]

    if not available_smoothies:
        bot.send_message(call.message.chat.id, "Больше нет доступных смузи для рекомендации!")
        return

    recommended_smoothie = random.choice(available_smoothies)
    response = f"Рекомендую попробовать: {recommended_smoothie['name']}\nРецепт: {recommended_smoothie['recipe']}"
    bot.send_message(call.message.chat.id, response)
    if "photo" in recommended_smoothie:
        bot.send_photo(call.message.chat.id, recommended_smoothie['photo'])

    last_recommended_smoothie = recommended_smoothie

@bot.message_handler(func=lambda message: message.text.lower() == "еще")
def send_menu_again(message):
    bot.reply_to(message, "Выберите, какое смузи вы хотите:", reply_markup=create_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == "спасибо")
def send_gratitude(message):
    bot.reply_to(message, "Не за что!")

@bot.message_handler(commands=['recommend_by_weight'])
def handle_weight_recommendation(message):
    msg = bot.reply_to(message, "Введите ваш вес в кг (например: 70):")
    bot.register_next_step_handler(msg, process_weight_recommendation)

def process_weight_recommendation(message):
    try:
        weight = float(message.text)
        
        if weight <= 0 or weight > 300:
            bot.send_message(message.chat.id, "Пожалуйста, введите корректный вес от 1 до 300 кг.")
            return
        
        # Определяем категорию по весу
        if weight < 60:
            category = "набор массы"
            fruits = ["банан", "клубника"]
            additives = ["протеин"]
        elif 60 <= weight <= 90:
            category = "поддержание веса"
            fruits = ["банан", "клубника", "шпинат"]
            additives = ["протеин", "семена чиа"]
        else:
            category = "похудение"
            fruits = ["spinach", "strawberry"]
            additives = ["семена чиа", "имбирь"]
        
        # Ищем подходящие смузи
        recommended = []
        for smoothie in smoothie_recipes.get("smoothies", []):
            if (smoothie["fruit"] in fruits and 
                any(additive in smoothie["additives"] for additive in additives)):
                recommended.append(smoothie)
        
        if recommended:
            smoothie = random.choice(recommended)
            response = f"Рекомендация для веса {weight} кг ({category}):\n"
            response += f"🍹 {smoothie['name']}\nРецепт: {smoothie['recipe']}"
            bot.send_message(message.chat.id, response)
            if "image" in smoothie:
                bot.send_photo(message.chat.id, smoothie['image'])
        else:
            bot.send_message(message.chat.id, "К сожалению, не нашлось подходящих смузи.")
            
    except ValueError:
        bot.send_message(message.chat.id, "Пожалуйста, введите число (например: 70)")



print("Бот запущен...")
bot.infinity_polling()
