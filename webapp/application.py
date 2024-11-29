from app import application, db
from app.models import User, Post, Comment, FarmerData

# Shell context processor
@application.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'Comment': Comment, 'FarmerData': FarmerData}

# Main driver to run the application
if __name__ == "__main__":
    application.run(host="0.0.0.0", port=8080, debug=True)
