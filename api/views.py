from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse
from .models import Team, Fixture
from .serializers import UserSerializer
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from bs4 import BeautifulSoup
import requests
import pandas as pd
import csv
from scipy.stats import poisson
import math
import heapq
import json
import os
# Create your views here.

league_data = {}

class LeaguePrediction(APIView):
    # def __init__(self,request, fn,urlavgtable, urlfixture, Homeavg, Awayavg ) :
    #     self.file_name = fn
    #     json_data = json.loads(request.body.decode('utf-8'))
    #     league = json_data.get('league', '')
        
        # self.Homeavg = json_data.get('Home Average', '')
        # self.Awayavg = json_data.get('Away Average', '')

    def get(self, request, league):
        league_form = request.POST['league']
        league = str(league_form)
        urlavgtable = f'https://www.soccerstats.com/table.asp?league={league}&tid=d'
        urlfixture = f'https://www.soccerstats.com/latest.asp?league={league}'
        try:
                # Print the league table into in-memory data
            response = requests.get(urlavgtable)
            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", {"id": "btable"})
            header = table.find_all("th")
            header = [h.text.strip() for h in header]
            rows = table.find_all("tr")[1:]
            league_data[league] = {'header': header, 'rows': []}

            for row in rows[1:]:
                cols = row.find_all('td')
                cols = [col.text.strip() for col in cols]
                league_data[league]['rows'].append(cols)

            # Send the fixture list and the predictions
            res = requests.get(urlfixture)
            soup = BeautifulSoup(res.content, 'html.parser')
            odd_rows = soup.find_all('tr', {'bgcolor':'#fff5e6', 'height': '32'})
            cols = []
            for row in odd_rows:
                cols.extend(row.find_all('td', {'style': ['text-align:right;padding-right:8px;', 'text-align:left;padding-left:8px;']}))

            output = [col.text.strip() for col in cols]

            teams = [row[0] for row in league_data[league]['rows']]

            b_tags = soup.find_all('b')
            table = soup.find("table", style="margin-left:14px;margin-riht:14px;border:1px solid #aaaaaa;border-radius:12px;overflow:hidden;")

            Home_avg = float(100.000)
            if table:
                b_tags = table.find_all("b")
                if len(b_tags) >= 9:
                    Home_avg = b_tags[8].text

            Away_avg = float(100.000)
            if table:
                b_tags = table.find_all("b")
                if len(b_tags) >= 11:
                    Away_avg = b_tags[10].text

            H3a = Home_avg
            A3a = Away_avg
            H3 = float(H3a)
            A3 = float(A3a)
            predictions_list = []

            for i in range(0, len(output), 2):
                first_item = output[i]
                second_item = output[i+1]
                if first_item in teams:
                    row_list = league_data[league]['rows'][teams.index(first_item)]
                if second_item in teams:
                    row_listaway = league_data[league]['rows'][teams.index(second_item)]

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

                response_data = [
                    {
                        'prediction': f"{first_item} {most_likely_outcome[0]} vs {second_item} {most_likely_outcome[1]}",
                        'over_2.5_prob': f"{threematch_goals_probability}%",
                        'over_1.5_prob': f"{twomatch_goals_probability}%"
                    },
                    # Add more predictions in a similar format if needed
                ]
                return Response(response_data)
                predictions_list.extend(response_data)

                # Join predictions with newlines
                predictions = predictions_list

        except Exception as e:
            predictions = f'Error: {str(e)}'


            

 

@api_view(['POST'])
def login(request):
    
    user = get_object_or_404(User, username = request.data['username'])
    if not user.check_password(request.data['password']):
        return Response({"detail":"Not found"}, status=status.HTTP_404_NOT_FOUND)
    token, created = Token.objects.get_or_create(user=user)
    serializer = UserSerializer(instance=user)
    return Response({"token":token.key, "user":serializer.data})

@api_view(['POST'])
def signup(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        user = User.objects.get(username=request.data['username'])
        user.set_password(request.data['password'])
        user.save()
        token = Token.objects.create(user=user)
        return Response({"token":token.key, "user":serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@authentication_classes([SessionAuthentication, TokenAuthentication])
@permission_classes([IsAuthenticated])
def auth_token(request):
    return Response("passed for {}".format(request.user.email))