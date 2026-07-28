from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# اسم ومسار قاعدة البيانات (راح ينشئ ملف اسمه supermarket.db بنفس المجلد)
SQLALCHEMY_DATABASE_URL = "sqlite:///./supermarket.db"

# إعداد المحرك، و (check_same_thread=False) ضرورية جداً حتى FastAPI يكدر يقرا ويكتب براحته
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# دالة لفتح وإغلاق الاتصال بقاعدة البيانات مع كل طلب يوصل للسيرفر
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
