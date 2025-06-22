import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_clients.fast_api_client_httpx import FastFaceitClientHttpx
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_detailed_bans():
    """Тестирует детальную обработку банов"""
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        logger.error("❌ FACEIT_API_KEY не найден в переменных окружения")
        return
        
    client = FastFaceitClientHttpx(api_key)
    
    # Steam ID игрока с активным баном (замените на реальный Steam ID)
    steam_id = "76561198376323869"  # Замените на реальный Steam ID
    
    try:
        logger.info(f"Тестируем детальную обработку банов для Steam ID: {steam_id}")
        
        # Получаем данные игрока
        player_data = await client.get_player_by_steam_id(steam_id)
        
        if player_data:
            logger.info("✅ Данные игрока получены успешно")
            
            # Проверяем баны
            bans = player_data.get("bans", [])
            logger.info(f"Найдено банов: {len(bans)}")
            
            for i, ban in enumerate(bans, 1):
                logger.info(f"\n--- Бан #{i} ---")
                logger.info(f"Причина: {ban.get('reason')}")
                logger.info(f"Дата выдачи: {ban.get('start_date')}")
                logger.info(f"Дата окончания: {ban.get('end_date')}")
                
                logger.info("✅ Бан обработан корректно")
            
            if not bans:
                logger.info("ℹ️ У игрока нет банов")
                
        else:
            logger.error("❌ Не удалось получить данные игрока")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

async def test_ban_processing_with_mock_data():
    """Тестирует обработку банов с мок-данными"""
    api_key = os.getenv("FACEIT_API_KEY", "dummy_key_for_testing")
    client = FastFaceitClientHttpx(api_key)
    
    # Мок-данные банов для тестирования
    mock_bans = [
        {
            "type": "VAC",
            "reason": "Smurfing",
            "starts_at": "2024-01-01T00:00:00Z",
            "ends_at": "2025-12-31T23:59:59Z"  # Активный бан (в будущем)
        },
        {
            "type": "Game",
            "reason": "Toxic behavior",
            "starts_at": 1704067200,  # Unix timestamp
            "ends_at": None  # Навсегда = активен
        },
        {
            "type": "Expired",
            "reason": "Old ban",
            "starts_at": "2023-01-01T00:00:00Z",
            "ends_at": "2023-12-31T23:59:59Z"  # Истекший бан
        },
        {
            "type": "Recent",
            "reason": "Recent ban",
            "starts_at": "2024-06-01T00:00:00Z",
            "ends_at": "2024-12-31T23:59:59Z"  # Активный бан
        }
    ]
    
    logger.info("Тестируем обработку мок-данных банов (только активные)...")
    
    processed_bans = client._process_bans(mock_bans)
    
    logger.info(f"Найдено активных банов: {len(processed_bans)}")
    
    for i, ban in enumerate(processed_bans, 1):
        logger.info(f"\n--- Активный бан #{i} ---")
        logger.info(f"Причина: {ban.get('reason')}")
        logger.info(f"Дата выдачи: {ban.get('start_date')}")
        logger.info(f"Дата окончания: {ban.get('end_date')}")

if __name__ == "__main__":
    print("🧪 Тестирование детальной обработки банов")
    print("=" * 50)
    
    # Сначала тестируем с мок-данными
    asyncio.run(test_ban_processing_with_mock_data())
    
    print("\n" + "=" * 50)
    print("Тестирование с реальными данными")
    
    # Тестируем с реальными данными
    asyncio.run(test_detailed_bans()) 