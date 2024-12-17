from sqlalchemy import Column, Integer, String, BigInteger
from db import Base

class TeamScore(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True)
    score = Column(BigInteger)
    teamName = Column(String(40))
    secret = Column(Integer)

    def __init__ (self, team, score, secret=0):
        self.teamName = team
        self.score = score
        self.secret = secret

    def __repr__ (self):
        return '<%s : %d>' % (self.teamName, self.score)
