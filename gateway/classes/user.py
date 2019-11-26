class User:
    def __init__(self, user_id, firstname):
        self.user_id = user_id
        self.firstname = firstname
        self.is_anonymous = False
        self.is_active = True
        self.is_authenticated = False
        self.is_admin = False

    def get_id(self):
        return self.user_id
