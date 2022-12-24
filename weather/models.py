from django.db import models


class Measure(models.Model):
    date = models.DateTimeField("Дата замера", null=False, blank=False)
    temperature = models.FloatField("Температура")
    humidity = models.FloatField("Влажность")

    def __str__(self):
        return "Measure(%d, date=%s, temp=%.2f, hum=%.2f)" % (self.id, self.date.strftime("%d-%m-%Y %H:%M:%S%z"), self.temperature, self.humidity)