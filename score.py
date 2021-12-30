
import requests
from typing import List
from bs4 import BeautifulSoup
# import time
from requests_html import HTMLSession



class Match:
    def __init__(self, name, link):
        self.name = name
        self.link = link


    def details(self) -> list:
        '''
        Returns
        [
            Name -> str,\n
            Link -> str,\n
            Match Facts -> dict,\n
            Status -> int: -1 if match has not started, 0 if match is live, 1 if match has ended, None if status not clear
        ]
        '''

        return [self.name, self.link, self.match_facts(), self.get_status()]
        
    def match_facts(self):
        
        fact_link = self.link.replace('/live-cricket-scores/','/cricket-match-facts/') 
            
        
        session = HTMLSession()
        r = session.get(fact_link)
        # r.html.render()
        
        fact_soup = BeautifulSoup(r.html.html, 'lxml')
        
        
        fact_table = fact_soup.findAll('div', attrs={'class':'cb-col cb-col-100 cb-col-rt'})[0]
        
        headings = fact_table.findAll('div', attrs={'class':'cb-col cb-col-27 cb-mat-fct-itm text-bold'})
        facts = fact_table.findAll('div', attrs={'class':'cb-col cb-col-73 cb-mat-fct-itm'})

        headings = map(lambda x: x.text.strip(':').strip('\t'), headings)
        facts = map(lambda x: x.text.strip(':').strip('\t'), facts)


        match_facts = dict(zip(headings, facts))
        
        try:
            match_facts.pop('Playing')
            
        except:
            try:
                match_facts.pop('Bench')
            except:
                pass
        finally:
            match_facts.pop('Date')
            match_facts.pop('Time')

            
        return match_facts
            
        
    def get_status(self, ret_type=False):
        '''
        * returns -1 if match has not started\n
        * returns 0 if match is live\n
        * returns 1 if match has ended
        * returns None if status not clear
        '''
        
        # r = requests.get(self.link)
        
        session = HTMLSession()
        r = session.get(self.link)
        # r.html.render()
        soup = BeautifulSoup(r.html.html, 'lxml')

        hasEnded = bool(soup.find('div', attrs={'class':'cb-col cb-col-100 cb-min-stts cb-text-complete'}))
        isAbandon = bool(soup.find('div', attrs={'class':'cb-text-abandon'}))

        if hasEnded:
            if ret_type:
                return (1, 'hasEnded', soup)
            return 1
        
        elif isAbandon:
            if ret_type:
                return (1,'isAbandon', soup)
            return 1

        
        isLive = bool(soup.find('div', attrs={'class':'cb-text-inprogress'}))
        isStumps = bool(soup.find('div', attrs={'class':'cb-text-stumps'}))
        isLunch = bool(soup.find('div', attrs={'class':'cb-text-lunch'}))
        isTea = bool(soup.find('div', attrs={'class':'cb-text-tea'}))
        isInningsBreak = bool(soup.find('div', attrs={'class':'cb-text-inningsbreak'}))
        isRain = bool(soup.find('div', attrs={'class':'cb-text-rain'}))
        isWet = bool(soup.find('div', attrs={'class':'cb-text-wetoutfield'}))
        
        if isLive:
            if ret_type:
                return (0,'isLive', soup)
            return 0
        elif isRain:
            if ret_type:
                return (0,'isRain', soup)
            return 0
        elif isWet:
            if ret_type:
                return (0,'isWet', soup)
            return 0
        elif isStumps:
            if ret_type:
                return (0,'isStumps', soup)
            return 0
        elif isTea:
            if ret_type:
                return (0,'isTea', soup)
            return 0
        elif isLunch:
            if ret_type:
                return (0,'isLunch', soup)
            return 0
        elif isInningsBreak:
            if ret_type:
                return (0,'isInningsBreak', soup)
            return 0

        isToss = bool(soup.find('div', attrs={'class':'cb-text-toss'}))
        hasNotStarted = bool(soup.find('div', attrs={'id':'text_link_container'}))
        if isToss:
            if ret_type:
                return (-1,'isToss', soup)
            return -1
        elif hasNotStarted:
            if ret_type:
                return (-1,'hasNotStarted', soup)
            return -1
        

            
    def curr_score(self):
        '''
        returns:
        {'teams':(teamA, teamB), 'summary':summary, 'inningsWiseScores':{'innings_1':{'batting':[(name, (runs, balls))], 'bowling':[(name, (wickets, runs, overs))]}}}
        '''
        
        
        status, detailedStatus, soup = self.get_status(ret_type=True)

        
        score = {}
        
        #team names
        teams = soup.find('h1', attrs={'class':'cb-nav-hdr cb-font-18 line-ht24'}).text.split(',')[0].split('vs')
        teamA, teamB = map(lambda x: x.strip(), teams)
        score['teams'] = (teamA, teamB)
        
        #match name
        matchName = soup.find('h1', attrs={'class':'cb-nav-hdr cb-font-18 line-ht24'}).text.split('-')[0].strip()
        
        score['match_name'] = matchName
        
        if detailedStatus == 'hasNotStarted':
            return score
        

        session = HTMLSession()
        r = session.get(self.link.replace('live-cricket-scores', 'live-cricket-scorecard'))

        # r.html.render()
        
        scoreSoup = BeautifulSoup(r.html.html, 'lxml')

        #summary statement
        summary = scoreSoup.find('div', attrs={'class': 'cb-scrcrd-status'}).text
        score['summary'] = summary
        
        if status == -1:
            return score
                
        #batting team name
        inn_heads = scoreSoup.findAll('div', attrs={'class':'cb-col cb-col-100 cb-scrd-hdr-rw'})[:-1]
        inn_scores = []
        bat_team = []
        
        for i in inn_heads:
            sc = i.find('span', attrs={'class':'pull-right'})
            inn_scores.append(sc.text)
            sc.decompose()
            bat_team.append(i.find('span').text)
            
            
        
        
        #get top batsmen of each innings
        
        no_inns = len(inn_heads)
        
        allOut = False
        
        inningsWiseScores = {}
        
        for i, _ in enumerate(inn_heads):
            
            inning = scoreSoup.find('div', attrs={'id':f'innings_{i+1}'})
            batCard = inning.findAll('div', attrs={'class':'cb-col cb-col-100 cb-ltst-wgt-hdr'})[0]
            bowlCard = inning.findAll('div', attrs={'class':'cb-col cb-col-100 cb-ltst-wgt-hdr'})[1]

            #get current batsmen
            if status == 0:
                if (i+1) == no_inns:
                    
                    if '-10' in inn_scores[i]:
                        allOut = True
                        
                    else:
                        batsmen = batCard.findAll('div', attrs={'class':'cb-col cb-col-100 cb-scrd-itms'})
                        
                        curr_batsmen = list(map(lambda x: x.find('div', attrs={'class':'cb-col cb-col-27 text-bold'}), batsmen))

                        batters = dict(zip(curr_batsmen, batsmen))
                        
                        curr_batters = {}
                        
                        for div, row in batters.items():
                            if not div is None:
                                curr_batters[div.text.strip()] = row
                                
                        for batsman, div in curr_batters.items():
                            runs = div.find('div', attrs={'class':'cb-col cb-col-8 text-right text-bold'}).text
                            balls = div.findAll('div', attrs={'class':'cb-col cb-col-8 text-right'})[0].text
                            curr_batters[batsman] = (runs, balls)


                        final_batters = []

                        for j in curr_batters.keys():
                            final_batters.append((j, curr_batters[j]))
                            
                        curr_batters = final_batters
                            
                    
            #get top batsmen
            if status == 1 or i+1 != no_inns or allOut: 
                batsmen = batCard.findAll('div', attrs={'class':'cb-col cb-col-100 cb-scrd-itms'})
                valid_rows = []
                list(map(lambda x: valid_rows.append(x) if x.find('div', attrs={'class':'cb-col cb-col-33'}) else None, batsmen))

                runs = []
                names = []
                balls = []

                for row in valid_rows:
                    try:
                        names.append(row.find('div', attrs={'class':'cb-col cb-col-27'}).text.strip())
                    except:
                        names.append(row.find('div', attrs={'class':'cb-col cb-col-27 text-bold'}).text.strip())
                    runs.append(int(row.find('div', attrs={'class':'cb-col cb-col-8 text-right text-bold'}).text))
                    balls.append(int(row.findAll('div', attrs={'class':'cb-col cb-col-8 text-right'})[0].text))
                
                curr_batters_list = dict(zip(names, tuple(zip(runs, balls))))
                curr_batters_list = sorted(curr_batters_list.items(), key=lambda x: x[1][0], reverse=True)
                                
                curr_batters = {}
                
                def _setvalue(x):
                    curr_batters[x[0]] = x[1]
                
                list(map(lambda x: _setvalue(x), curr_batters_list))
                
                curr_batters = list(curr_batters.items())[:2]
                
                
            #get top bowlers of each innings
            
            bowlers = bowlCard.findAll('div', attrs={'class':'cb-col cb-col-100 cb-scrd-itms'})
            
            runs = []
            names = []
            overs = []
            wickets = []
            for bowler in bowlers:
                names.append(bowler.find('div', attrs={'class':'cb-col cb-col-40'}).text.strip())
                runs.append(int(bowler.findAll('div', attrs={'class':'cb-col cb-col-10 text-right'})[0].text))
                overs.append(float(bowler.findAll('div', attrs={'class':'cb-col cb-col-8 text-right'})[0].text))        
                wickets.append(int(bowler.find('div', attrs={'class':'cb-col cb-col-8 text-right text-bold'}).text))
                
                
            curr_bowlers_list = dict(zip(names, tuple(zip(wickets, runs, overs))))
            curr_bowlers_list = sorted(curr_bowlers_list.items(), key=lambda x: x[1][0], reverse=True)
            
            curr_bowlers = {}
            
            def _setvalue(x):
                curr_bowlers[x[0]] = x[1]
                            
            list(map(lambda x: _setvalue(x), curr_bowlers_list))
                            
            curr_bowlers = list(curr_bowlers.items())[:2]
            
            
            
            #final return from loop
            inningsWiseScores[bat_team[i]] = {'overall': inn_scores[i], 'batting': curr_batters, 'bowling': curr_bowlers}

        score['inningsWiseScores'] = inningsWiseScores
        
        
        return score
        


        

def get_matches() -> List[Match]:
    
    URL = "https://www.cricbuzz.com/"
    
    r = requests.get(URL)

    soup = BeautifulSoup(r.content, 'html5lib')

    matches = []

    matchlist = soup.find(
        'ul', attrs={'class': 'cb-col cb-col-100 videos-carousal-wrapper'})

    matchboxes = matchlist.findAll('li', attrs={
                                'class': 'cb-col cb-col-25 cb-mtch-blk cb-vid-sml-card-api videos-carousal-item cb-carousal-item-large cb-view-all-ga'})
    
    for matchbox in matchboxes:

        a = matchbox.find('a', attrs={'class': 'cb-font-12'})
        
        name = a['title']
        link = a['href']

        matches.append(Match(name, f'https://cricbuzz.com{link}'))
        
    return matches

    


# if __name__ == '__main__':
#     stt = time.time()
#     print(get_matches()[0].curr_score())
#     print(time.time()-stt)




'''

if __name__ == "__main__":
    matches = get_matches(FIREFOX_PATH = 'C:\\Users\\conta\\Desktop\\programs\\python_codes\\TiggyBot\\geckodriver.exe'
)
    match = matches[0]
    match_facts = match.match_facts()

    curr_score = match.curr_score()
    
    inningsWiseScores = list(curr_score['inningsWiseScores'].items())
    
    scoreboard = f"**{curr_score['match_name']}**\n*{match.link}*\n\n*{curr_score['summary']}*\n\n"

    num_inns = len(inningsWiseScores)
    
    for i in range(0, num_inns):
        scoreboard += f"__{inningsWiseScores[i][0]}__ - *{inningsWiseScores[i][1]['overall']}*:\n\n"
        
        batting = inningsWiseScores[i][1]['batting']
        
        scoreboard+= f"*Batting*\n"
        
        num_batsmen = len(batting)
        if num_batsmen == 0:
            scoreboard += "-\n\n"
        elif num_batsmen == 1:
            scoreboard += f"{batting[0][0]}: {batting[0][1][0]}({batting[0][1][1]})\n\n"
        elif num_batsmen == 2:
            scoreboard += f"{batting[0][0]}: {batting[0][1][0]}({batting[0][1][1]})\n"
            scoreboard += f"{batting[1][0]}: {batting[1][1][0]}({batting[1][1][1]})\n\n"
        
        bowling = inningsWiseScores[i][1]['bowling']
        
        scoreboard+= f"*Bowling*\n"
        
        num_bowlers = len(bowling)
        if num_bowlers == 0:
            scoreboard += "-\n\n"
        elif num_bowlers == 1:
            scoreboard += f"{bowling[0][0]}: {bowling[0][1][0]}({bowling[0][1][1]})\n\n"
        elif num_bowlers == 2:
            scoreboard += f"{bowling[0][0]}: {bowling[0][1][0]}-{bowling[0][1][1]}({bowling[0][1][2]})\n"
            scoreboard += f"{bowling[1][0]}: {bowling[1][1][0]}-{bowling[1][1][1]}({bowling[1][1][2]})\n\n"
        

    scoreboard+= '\*\*\*\*\*\*\*\*\n\n'
    
    scoreboard+= '__Extras__\n\n'
    for i in list(match_facts.keys()):
        scoreboard+=f'{i}: {match_facts[i]}\n'
    
    print(scoreboard)


    # {'Match': 'ADS vs MLR, 6th Match, Big Bash League 2021-22', 
    #  'Toss': 'Adelaide Strikers won the toss and opt to bat', 
    #  'Venue': 'Adelaide Oval, Adelaide', 
    #  'Umpires': ' Ben Treloar, Michael Graham-Smith ', 
    #  'Third Umpire': 'Philip Argall', 
    #  'Match Referee': ' Steve Davis '}

    
    
    # **match name**

    # *status*

    # __1st innings name__:
    # batsman 1 name: runs(balls)
    # batsman 2 name: runs(balls)

    # bowler 1 name: wickets-runs(overs)
    # bowler 2 name: wickets-runs(overs)

    # __2nd innings name__:
    # batsman 1 name: runs(balls)
    # batsman 2 name: runs(balls)

    # bowler 1 name: wickets-runs(overs)
    # bowler 2 name: wickets-runs(overs)

    # \*\*\*\*\*\*\*\*
    
    # __Extras__
    # XYZ: *abc*
    
    

'''