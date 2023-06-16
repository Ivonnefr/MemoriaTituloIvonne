from main import db

db.create_all()
db.session.commit()
