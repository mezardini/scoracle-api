from django.db import models

# Create your models here.
class Team(models.Model):
    name = models.CharField(max_length=100)
    # Add other relevant fields

class Fixture(models.Model):
    home_team = models.ForeignKey(Team, related_name='home_fixtures', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_fixtures', on_delete=models.CASCADE)
    # Add other relevant fields