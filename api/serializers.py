from rest_framework import serializers

class GoalPredictionSerializer(serializers.Serializer):
    file_name = serializers.CharField()
    urlavgtable = serializers.CharField()
    urlfixture = serializers.CharField()
    Homeavg = serializers.FloatField()
    Awayavg = serializers.FloatField()