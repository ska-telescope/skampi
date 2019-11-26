class User:

    def __init__(self,id,username,name,avatarUrl):
        self.id = id
        self.username = username
        self.name = name
        self.avatarUrl = avatarUrl
        

    def toDB(self):
        return {
            "username": self.username,
            "name": self.name,
            "avatarUrl": self.avatarUrl
        }