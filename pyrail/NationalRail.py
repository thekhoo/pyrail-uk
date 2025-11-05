class NationalRailClient:
    
    def __init__(self, token: str):
        self.token = token
        
    def hello(self):
        print("hello from the national rail client!")