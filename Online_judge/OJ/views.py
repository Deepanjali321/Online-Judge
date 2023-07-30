# ```js
import traceback
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

from USERS.models import User, Submission
from OJ.models import Problem, TestCase
from OJ.forms import CodeForm
from datetime import datetime
from time import time

import os
import signal
import subprocess
import os.path
import docker


# To show stats on the dashboard
@login_required(login_url='login')
def homePage(request):
    return render(request, 'OJ/home.html')


# Has the list of problems with sorting & pagination
@login_required(login_url='login')
def problemPage(request):
    problems = Problem.objects.all()
    submissions = Submission.objects.filter(user=request.user, verdict="Accepted")
    accepted_problems = [submission.problem_id for submission in submissions]
    context = {'problems': problems, 'accepted_problems': accepted_problems}
    return render(request, 'OJ/problem.html', context)


# Shows problem description on the left side and has a text editor on the right side with a code submit button
@login_required(login_url='login')
def descriptionPage(request, problem_id):
    user_id = request.user.id
    problem = get_object_or_404(Problem, id=problem_id)
    user = User.objects.get(id=user_id)
    form = CodeForm()
    context = {'problem': problem, 'user': user, 'user_id': user_id, 'code_form': form}
    return render(request, 'OJ/description.html', context)


# Shows the verdict for the submission
@login_required(login_url='login')
def verdictPage(request, problem_id):
    if request.method == 'POST':
        # Setting up the docker client
        docker_client = docker.from_env()
        Running = "running"

        problem = Problem.objects.get(id=problem_id)
        testcase = TestCase.objects.get(problem_id=problem_id)
        # Replacing \r\n by \n in original output to compare it with the user code output
        testcase.output = testcase.output.replace('\r\n', '\n').strip()

        # Setting verdict to wrong by default
        verdict = "Wrong Answer"
        res = ""
        run_time = 0

        # Extract data from form
        form = CodeForm(request.POST)
        user_code = ''
        if form.is_valid():
            user_code = form.cleaned_data.get('user_code')
            user_code = user_code.replace('\r\n', '\n').strip()

        language = request.POST['language']
        submission = Submission(user=request.user, problem=problem, submission_time=datetime.now(),
                                language=language, user_code=user_code)
        submission.save()

        filename = str(submission.id)

        # If the user code is in C++
        if language == "C++":
            extension = ".cpp"
            cont_name = "oj-cpp"
            compile_cmd = f"g++ -o {filename} {filename}.cpp"
            clean_cmd = f"rm {filename} {filename}.cpp"
            docker_img = "gcc:11.2.0"
            exe_cmd = f"./{filename}"

        # Add similar conditions for other languages if needed

        file = filename + extension
        filepath = settings.FILES_DIR + "/" + file
        code = open(filepath, "w")
        code.write(user_code)
        code.close()

        # Checking if the docker container is running or not
        try:
            container = docker_client.containers.get(cont_name)
            container_state = container.attrs['State']
            container_is_running = (container_state['Status'] == Running)
            if not container_is_running:
                subprocess.run(f"docker start {cont_name}", shell=True)
        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {cont_name} {docker_img}", shell=True)

        # Copying the .cpp file into the docker container
        subprocess.run(f"docker cp {filepath} {cont_name}:/{file}", shell=True)

        # Compiling the code
        cmp = subprocess.run(f"docker exec {cont_name} {compile_cmd}", capture_output=True, shell=True)
        if cmp.returncode != 0:
            verdict = "Compilation Error"
            subprocess.run(f"docker exec {cont_name} {clean_cmd}", shell=True)
        else:
            # Running the code on given input and taking the output in a variable as bytes
            start = time()
            try:
                res = subprocess.run(f"docker exec {cont_name} sh -c 'echo \"{testcase.input}\" | {exe_cmd}'",
                                     capture_output=True, timeout=problem.time_limit, shell=True)
                run_time = time() - start
                subprocess.run(f"docker exec {cont_name} {clean_cmd}", shell=True)
            except subprocess.TimeoutExpired:
                run_time = time() - start
                verdict = "Time Limit Exceeded"
                subprocess.run(f"docker container kill {cont_name}", shell=True)
                subprocess.run(f"docker start {cont_name}", shell=True)
                subprocess.run(f"docker exec {cont_name} {clean_cmd}", shell=True)

            if verdict != "Time Limit Exceeded" and res.returncode != 0:
                verdict = "Runtime Error"

        user_stderr = ""
        user_stdout = ""
        if verdict == "Compilation Error":
            user_stderr = cmp.stderr.decode('utf-8')
        elif verdict == "Wrong Answer":
            user_stdout = res.stdout.decode('utf-8')
            if str(user_stdout) == str(testcase.output):
                verdict = "Accepted"
            testcase.output += '\n'  # Added an extra line to compare user output with an extra line at the end
            if str(user_stdout) == str(testcase.output):
                verdict = "Accepted"

        # Creating Solution class objects and showing them on the leaderboard
        user = User.objects.get(username=request.user)
        previous_verdict = Submission.objects.filter(user=user.id, problem=problem, verdict="Accepted")
        if len(previous_verdict) == 0 and verdict == "Accepted":
            user.save()

        submission.verdict = verdict
        submission.user_stdout = user_stdout
        submission.user_stderr = user_stderr
        submission.run_time = run_time
        submission.save()
        os.remove(filepath)
        context = {'verdict': verdict}
        return render(request, 'OJ/verdict.html', context)
