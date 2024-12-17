from redis import StrictRedis
from flask import Flask, render_template, request, redirect
from datetime import datetime, timedelta
import random

# Hardcode Redis connection settings
REDIS_HOST = 'localhost'  # Change to your Redis server host
REDIS_PORT = 6379  # Redis default port, change if necessary
REDIS_PASSWORD = ''  # Provide password if required
REDIS_SSL = False  # Set to True if Redis requires SSL (e.g., Azure Redis)

# Set up Redis connection with hardcoded settings
r = StrictRedis(
    host='manleytestapp-cache.redis.cache.windows.net',
    port=6380,
    password='1JlboCFjYtRqWV3DYogrPdzf0msYGOjPcAzCaIF3h6U=',
    ssl=True
)

app = Flask(__name__)

valid_teams = ["bob", "jerry", "smith"]
BLOCK_TIME = 5  # Time in seconds for the block (5 seconds for testing)

@app.route("/<teamname>/plus1")
def onepoint(teamname):
    if teamname in valid_teams:
        r.incrby(f"score:{teamname}", 1)
    return redirect("/")

@app.route("/<teamname>/minus1")
def subonepoint(teamname):
    if teamname in valid_teams:
        r.incrby(f"score:{teamname}", -1)
    return redirect("/")

@app.route("/<teamname>/plus5")
def fivepoint(teamname):
    if teamname in valid_teams:
        r.incrby(f"score:{teamname}", 5)
    return redirect("/")

@app.route("/<teamname>/plus50")
def fiftypoint(teamname):
    provided_secret = request.args.get('secret')
    new_secret = random.randrange(100)
    expected_secret = r.get(f"secret:{teamname}")
    if expected_secret is None or int(expected_secret) != int(provided_secret):
        r.set(f"secret:{teamname}", new_secret)
        return redirect("/")

    r.set(f"secret:{teamname}", new_secret)
    if teamname in valid_teams:
        r.incrby(f"score:{teamname}", 50)
    return redirect("/")

@app.route("/<teamname>/votefor")
def votefor(teamname):
    secret = random.randrange(100)
    r.set(f"secret:{teamname}", secret)
    return render_template("vote.html", TEAMNAME=teamname, SECRET=secret)

@app.route("/<teamname>/subtractfor")
def subtractfor(teamname):
    secret = random.randrange(100)
    r.set(f"secret:{teamname}", secret)
    return render_template("subtract.html", TEAMNAME=teamname, SECRET=secret)

@app.route("/<teamname>/Block")
def block(teamname):
    blocked_until = datetime.now() + timedelta(seconds=BLOCK_TIME)
    r.set(f"blocked_until:{teamname}", blocked_until.timestamp())  # Store the block expiration timestamp in Redis
    return redirect("/")

@app.route("/unblock")
def unblock():
    # Set the blocked_until timestamp to a past time (e.g., current time)
    for team in valid_teams:
        blocked_until = datetime.now().timestamp()  # Set it to the current time
        r.set(f"blocked_until:{team}", blocked_until)  # Unblock by setting timestamp to now

    # Return a response with no content (an empty body)
    return "", 204  # HTTP 204 No Content

@app.route("/")
def scores():
    teams = []
    for team_key in r.keys("score:*"):
        team_name = team_key.split(":")[1]
        new_team = Team(team_name, r.get(f"score:{team_name}"))
        teams.append(new_team)

    teams.sort(key=Team.getScore, reverse=True)

    # Add blocked time logic for the frontend
    blocked_teams = {}
    for team in valid_teams:
        blocked_until = r.get(f"blocked_until:{team}")
        if blocked_until:
            blocked_until = datetime.fromtimestamp(float(blocked_until))
            remaining_time = max(0, (blocked_until - datetime.now()).seconds)
            if remaining_time > 0:
                blocked_teams[team] = remaining_time  # Store remaining block time in seconds
            else:
                blocked_teams[team] = 0  # Block expired, free to vote
        else:
            blocked_teams[team] = 0  # Not blocked, free to vote

    return render_template("scoreboard.html", TEAMS=teams, BLOCKED_TEAMS=blocked_teams)

class Team:
    def __init__(self, name, score):
        self.name = name
        self.score = score

    def getScore(self):
        return int(self.score)

if __name__ == "__main__":
    app.debug = True
    app.run(host="0.0.0.0", port=8000)
