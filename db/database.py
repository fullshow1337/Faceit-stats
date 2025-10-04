from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

# Настройка базы данных
DATABASE_URL = "sqlite+aiosqlite:///./recent_searches.db"

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class RecentSearchDB(Base):
    """Модель для таблицы recent_searches в БД"""
    __tablename__ = "recent_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    steam_id = Column(String(17), nullable=False, index=True)
    nickname = Column(String(100), nullable=False)
    avatar = Column(Text, nullable=True)
    level = Column(Integer, nullable=True)
    country = Column(String(2), nullable=True)
    has_bans = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.now, index=True)
    success = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<RecentSearchDB(id={self.id}, steam_id={self.steam_id}, nickname={self.nickname})>"


async def init_database():
    """Инициализация базы данных - создание таблиц"""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Удалены вспомогательные сущности для снимков ELO по запросу пользователя

async def add_recent_search_to_db(steam_id: str, nickname: str = None, avatar: str = None, 
                                  level: int = None, country: str = None, has_bans: bool = False, 
                                  success: bool = True):
    """Добавляет новый поиск в базу данных"""
    try:
        async with async_session_maker() as session:
            # Проверяем, есть ли уже запись с таким steam_id
            # Если есть, обновляем её, иначе создаем новую
            from sqlalchemy import select
            
            result = await session.execute(
                select(RecentSearchDB).where(RecentSearchDB.steam_id == steam_id)
            )
            existing_search = result.scalar_one_or_none()
            
            if existing_search:
                # Обновляем существующую запись
                existing_search.nickname = nickname or existing_search.nickname
                existing_search.avatar = avatar or existing_search.avatar
                existing_search.level = level if level is not None else existing_search.level
                existing_search.country = country or existing_search.country
                existing_search.has_bans = has_bans
                existing_search.timestamp = datetime.now()
                existing_search.success = success
                logger.info(f"Updated existing search for steam_id: {steam_id}")
            else:
                # Создаем новую запись
                new_search = RecentSearchDB(
                    steam_id=steam_id,
                    nickname=nickname or f"Player_{steam_id[-4:]}",
                    avatar=avatar,
                    level=level,
                    country=country,
                    has_bans=has_bans,
                    timestamp=datetime.now(),
                    success=success
                )
                session.add(new_search)
                logger.info(f"Added new search for steam_id: {steam_id}")
            
            await session.commit()
            
            # Ограничиваем количество записей (оставляем только последние 50)
            await cleanup_old_searches(session)
            
    except Exception as e:
        logger.error(f"Error adding search to database: {e}")
        raise

async def cleanup_old_searches(session: AsyncSession, max_records: int = 50):
    """Удаляет старые записи, оставляя только последние max_records"""
    try:
        from sqlalchemy import select, delete
        
        # Получаем общее количество записей
        count_result = await session.execute(select(RecentSearchDB))
        total_count = len(count_result.all())
        
        if total_count > max_records:
            # Получаем ID записей, которые нужно удалить (все кроме последних max_records)
            subquery = select(RecentSearchDB.id).order_by(RecentSearchDB.timestamp.desc()).limit(max_records)
            delete_query = delete(RecentSearchDB).where(RecentSearchDB.id.notin_(subquery))
            
            result = await session.execute(delete_query)
            await session.commit()
            
            deleted_count = result.rowcount
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old search records")
                
    except Exception as e:
        logger.error(f"Error cleaning up old searches: {e}")

async def get_recent_searches_from_db(limit: int = 10) -> list[RecentSearchDB]:
    """Получает последние поиски из базы данных"""
    try:
        async with async_session_maker() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(RecentSearchDB)
                .order_by(RecentSearchDB.timestamp.desc())
                .limit(limit)
            )
            searches = result.scalars().all()
            logger.info(f"Retrieved {len(searches)} recent searches from database")
            return list(searches)
            
    except Exception as e:
        logger.error(f"Error getting recent searches from database: {e}")
        return []

async def init_test_data_db():
    """Инициализирует тестовые данные в базе данных"""
    try:
        async with async_session_maker() as session:
            from sqlalchemy import select
            
            # Проверяем, есть ли уже данные
            result = await session.execute(select(RecentSearchDB))
            existing_count = len(result.all())
            
            if existing_count == 0:
                # Добавляем одну тестовую запись с реальным пользователем
                test_search = RecentSearchDB(
                    steam_id='76561198003886164',
                    nickname='fullshow',
                    avatar=None,
                    level=10,
                    country='JP',
                    has_bans=False,
                    timestamp=datetime.now(),
                    success=True
                )
                
                session.add(test_search)
                await session.commit()
                logger.info("Added 1 test search entry to database (fullshow)")
            else:
                logger.info(f"Database already contains {existing_count} search entries")
                
    except Exception as e:
        logger.error(f"Error initializing test data: {e}") 