import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Получаем API ключ
FACEIT_API_KEY = os.getenv("FACEIT_API_KEY")
if not FACEIT_API_KEY:
    raise ValueError("FACEIT_API_KEY not found in environment variables")

# Базовый URL для API
BASE_URL = "https://open.faceit.com/data/v4"

# Заголовки для запросов
headers = {
    "Authorization": f"Bearer {FACEIT_API_KEY}"
}

def safe_api_call(url, headers):
    """Безопасный вызов API с обработкой ошибок"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling {url}: {str(e)}")
        if hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text}")
        return None

def get_player_info(nickname):
    """Получает основную информацию о игроке"""
    url = f"{BASE_URL}/players?nickname={nickname}"
    return safe_api_call(url, headers)

def get_player_stats(player_id):
    """Получает статистику игрока"""
    url = f"{BASE_URL}/players/{player_id}/stats/cs2"
    return safe_api_call(url, headers)

def get_player_matches(player_id, offset=0, limit=20):
    """Получает историю матчей игрока"""
    url = f"{BASE_URL}/players/{player_id}/history?game=cs2&offset={offset}&limit={limit}"
    return safe_api_call(url, headers)

def get_player_bans(player_id):
    """Получает информацию о банах игрока"""
    url = f"{BASE_URL}/players/{player_id}/bans"
    return safe_api_call(url, headers)

def get_player_infractions(player_id):
    """Получает информацию о нарушениях игрока"""
    url = f"{BASE_URL}/players/{player_id}/infractions"
    return safe_api_call(url, headers)

def get_player_tournaments(player_id):
    """Получает информацию о турнирах игрока"""
    url = f"{BASE_URL}/players/{player_id}/tournaments"
    return safe_api_call(url, headers)

def get_player_teams(player_id):
    """Получает информацию о командах игрока"""
    url = f"{BASE_URL}/players/{player_id}/teams"
    return safe_api_call(url, headers)

def get_player_friends(player_id):
    """Получает список друзей игрока"""
    url = f"{BASE_URL}/players/{player_id}/friends"
    return safe_api_call(url, headers)

def get_player_achievements(player_id):
    """Получает достижения игрока"""
    url = f"{BASE_URL}/players/{player_id}/achievements"
    return safe_api_call(url, headers)

def get_all_player_data(nickname):
    """Получает всю доступную информацию о игроке"""
    try:
        # Получаем основную информацию
        player_info = get_player_info(nickname)
        if not player_info:
            print(f"Could not get basic info for player {nickname}")
            return None
            
        player_id = player_info.get('player_id')
        print(f"Got player ID: {player_id}")
        
        # Собираем все данные
        all_data = {
            "basic_info": player_info,
            "stats": get_player_stats(player_id),
            "matches": get_player_matches(player_id),
            "bans": get_player_bans(player_id),
            "infractions": get_player_infractions(player_id),
            "tournaments": get_player_tournaments(player_id),
            "teams": get_player_teams(player_id),
            "friends": get_player_friends(player_id),
            "achievements": get_player_achievements(player_id)
        }
        
        # Сохраняем данные в файл для анализа
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"player_data_{nickname}_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        print(f"All data saved to {filename}")
        return all_data
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

if __name__ == "__main__":
    # Тестируем на примере игрока
    nickname = "MegaRush--"  # Замените на нужный никнейм
    data = get_all_player_data(nickname)
    
    if data:
        print("\nBasic Info:")
        print(json.dumps(data['basic_info'], indent=2, ensure_ascii=False))
        
        print("\nBans:")
        print(json.dumps(data['bans'], indent=2, ensure_ascii=False))
        
        print("\nInfractions:")
        print(json.dumps(data['infractions'], indent=2, ensure_ascii=False)) 