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

async def test_real_bans():
    """Тестирует получение реальных банов"""
    api_key = os.getenv("FACEIT_API_KEY")
    if not api_key:
        logger.error("❌ FACEIT_API_KEY не найден в переменных окружения")
        return
        
    # Steam ID для тестирования
    steam_id = "76561199765748683"
    
    try:
        logger.info(f"Тестируем получение банов для Steam ID: {steam_id}")
        
        # Используем контекстный менеджер для правильной инициализации клиента
        async with FastFaceitClientHttpx(api_key) as client:
            # Сначала проверим, существует ли игрок
            logger.info("Проверяем существование игрока...")
            player_data = await client.get_player_by_steam_id(steam_id)
            
            if not player_data:
                logger.error("❌ Игрок не найден на FACEIT")
                return
                
            logger.info("✅ Игрок найден на FACEIT")
            logger.info(f"Player ID: {player_data.get('player_id')}")
            logger.info(f"Nickname: {player_data.get('nickname')}")
            
            # Получаем полные данные игрока
            logger.info("Получаем полные данные игрока...")
            complete_data = await client.get_complete_player_data(steam_id)
            
            if complete_data:
                logger.info("✅ Полные данные игрока получены успешно")
                
                # Проверяем баны
                bans = complete_data.get("bans", [])
                logger.info(f"Найдено банов в полных данных: {len(bans)}")
                
                if bans:
                    for i, ban in enumerate(bans, 1):
                        logger.info(f"\n--- Бан #{i} ---")
                        logger.info(f"Причина: {ban.get('reason')}")
                        logger.info(f"Дата выдачи: {ban.get('start_date')}")
                        logger.info(f"Дата окончания: {ban.get('end_date')}")
                else:
                    logger.info("ℹ️ У игрока нет активных банов")
                
                # Также проверим напрямую через API банов
                logger.info("\n" + "="*50)
                logger.info("Проверяем напрямую через API банов...")
                
                player_id = complete_data.get("player_id")
                if player_id:
                    raw_bans = await client.get_player_bans(player_id)
                    logger.info(f"Найдено банов через API: {len(raw_bans)}")
                    
                    if raw_bans:
                        for i, ban in enumerate(raw_bans, 1):
                            logger.info(f"\n--- Сырой бан #{i} ---")
                            logger.info(f"Полные данные: {ban}")
                    else:
                        logger.info("ℹ️ API не вернул банов")
                else:
                    logger.error("❌ Не удалось получить player_id")
            else:
                logger.error("❌ Не удалось получить полные данные игрока")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Тестирование реальных банов")
    print("=" * 50)
    
    asyncio.run(test_real_bans()) 