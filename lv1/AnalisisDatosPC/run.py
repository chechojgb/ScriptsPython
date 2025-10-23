from app.database.connection import init_db
from app.tracker.tracker import track_activity
from datetime import date, datetime

def main():
    init_db()
    # track_activity()
    
    # hoy = date.today()
    # print(hoy)
    
if __name__ == "__main__":
    main()