from dao.mysql_connection import MySqlConection
import dao.account_profiles as profiles
import dao.account_profiles_metrics as metrics

def insert():
    db = MySqlConection()
    
    if db:
        # コネクト
        db.connect()
        
        # Profile data example
        profile_data = (
            "b3d2f73d-4b8c-47fb-85c3-cd571287754b",
            "https://p16-sign-va.tiktokcdn.com/tos-maliva-avt-0068/188d468fc1de3f328250ea0c96e98f8b~c5_100x100.webp?x-expires=1628060400&x-signature=BnPoX8rWsYZZ%2BtyzCoWanxYdRyg%3D",
            "la_flama_blanca",
            "Display Name",
            1124,
            '[{"percentage": 0.1797, "country": "MY"}, {"percentage": 0.5996, "country": "TW"}, {"percentage": 0.0629, "country": "VN"}]',
            '[{"percentage": 0.6031, "gender": "Female"}, {"percentage": 0.1685, "gender": "Male"}, {"percentage": 0.2283, "gender": "Other"}]',
            "admin"
        )
        profiles.insert_business_profile(db.cursor, profile_data)
        
        # Metrics data example
        metrics_data = [
            ("b3d2f73d-4b8c-47fb-85c3-cd571287754b", "2024-05-25", 4, 10, 1126, 4, 0, 26, "admin"),
            ("b3d2f73d-4b8c-47fb-85c3-cd571287754b", "2024-05-26", 6, 15, 312, 0, 0, 15, "admin"),
            ("b3d2f73d-4b8c-47fb-85c3-cd571287754b", "2024-05-27", 8, 20, 283, 0, 0, 19, "admin")
        ]
        metrics.insert_business_metrics(db.cursor, metrics_data)
        
        # コミット
        db.commit()
        
        # クローズ
        db.close()

def update():
    db = MySqlConection()
    
    if db:
        # コネクト
        db.connect()
        
        # Updating example profile data
        updated_profile_data = (
            "https://new_profile_image_url.com",
            "new_username",
            "New Display Name",
            2000,
            '[{"percentage": 0.5, "country": "US"}, {"percentage": 0.5, "country": "CA"}]',
            '[{"percentage": 0.5, "gender": "Female"}, {"percentage": 0.5, "gender": "Male"}]',
            "admin",
            "b3d2f73d-4b8c-47fb-85c3-cd571287754b"
        )
        profiles.update_business_profile(db.cursor, updated_profile_data)
        
        # Updating example metrics data
        updated_metric_data = (10, 25, 1300, 5, 1, 30, "admin", "b3d2f73d-4b8c-47fb-85c3-cd571287754b", "2024-05-25")
        metrics.update_business_metrics(db.cursor, updated_metric_data)
        
        # コミット
        db.commit()
        
        # クローズ
        db.close()

if __name__ == "__main__":
    insert()
    
    # update()
        