from database import SessionLocal, engine
from models import Base
from analytics import calculate_sleep_debt_impact
from seed import seed_data

Base.metadata.create_all(bind=engine)
db = SessionLocal()
seed_data()
res = calculate_sleep_debt_impact(1, db)
print(res)
