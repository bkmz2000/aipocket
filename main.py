import requests
import time
import json
import pickle
import os

TOKEN = "8091232579:AAFsDp6fNNX9fl1NDTcI9xEzHK7UX8Qs8GM"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"
admins = set()

def get_updates(offset=None):
    url = f"{BASE_URL}getUpdates"
    params = {"offset": offset} if offset else {}
    response = requests.get(url, params=params)
    return response.json()

def send_message(chat_id, text):
    url = f"{BASE_URL}sendMessage"
    data = {"chat_id": chat_id, "text": text}
    requests.post(url, data=data)

def select_role(chat_id, text):
    url = f"{BASE_URL}sendMessage"
    keyboard = {
        "inline_keyboard": [
            [{"text": "I am a user", "callback_data": "user"}],
            [{"text": "I am an admin", "callback_data": "admin"}]
        ]
    }
    data = {"chat_id": chat_id, "text": text, "reply_markup": json.dumps(keyboard)}
    requests.post(url, data=data)

def main():
    state = {"update_id": 0, "admins": set()}
    if os.path.exists("state"):
        with open("state", "rb") as f:
            state = pickle.load(f)

    update_id = state["update_id"]
    admins = state["admins"]

    user_messages = []
    responses = set()

    while True:
        updates = get_updates(update_id)
        
        if "result" in updates:
            for item in updates["result"]:
                update_id = item["update_id"] + 1
                chat_id = item.get("message", {}).get("chat", {}).get("id")
                text = item.get("message", {}).get("text", "")
                
                if text == "/start":
                    select_role(chat_id, "Select your role:")
                elif "callback_query" in item:
                    callback_data = item["callback_query"]["data"]
                    chat_id = item["callback_query"]["message"]["chat"]["id"]
                    if callback_data == "user":
                        if chat_id in admins:
                            admins.remove(chat_id)
                        send_message(chat_id, "You can send messages now.")
                    elif callback_data == "admin":
                        admins.add(chat_id)
                        send_message(chat_id, "You will receive user messages every minute.")
                elif chat_id in admins and "reply_to_message" in updates["result"][0]["message"]:
                    user_id = updates["result"][0]["message"]["from"]["id"]
                    responses.add((user_id, text))
                else:
                    if chat_id not in admins:
                        user_messages.append((chat_id, text))
                        send_message(chat_id, "Message sent to admins.")

        if user_messages:
            if admins:
                for _, text in user_messages:
                    for admin_id in admins:
                        send_message(admin_id, text)
                user_messages = []

        if responses:
            new = responses.copy()
            for user_id, text in responses:
                if user_id not in admins:
                    send_message(user_id, text)
                    new.remove((user_id, text))
            responses = new

        pickle.dump({"update_id": update_id, "admins": admins}, open("state", "wb"))

        print(updates)

if __name__ == "__main__":
    main()
