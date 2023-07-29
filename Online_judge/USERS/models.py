

from distutils.command.build_scripts import first_line_re
from django.db import models
from django.contrib.auth.models import AbstractUser
from OJ.models import Problem, TestCase


###############################################################################################################################


class User(AbstractUser):
    email = models.EmailField(unique=True, default="")
    full_name = models.CharField(max_length=50, default="")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.full_name = self.first_name+" "+self.last_name

    def __str__(self):
        return self.username


###############################################################################################################################


class Submission(models.Model):
    
    LANGUAGES = (("C++", "C++"), ("C", "C"), ("Python3", "Python3"), ("Python2", "Python2"), ("Java", "Java"))
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    problem = models.ForeignKey(Problem, null=True, on_delete=models.SET_NULL)
    user_code = models.TextField(max_length=10000, default="")
    user_stdout = models.TextField(max_length=10000, default="")
    user_stderr = models.TextField(max_length=10000, default="")
    submission_time = models.DateTimeField(auto_now_add=True, null=True)
    run_time = models.FloatField(null=True, default=0)
    language = models.CharField(
        max_length=10, choices=LANGUAGES, default="C++")
    verdict = models.CharField(max_length=100, default="Wrong Answer")

    class Meta:
        ordering = ['-submission_time']
   
    def __str__(self):
        return str(self.submission_time) + " : @" + str(self.user) + " : " + self.problem.name + " : " + self.verdict + " : " + self.language
# Create your models here
