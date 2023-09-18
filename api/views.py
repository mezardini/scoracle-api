from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Team, Fixture
from .serializers import MatchPredictorSerializer
from bs4 import BeautifulSoup
import requests
import pandas as pd
import csv
from scipy.stats import poisson
import math
import heapq
import json
# Create your views here.


class LeaguePrediction(APIView):
    def __init__(self,request, fn,urlavgtable, urlfixture, Homeavg, Awayavg ) :
        self.file_name = fn
        json_data = json.loads(request.body.decode('utf-8'))
        league = json_data.get('league', '')
        urlavgtable = 'https://www.soccerstats.com/table.asp?league='+league+'&tid=d'
        urlfixture = 'https://www.soccerstats.com/latest.asp?league='+league
        self.urlavgtable = urlavgtable
        self.urlfixture = urlfixture
        self.Homeavg = json_data.get('Home Average', '')
        self.Awayavg = json_data.get('Away Average', '')

    def post(self, request):
        try:
            # Print the league table into a csv file
            response = requests.get(self.urlavgtable)

            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the table element containing the data
            table = soup.find("table", {"id": "btable"})

            # Get the table header
            header = table.find_all("th")
            header = [h.text.strip() for h in header]

            # Get the table rows
            rows = table.find_all("tr")[1:]
            header_row = ['Team name', 'Scoredhome', 'Conc.', 'Total', 'Scored', 'Conc.', 'Total', 'Scored', 'Conc.', 'Total', 'GP']

        
            with open("csv/"+self.file_name, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(header_row)

                for row in rows[1:]:
                    cols = row.find_all('td')
                    cols = [col.text.strip() for col in cols]

                    writer.writerow(cols)
            # Send the fixture list and the predictions      
            res = requests.get(self.urlfixture)
            soup = BeautifulSoup(res.content, 'html.parser')

            odd_rows = soup.find_all('tr', {'class': 'odd', 'height': '32'})
            cols = []
            for row in odd_rows:
                cols.extend(row.find_all('td', {'style': ['text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']}))

            output = [col.text.strip() for col in cols]   

            # for i in range(0, len(output), 4):
            #     first_line = output[i].ljust(50) + output[i+1].rstrip()
            #     # second_line = output[i+2].ljust(50) + output[i+3].rstrip()

            #     print(f"{first_line}")
            # for i in range(len(output)):
            #     if i % 2 == 0:
            #         print(output[i], end=" ")
            #         if i+1 < len(output):
            #             print(output[i+1])


            with open("csv/"+self.file_name, newline='') as csvfile:

                # Create a CSV reader object
                reader = csv.reader(csvfile)

                # Create an empty list to hold the values in the first column
                teams = []

                # Iterate over each row in the CSV file
                for row in reader:

                    # Append the value in the first column to the list
                    teams.append(row[0])

        # Print the first column values as a list
        # print(first_column_values[2])

            b_tags = soup.find_all('b')
            # if len(b_tags) >= 755:
            #     b_tags[752].text
            #     b_tags[754].text
            H3a = self.Homeavg 
            A3a = self.Awayavg
            H3 = float(H3a)
            A3 = float(A3a)   

            for i in range(0, len(output), 2):
                first_item = output[i]
                second_item = output[i+1]
                if first_item in teams:
                    # print("Found at index:", my_list.index(first_item))
                    with open("csv/"+self.file_name, 'r') as f:
                        reader = csv.reader(f)
                        row_index = 0
                        for row in reader:
                            if row_index == teams.index(first_item):  # row_index starts from 0, so we're looking at row 5 here
                                row_list = row
                                break  # stop iterating over rows once we find the desired row
                            row_index += 1
                if second_item in teams:
                    # print("Found at index:", my_list.index(first_item))
                    with open("csv/"+self.file_name, 'r') as f:
                        reader = csv.reader(f)
                        row_index = 0
                        for row in reader:
                            if row_index == teams.index(second_item):  # row_index starts from 0, so we're looking at row 5 here
                                row_listaway = row
                                break  # stop iterating over rows once we find the desired row
                            row_index += 1
                            # print(row_listaway[5])
                    H1 = ("{:0.2f}".format(float(row_list[1])/H3)) 
                    H2 = ("{:0.2f}".format(float(row_listaway[6])/H3)) 
                    Home_goal = ("{:0.2f}".format(float(H1) * float(H2) * float(H3)))
                    A1 = ("{:0.2f}".format(float(row_list[2])/A3)) 
                    A2 = ("{:0.2f}".format(float(row_listaway[5])/A3)) 
                    Away_goal = ("{:0.2f}".format(float(A1) * float(A2) * float(A3)))
                    twomatch_goals_probability = ("{:0.2f}".format((1-poisson.cdf(k=2, mu=float(float(Home_goal) + float(Away_goal))))*100))
                    threematch_goals_probability = ("{:0.2f}".format((1-poisson.cdf(k=3, mu=float(float(Home_goal) + float(Away_goal))))*100))

                    lambda_home = float(Home_goal)
                    lambda_away = float(Away_goal)

                    score_probs = [[poisson.pmf(i, team_avg) for i in range(0, 10)] for team_avg in [lambda_home, lambda_away]]

                    outcomes = [[i, j] for i in range(0, 10) for j in range(0, 10)]

                    probs = [score_probs[0][i] * score_probs[1][j] for i, j in outcomes]

                    most_likely_outcome = outcomes[probs.index(max(probs))]

                    most_likely_prob_percent = max(probs) * 100
                    response_data = {
                        'H3': H3,
                        'A3': A3,
                        'Home_goal': Home_goal,
                        'Away_goal': Away_goal,
                        'most_likely_outcome': f"{first_item} {most_likely_outcome[0]} vs {second_item} {most_likely_outcome[1]}",
                        'most_likely_prob_percent': f"{most_likely_prob_percent:.1f}%",
                        'threematch_goals_probability': f"Over 2.5 prob: - {threematch_goals_probability}%",
                        'twomatch_goals_probability': f"Over 1.5 prob: - {twomatch_goals_probability}%"
                    }

                    return response_data
                # print(f"The most probable scoreline is Home {most_likely_outcome[0]} - {most_likely_outcome[1]} Away with probability {most_likely_prob_percent:.1f}%")
                max_goals = 3  # maximum number of goals to consider
                top_n = 5  # number of top scorelines to print

                scorelines = []
                def poisson_probability(lambda_, k):
                    return math.exp(-lambda_) * (lambda_ ** k) / math.factorial(k)

                for a in range(max_goals + 1):
                    for b in range(max_goals + 1):
                        prob = poisson_probability(lambda_home, a) * poisson_probability(lambda_away, b)
                        scoreline = (prob, f"A {a} - {b} B")
                        heapq.heappush(scorelines, scoreline)
                        if len(scorelines) > top_n:
                            heapq.heappop(scorelines)
                print("Top", top_n, "Probable Scorelines:")
                for scoreline in sorted(scorelines, reverse=True):
                    prob, outcome = scoreline
                    prob_percentage = prob * 100
                    print(outcome + ":", f"{prob_percentage:.2f}%")

        except Exception as e:
            return Response({'error': str(e)})

            

 
class SingleMatchPrediction(APIView):
    def post(self, request):
        Home_Team = request.data.get("Home_Goal_At_Home")
        Away_Team = request.data.get("Home_Goal_At_Home")
        Home_Goal_At_Home = request.data.get("Home_Goal_At_Home")
        Away_Goal_At_Away = request.data.get("Away_Goal_At_Away")
        Home_League_Average = request.data.get("Home_League_Average")
        Away_Conceded_Away = request.data.get("Away_Conceded_Away")
        Home_Conceded_Home = request.data.get("Home_Conceded_Home")
        Away_League_Average = request.data.get("Away_League_Average")
        H1 = ("{:0.2f}".format(float(Home_Goal_At_Home)/Home_League_Average)) 
        H2 = ("{:0.2f}".format(float(Away_Conceded_Away)/Home_League_Average)) 
        Home_goal = ("{:0.2f}".format(float(H1) * float(H2) * float(Home_League_Average)))
        A1 = ("{:0.2f}".format(float(Home_Conceded_Home)/Away_League_Average)) 
        A2 = ("{:0.2f}".format(float(Away_Goal_At_Away)/Away_League_Average)) 
        Away_goal = ("{:0.2f}".format(float(A1) * float(A2) * float(Away_League_Average)))
        twomatch_goals_probability = ("{:0.2f}".format((1-poisson.cdf(k=2, mu=float(float(Home_goal) + float(Away_goal))))*100))
        threematch_goals_probability = ("{:0.2f}".format((1-poisson.cdf(k=3, mu=float(float(Home_goal) + float(Away_goal))))*100))

        lambda_home = float(Home_goal)
        lambda_away = float(Away_goal)

        score_probs = [[poisson.pmf(i, team_avg) for i in range(0, 10)] for team_avg in [lambda_home, lambda_away]]

        outcomes = [[i, j] for i in range(0, 10) for j in range(0, 10)]

        probs = [score_probs[0][i] * score_probs[1][j] for i, j in outcomes]

        most_likely_outcome = outcomes[probs.index(max(probs))]

        most_likely_prob_percent = max(probs) * 100
        response_data = {
            'Home_goal': Home_goal,
            'Away_goal': Away_goal,
            'most_likely_outcome': f"{Home_Team} {most_likely_outcome[0]} vs {Away_Team} {most_likely_outcome[1]}",
            'most_likely_prob_percent': f"{most_likely_prob_percent:.1f}%",
            'threematch_goals_probability': f"Over 2.5 prob: - {threematch_goals_probability}%",
            'twomatch_goals_probability': f"Over 1.5 prob: - {twomatch_goals_probability}%"
        }

        return response_data

