from .database import SessionLocal, init_db
from .models import Rule

# List of rules to insert (add as many as you want)
RULES = [
    {
        "title": "Order of Play",
        "description": "The Captain is determined randomly on the first tee. The order rotates each hole."
    },
    {
      "title": "Basic Game (4 Players)",
      "description": "Played with four players. Hitting order is determined randomly at the first tee. The first player is the Captain. The Captain may request a partner for that hole (best ball). A player becomes ineligible to be requested once the next player in order has hit their shot. The fourth player may be requested until the first 'second' shot is struck. If the Captain doesn't request a partner, they compete against the best ball of the other three. A player can turn down a Captain's request, then competing against the best ball of the other three."
    },
    {
      "title": "Rotation (4 Players)",
      "description": "At the second hole, the order of play rotates: player who hit second hits first, third becomes second, fourth becomes third, and the prior Captain moves to fourth."
    },
    {
      "title": "Mandatory Solo (4-Man Game)",
      "description": "In the 4-man game only, each player is required to go solo at least once in the first 16 holes (before the start of the Hoepfinger)."
    },
    {
      "title": "5-Man Game Setup",
      "description": "Order determined randomly at the first tee. First player is Captain, fifth player is Aardvark. Captain may only request a partnership with one of the first four players (#2-4). Once teams are aligned amongst the first four, the Aardvark may request to join one of the two teams (making it 2 vs 3), provided the request is made prior to the first second shot. If one of the first four players goes solo, the game for that hole becomes one-on-one-on-three."
    },
    {
      "title": "Aardvark Joining (5-Man Game)",
      "description": "If the solicited team (A) rejects the Aardvark’s request, he automatically joins the other team (B), and the point risk to each player on team B is doubled (triple risk to team A). The Aardvark can also 'go it alone', playing his ball against the best ball of each of the two other teams. Team A and Team B also compete best ball."
    },
    {
      "title": "Rotation and Spot Selection (5-Man Game)",
      "description": "Rotation is equal after 15 holes. On the 16th tee, the low point-getter selects where they want to hit in the rotation, with others falling into relative spots. On the 17th and 18th tees, the recalculated low point-getter chooses their spot."
    },
    {
      "title": "6-Man Game Setup",
      "description": "Has two Aardvarks. The first Aardvark (#5) must settle which team he is on before the second Aardvark (#6) can inquire about a partnership. After random rotation, Captain selects partners from top four hitters. Once his partnership is solidified, the first player in order not selected becomes a second Captain, able to select any remaining player as a partner. The second Captain can 'go it alone'. If the original Captain 'goes it alone', players 2-4 form Team B, and 5&6 become Team C."
    },
    {
      "title": "Aardvark (General Definition)",
      "description": "On a given hole, the player to hit fifth or sixth in the order. The Aardvark may ask to join a team, or go on his own. A request may be denied ('tossed'), in which case the Aardvark is automatically on (one of) the other team(s). If there are more than two teams for the Aardvark to choose from and he is tossed by his first choice, he will then choose between the remaining teams."
    },
    {
      "title": "Change of Mind",
      "description": "If a question is asked of a player or team (e.g., a double or request to join), a player’s answer is final upon the start of the next game-action (e.g., player addressing ball, subsequent offer/request)."
    },
    {
      "title": "Hanging Chad",
      "description": "When the Karl Marx rule applies but impacted players have the same point total, the scorekeeper keeps their scores in limbo until they diverge. This postpones the application of the Karl Marx rule."
    },
    {
      "title": "The Hoepfinger",
      "description": "Phase of the game starting once each player has had their full complement of turns as Captain. 4-man game: starts on 17th hole. 5-man game: starts on 16th hole. 6-man game: starts on 13th hole. At the start of each Hoepfinger hole, the player furthest down (the Goat) chooses their spot in the rotation. In 6-man game, a player may not choose to hit from the same spot more than twice in a row. Base value of each hole determined by Joe’s Special."
    },
    {
      "title": "The Invisible Aardvark",
      "description": "Exists only in the 4-man game. Automatically asks to join the team that was forcibly formed. Records no score. Important for Betting Conventions."
    },
    {
      "title": "The Invitation",
      "description": "The Captain and/or Aardvark(s) may invite another player(s) to join their partnership. No player may be invited after they have hit their tee shot AND the next shot has been played. If invitation is turned down, bet doubles and: 4-man game: player turning down plays 'on his own' against other three. 5-man game (Captain asks non-Aardvark): similar to 4-man; (Aardvark turned down): Aardvark is 'tossed' to other team. 6-man game (second Aardvark turned down with >2 teams): he may select which remaining team to request partnership with."
    },
    {
      "title": "The Karl Marx Rule",
      "description": "When quarters won/lost are not easily divisible (e.g., 5-man game, 3-on-2, 1 quarter wager, 2-man team loses, owing 3 quarters). The player furthest down owes fewer quarters. If tied, scorekeeper waits until totals diverge before assigning the odd quarter. 'From each according to his ability, to each according to his need.'"
    },
    {
      "title": "Line of Scrimmage",
      "description": "No offer of a double can be proffered by a player that has passed the line of scrimmage (the ball furthest from the hole). A double may not be offered if relying on information from another player past the line of scrimmage. However, a proper double offered to a team that has passed the line of scrimmage is valid and must be responded to before the next ball is hit."
    },
    {
      "title": "Order of Play",
      "description": "Aside from tee box rotation, play follows strict Match Play format (USGA Rules of Golf). Player furthest from hole hits next. Once a ball is in the cup, no further betting. A shot/putt can be conceded ('good, but not in') but isn't deemed in the cup for betting purposes."
    },
    {
      "title": "Range Finders",
      "description": "On par 3s, may only be used prior to the first tee shot AND only by players immediately before their second shot if not yet on the green. Not to be used on any hole to bypass the Line of Scrimmage rule by gentlemen's agreement."
    },
    {
      "title": "Vinnie’s Variation",
      "description": "In the 4-man game, the base value of each hole is doubled starting on the 13th tee and continuing through the start of the Hoepfinger phase (17th hole)."
    }
    ,
    {
      "title": "Typical Wager",
      "description": "Begins at one quarter per hole. During special weeks (PGA Tour Majors, designated by Commissioner), base wager may start at two quarters."
    },
    {
      "title": "Ackerley’s Gambit",
      "description": "If a team offered a double cannot agree, players may opt in while others opt out. Opt-out player(s) relinquish their at-risk quarters to those staying in. Opt-in player(s) are responsible for the entire bet. The offering team is unaffected. The dissenting player's score still accrues to the benefit of opt-in teammates."
    },
    {
      "title": "The Big Dick",
      "description": "Before 18th tee, player with most points may declare 'on-his-own' versus the group, risking all winnings. Others must unanimously agree. A Gambit can cover a player who declines. If remaining players are four or more, they also play a separate Wolf, Goat, Pig game."
    },
    {
      "title": "The Carry-Over",
      "description": "If a hole is halved by all teams, it's 'carried-over', doubling the prior hole's starting wager. Cannot occur on consecutive holes (e.g., if 3rd hole is halved after 2nd was carried over, 4th hole starts at same value as 3rd did after carry-over)."
    },
    {
      "title": "Double",
      "description": "Offer from one team to another to double the stakes. Can be done anytime after teams are formed, but not while a member of the target team is addressing their ball. If turned down, offering team wins hole by default at pre-double wager. If accepted, offering team cannot double again unless redoubled. If no response and reasonable time elapses, double is deemed accepted once next shot is played in proper order."
    },
    {
      "title": "The Duncan",
      "description": "If Captain announces before hitting that he intends to go 'on his own' (the Pig), he wins 3 quarters for every 2 wagered if he earns the best net score."
    },
    {
      "title": "The Float",
      "description": "In 4-man and 5-man games, each player may invoke a 'float' once during the round when Captain, increasing the wager. Not required."
    },
    {
      "title": "If at First you Do succeed, then try, try again",
      "description": "If WGP results are determined before leaving tee box, the 'furthest down' player on conceding team selects a new partner for best ball for remainder of hole. Points at risk are two; no further betting/doubling."
    },
    {
      "title": "In the hole",
      "description": "Once any player has holed a shot, no additional wagering may occur."
    },
    {
      "title": "Joes’ Special",
      "description": "Player furthest down (Goat) moving to Hoepfinger may set starting value at each Hoepfinger hole as 2, 4, or 8 quarters. If natural start value (e.g. due to carry-over) is >8, Goat may choose that. Otherwise, Hoepfinger hole max start is 8 (neither carryovers nor Major weeks alter this). If Goat is silent, Hoepfinger starts at greater of 2 quarters or natural start. First invoked on hole 16 (5/6-man) or 17 (4-man). No 'doubling' during Joe’s Special until all players have hit tee shots."
    },
    {
      "title": "Double Points Rounds",
      "description": "Base bet doubled (two quarters) on days of: The Masters, PGA Championship, U.S. Open, Open Championship (British), Players Championship, and Annual Banquet."
    },
    {
      "title": "On Your Own",
      "description": "Captain may elect to go 'on his own' (playing his ball against best ball of opponents), doubling base wager. A player can also go 'on his own' by turning down Captain's partnership offer."
    },
    {
      "title": "The Option",
      "description": "If Captain has lost most quarters pre-hole, they can double wager before tee shots. If multiple players tied for greatest losses, each can invoke. Automatically invoked unless Captain proactively 'turns it off'."
    },
    {
      "title": "Ping Ponging the Aardvark",
      "description": "A team may turn away (re-toss) an Aardvark (invisible or not) tossed to them, doubling the bet again. A team may not toss the same Aardvark twice on the same hole."
    },
    {
      "title": "Quorum",
      "description": "A player’s performance added to spreadsheet only when at least three Members play in same group. If multiple groups, Members may 'deputize' Pigeons to reach quorum in each group."
    },
    {
      "title": "Tossing the Aardvark",
      "description": "4-man game: Invisible Aardvark may be tossed (doubling hole value), except if a player goes 'on his own'. If tossed by forcibly formed team before either player hits, they win 3 quarters for every 2 wagered ('3 for 2'). 5-man game: If Aardvark tossed, wager doubles. 6-man game: If Aardvark tossed, tossing team doubles wager with each other team; wager between teams not involved in toss is not doubled (can happen with 3 teams)."
    },
    {
      "title": "The Tunkarri",
      "description": "In 5 or 6-man game, either Aardvark may declare before Captain hits tee shot that he intends to go 'on his own'. If so, wins 3 quarters for every 2 wagered if he earns best net score."
    }
    ,
    {
      "title": "Acting Commissioner",
      "description": "Commissioner Emeritus is Jon Pettit. Pettit Trophy winner serves as Acting Commissioner after hosting Annual Banquet. Leads discussions, mitigates disputes, interprets rules (interpretations are executive orders until voted on at term end for permanent inclusion)."
    },
    {
      "title": "The Annual Banquet",
      "description": "Hosted by reigning champion. Rules reviewed, proposals considered/voted on. Members with >=20 appearances (previous year) vote on whether members with <20 appearances remain on spreadsheet (vote via email pre-banquet, led by current commissioner). Potluck; host provides entrée."
    },
    {
      "title": "Decorum",
      "description": "Players ask for privileges (e.g., 'Will you be my partner?'). Rooting against opponents allowed if in good form. Banter is a mainstay. Be cautious with advice. 'You are likely to be led down the wrong path, especially if it is the Weasel who is offering it.'"
    },
    {
      "title": "FTA (Failure to Appear)",
      "description": "Player committed to play but doesn't appear is fined 10 quarters (spreadsheet) per player who does appear. Avoidable by emailing all spreadsheet members before 7 am on day of play. Late cancellation still subject to ridicule."
    },
    {
      "title": "Good But Not In",
      "description": "Opposing team may deem next shot/putt 'good' (score recorded as if holed) 'but not in' (wagering may continue). Allows faster play while maintaining betting integrity."
    },
    {
      "title": "Handicaps",
      "description": "Official off-season: play to handicap trend from Pro Shop site, less lowest handicap trend (net handicap). Official posting season: official handicap applied. Individual handicaps determined by subtracting lowest player's handicap from all players'."
    },
    {
      "title": "The Creecher Feature",
      "description": "In awarding strokes, highest six handicap holes for each player played at ½ stroke. Other holes, full strokes. Example (Net HDCP 18+): HDCP holes 13-18 at ½ stroke, full strokes on others, + additional ½ stroke on two holes for every one stroke net HDCP exceeds 18. Example (Net HDCP 10): HDCP holes 5-10 at ½ stroke, full strokes on holes 1-4. Example (Net HDCP <=6): all 'handicap' holes at ½ strokes."
    },
    {
      "title": "The Pettit Trophy",
      "description": "Winner of the 'spreadsheet' awarded the Pettit Trophy. Perpetual trophy housed by most recent winner. Plaque updated by previous winner before Annual Banquet."
    },
    {
      "title": "Rules Amendments",
      "description": "Between Banquets: spreadsheet member proposes to Commissioner. If worthy, Commissioner puts to vote of all spreadsheet members. Majority affirmative vote needed. Adopted changes revisited at next Banquet for permanent approval."
    },
    {
      "title": "The Tossing of the Tees",
      "description": "Before play, designee tosses tees to determine order of play from tee throughout round, until Hoepfinger phase. Order rotates tee to tee."
    },
    {
      "title": "Quarters",
      "description": "The 25 cent piece is the base unit of currency for one betting unit."
    },
    {
      "title": "Scorekeeping",
      "description": "One player keeps 'point' score per hole (points won/lost). Tally should balance to zero. Mistakes corrected by group audit."
    },
    {
      "title": "The Spreadsheet",
      "description": "Maintained by a volunteer member in good standing. Tracks quarters won (by player, date, including pigeons) and official appearances. Season: day after Open Championship final round to day of next Open Championship final round."
    },
    {
      "title": "Early Departures",
      "description": "If player doesn't complete round: (1) If ahead: quarters distributed evenly (Karl Marx rule if needed). (2) If behind: quarters paid out, spreadsheet score affected. (3) If pre-round unanimous agreement on early departure, that agreement takes precedent."
    }
  ]


]

def main():
    init_db()
    db = SessionLocal()
    for rule in RULES:
        # Avoid duplicate insertion by checking for existing title
        if not db.query(Rule).filter_by(title=rule["title"]).first():
            db.add(Rule(title=rule["title"], description=rule["description"]))
    db.commit()
    db.close()
    print("Rules seeded successfully.")

if __name__ == "__main__":
    main()
