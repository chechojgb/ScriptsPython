from app.database.connection import init_db
from app.database.activity_repo import close_active_sessions
from app.tracker.tracker import track_activity, start_tracking
from datetime import date, datetime
import time




def main():
    # init_db()
    start_tracking()
    # close_active_sessions()
    # hoy = date.today()
    # print(hoy)
    
if __name__ == "__main__":
    main()