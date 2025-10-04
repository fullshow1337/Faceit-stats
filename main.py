from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import os
import uvicorn
import requests
import logging
import re
from dotenv import load_dotenv
import time
from datetime import datetime
from api_clients.fast_api_client_httpx import FastFaceitClientHttpx
from db import (
    init_database, 
    add_recent_search_to_db, 
    get_recent_searches_from_db, 
    init_test_data_db,
    RecentSearchDB
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Отключаем DEBUG логирование для HTTP клиентов
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Загружаем переменные окружения из .env файла
load_dotenv()

# Проверяем загрузку переменных окружения
faceit_api_key = os.getenv("FACEIT_API_KEY")
steam_api_key = os.getenv("STEAM_API_KEY")

if not faceit_api_key:
    logger.error("FACEIT_API_KEY not found in environment variables")
    raise ValueError("FACEIT_API_KEY is required. Please set it in .env file")

logger.info(f"FACEIT_API_KEY loaded: {'Yes' if faceit_api_key else 'No'}")
logger.info(f"STEAM_API_KEY loaded: {'Yes' if steam_api_key else 'No'}")

# Проверяем, что API ключи не пустые
if not faceit_api_key.strip():
    logger.error("FACEIT_API_KEY is empty")
    raise ValueError("FACEIT_API_KEY cannot be empty")

app = FastAPI(
    title="FACEIT API Wrapper",
    description="API для работы с FACEIT платформой",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настраиваем шаблоны
templates = Jinja2Templates(directory="templates")

# Кэширование результатов поиска игроков (5 минут)
player_cache = {}
CACHE_DURATION = 300  # 5 минут в секундах

# Константы
MAX_RECENT_SEARCHES = 10

class RecentSearch(BaseModel):
    """Модель для хранения информации о недавнем запросе"""
    steam_id: str
    nickname: str
    avatar: Optional[str] = None
    level: Optional[int] = None
    country: Optional[str] = None
    has_bans: bool = False
    timestamp: datetime
    success: bool

async def add_recent_search(steam_id: str, nickname: str = None, avatar: str = None, level: int = None, country: str = None, has_bans: bool = False, success: bool = True):
    """Добавляет новый запрос в историю в базу данных"""
    try:
        await add_recent_search_to_db(
            steam_id=steam_id,
            nickname=nickname,
            avatar=avatar,
            level=level,
            country=country,
            has_bans=has_bans,
            success=success
        )
        logger.info(f"Added recent search to database: steam_id={steam_id}, nickname={nickname}")
    except Exception as e:
        logger.error(f"Failed to add recent search to database: {e}")

def get_cached_player(steam_id: str):
    """Получает кэшированного игрока"""
    if steam_id in player_cache:
        cached_time, cached_data = player_cache[steam_id]
        if time.time() - cached_time < CACHE_DURATION:
            logger.info(f"Using cached data for Steam ID: {steam_id}")
            return cached_data
        else:
            del player_cache[steam_id]
    return None

def cache_player(steam_id: str, data: dict):
    """Кэширует данные игрока"""
    player_cache[steam_id] = (time.time(), data)
    logger.info(f"Cached data for Steam ID: {steam_id}")

# Модели данных
class SteamUrlRequest(BaseModel):
    steam_url: str

def get_steam_id_from_url(steam_url: str) -> str:
    """Извлекает Steam ID из URL профиля Steam"""
    logger.info(f"Processing Steam URL: {steam_url}")
    
    # Паттерны для различных форматов Steam URL
    patterns = [
        r'steamcommunity\.com/profiles/(\d+)',  # Профиль по Steam ID
        r'steamcommunity\.com/id/([^/]+)',      # Профиль по кастомному ID
    ]
    
    for pattern in patterns:
        match = re.search(pattern, steam_url)
        if match:
            if pattern.endswith(r'(\d+)'):
                steam_id = match.group(1)
                logger.info(f"Found Steam ID directly: {steam_id}")
                return steam_id
            else:
                # Для кастомного ID нужно сделать дополнительный запрос к Steam API
                custom_id = match.group(1)
                logger.info(f"Found custom ID: {custom_id}, querying Steam API")
                
                steam_api_key = os.getenv("STEAM_API_KEY")
                if not steam_api_key:
                    logger.error("STEAM_API_KEY not found in environment variables")
                    raise HTTPException(
                        status_code=500,
                        detail="STEAM_API_KEY not configured"
                    )
                
                api_url = f'https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key={steam_api_key}&vanityurl={custom_id}'
                logger.info(f"Querying Steam API: {api_url}")
                
                try:
                    response = requests.get(api_url)
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get('response', {}).get('success') == 1:
                        steam_id = data['response']['steamid']
                        logger.info(f"Successfully resolved custom ID to Steam ID: {steam_id}")
                        return steam_id
                    else:
                        logger.error(f"Failed to resolve custom ID: {data.get('response', {}).get('message', 'Unknown error')}")
                        raise HTTPException(
                            status_code=404,
                            detail=f"Could not resolve Steam ID for custom URL: {custom_id}"
                        )
                except requests.RequestException as e:
                    logger.error(f"Error querying Steam API: {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error querying Steam API: {str(e)}"
                    )
    
    logger.error(f"Could not extract Steam ID from URL: {steam_url}")
    raise HTTPException(
        status_code=400,
        detail="Invalid Steam URL format. Please provide a valid Steam profile URL."
    )

@app.get("/")
async def index(request: Request):
    """Главная страница"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/privacy")
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/terms")
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

@app.get("/{steam_id}")
async def player_page(steam_id: str, request: Request):
    """Страница конкретного игрока по Steam ID"""
    # Проверяем, что steam_id похож на Steam ID (17 цифр)
    if not steam_id.isdigit() or len(steam_id) != 17:
        raise HTTPException(status_code=404, detail="Invalid Steam ID")
    
    # Возвращаем ту же страницу, но с предзаполненным Steam ID
    return templates.TemplateResponse("player.html", {
        "request": request,
        "steam_id": steam_id
    })

@app.get("/api/recent-searches")
async def get_recent_searches():
    """Получить последние 10 запросов из базы данных"""
    try:
        searches = await get_recent_searches_from_db(limit=MAX_RECENT_SEARCHES)
        return {
            "searches": [
                {
                    "steam_id": search.steam_id,
                    "nickname": search.nickname,
                    "avatar": search.avatar,
                    "level": search.level,
                    "country": search.country,
                    "has_bans": search.has_bans,
                    "timestamp": search.timestamp.isoformat(),
                    "success": search.success,
                    "time_ago": get_time_ago(search.timestamp)
                }
                for search in searches
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get recent searches from database: {e}")
        return {"searches": []}

def get_time_ago(timestamp: datetime) -> dict:
    """Возвращает структурированное время для переводов"""
    now = datetime.now()
    diff = now - timestamp
    
    total_seconds = diff.total_seconds()
    
    if total_seconds < 60:
        return {"key": "just_now", "value": None}
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        return {"key": "minutes_ago", "value": minutes}
    elif total_seconds < 86400:
        hours = int(total_seconds // 3600)
        return {"key": "hours_ago", "value": hours}
    else:
        days = diff.days
        return {"key": "days_ago", "value": days}

@app.post("/find-faceit-by-steam")
async def find_faceit_by_steam(request: SteamUrlRequest):
    """Поиск игрока FACEIT по Steam URL"""
    start_time = time.time()
    
    try:
        # Валидация входных данных
        if not request.steam_url or not request.steam_url.strip():
            logger.warning("Empty Steam URL provided")
            raise HTTPException(
                status_code=400,
                detail="Steam URL cannot be empty"
            )
        
        # Извлекаем Steam ID из URL
        steam_id = get_steam_id_from_url(request.steam_url)
        logger.info(f"Search for Steam ID: {steam_id}")
        
        # Проверяем кэш
        cached_result = get_cached_player(steam_id)
        if cached_result:
            cached_result["processing_time"] = time.time() - start_time
            cached_result["source"] = "cache"
            logger.info(f"Returning cached result for Steam ID: {steam_id}")
            return cached_result
        
        # Используем быстрый клиент
        api_key = os.getenv("FACEIT_API_KEY")
        if not api_key:
            logger.error("FACEIT_API_KEY not found during request")
            raise HTTPException(status_code=500, detail="FACEIT API key not configured")
        
        async with FastFaceitClientHttpx(api_key) as client:
            result = await client.get_complete_player_data(steam_id)
            
            if not result:
                logger.warning(f"Player not found on FACEIT for Steam ID: {steam_id}")
                # Добавляем неуспешный поиск в историю
                await add_recent_search(steam_id, f"Player_{steam_id[-4:]}", None, None, None, False, False)
                raise HTTPException(
                    status_code=404,
                    detail="Player not found on FACEIT"
                )
            
            # Добавляем информацию об источнике
            result["source"] = "api"
            result["processing_time"] = time.time() - start_time
            
            # Кэшируем результат
            cache_player(steam_id, result)

            # Удалено логирование снимков ELO по запросу пользователя
            
            # Добавляем в историю поисков
            nickname = result.get('nickname', f"Player_{steam_id[-4:]}")
            avatar = result.get('avatar')
            
            # Получаем уровень из разных источников
            level = None
            if result.get('faceit') and result['faceit'].get('level') is not None:
                level = result['faceit']['level']
            elif result.get('games') and result['games'].get('cs2') and result['games']['cs2'].get('skill_level') is not None:
                level = result['games']['cs2']['skill_level']
            
            # Получаем страну
            country = result.get('country')
            
            # Проверяем наличие банов
            has_bans = bool(result.get('bans') and len(result.get('bans', [])) > 0)
            
            await add_recent_search(steam_id, nickname, avatar, level, country, has_bans, True)
            
            logger.info(f"Search completed in {result['processing_time']:.2f} seconds for Steam ID: {steam_id}")
            return result
            
    except HTTPException as e:
        logger.error(f"HTTP error in search: {e.status_code} - {e.detail}")
        raise e
    except ValueError as e:
        logger.error(f"Validation error in search: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )

@app.post("/extension/find-faceit-by-steam")
async def find_faceit_by_steam_extension(request: SteamUrlRequest):
    """Поиск игрока FACEIT по Steam URL для расширения браузера (без логирования в ленту)"""
    start_time = time.time()
    
    try:
        # Валидация входных данных
        if not request.steam_url or not request.steam_url.strip():
            logger.warning("Empty Steam URL provided")
            raise HTTPException(
                status_code=400,
                detail="Steam URL cannot be empty"
            )
        
        # Извлекаем Steam ID из URL
        steam_id = get_steam_id_from_url(request.steam_url)
        logger.info(f"Extension search for Steam ID: {steam_id}")
        
        # Проверяем кэш
        cached_result = get_cached_player(steam_id)
        if cached_result:
            cached_result["processing_time"] = time.time() - start_time
            cached_result["source"] = "cache"
            logger.info(f"Returning cached result for Steam ID: {steam_id}")
            return cached_result
        
        # Используем быстрый клиент
        api_key = os.getenv("FACEIT_API_KEY")
        if not api_key:
            logger.error("FACEIT_API_KEY not found during request")
            raise HTTPException(status_code=500, detail="FACEIT API key not configured")
        
        async with FastFaceitClientHttpx(api_key) as client:
            result = await client.get_complete_player_data(steam_id)
            
            if not result:
                logger.warning(f"Player not found on FACEIT for Steam ID: {steam_id}")
                raise HTTPException(
                    status_code=404,
                    detail="Player not found on FACEIT"
                )
            
            # Добавляем информацию об источнике
            result["source"] = "extension"
            result["processing_time"] = time.time() - start_time
            
            # Кэшируем результат
            cache_player(steam_id, result)
            
            # НЕ добавляем в историю поисков для расширения
            
            logger.info(f"Extension search completed in {result['processing_time']:.2f} seconds for Steam ID: {steam_id}")
            return result
            
    except HTTPException as e:
        logger.error(f"HTTP error in extension search: {e.status_code} - {e.detail}")
        raise e
    except ValueError as e:
        logger.error(f"Validation error in extension search: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in extension search: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error. Please try again later."
        )

# Добавляем middleware для отключения кэширования
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

async def startup_event():
    """Инициализация при запуске приложения"""
    await init_database()
    await init_test_data_db()
    logger.info("Application startup completed")

# Добавляем обработчик события запуска
@app.on_event("startup")
async def startup():
    await startup_event()

if __name__ == "__main__":
    # Определяем окружение
    environment = os.getenv("ENVIRONMENT", "development")
    
    if environment == "production":
        # Настройки для продакшена
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=int(os.getenv("PORT", 8000)), 
            reload=False,
            workers=int(os.getenv("WORKERS", 1)),
            log_level="info"
        )
    else:
        # Настройки для разработки
        uvicorn.run(
            "main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
