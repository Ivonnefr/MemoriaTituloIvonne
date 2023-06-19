from main import app, db

with app.app_context():
    db.create_all()
    db.session.commit()
