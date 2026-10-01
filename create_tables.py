from database.base import Base
from database.connection import engine

from models.user import User
from models.notification import Notification
from models.user_preference import UserPreference
from models.user_tender_preference import UserTenderPreference
from models.tender import Tender
from models.tender_corrigendum import TenderCorrigendum
from models.corrigendum_notification import CorrigendumNotification


Base.metadata.create_all(bind=engine)

print("Database tables created successfully.")