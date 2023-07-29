# '''
# List of Views:
# - DASHBOARD PAGE: Has a dashboard with stats.
# - PROBLEM PAGE: Has the list of problems with sorting & paginations.
# - DEESCRIPTION PAGE: Shows problem description of left side and has a text editor on roght side with code submit buttton.
# '''
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


# ###############################################################################################################################


# # To show stats in dashboards
# @login_required(login_url='login')
def homePage(request):
    return render(request, 'OJ/home.html')


# ###############################################################################################################################


# # Has the list of problems with sorting & paginations
# @login_required(login_url='login')
def problemPage(request):
    problems = Problem.objects.all()
    submissions = Submission.objects.filter(user=request.user, verdict="Accepted")
    accepted_problems = []
    for submission in submissions:
        accepted_problems.append(submission.problem_id)
    context = {'problems': problems, 'accepted_problems': accepted_problems}
    return render(request, 'OJ/problem.html', context)



# ###############################################################################################################################


# # Shows problem description of left side and has a text editor on roght side with code submit buttton.
# @login_required(login_url='login')
def descriptionPage(request, problem_id):
    user_id = request.user.id
    problem = get_object_or_404(Problem, id=problem_id)
    user = User.objects.get(id=user_id)
    form = CodeForm()
    context = {'problem': problem, 'user': user, 'user_id': user_id, 'code_form': form}
    return render(request, 'OJ/description.html', context)


# ###############################################################################################################################


# # Shows the verdict to the submission
# @login_required(login_url='login')
# def verdictPage(request, problem_id):
  
#     if request.method == 'POST':
#         # setting docker-client
#         docker_client = docker.from_env()
#         Running = "running"

#         problem = Problem.objects.get(id=problem_id)
#         testcase = TestCase.objects.get(problem_id=problem_id)
#         #replacing \r\n by \n in original output to compare it with the usercode output
#         testcase.output = testcase.output.replace('\r\n','\n').strip() 

       


#         #setting verdict to wrong by default
#         verdict = "Wrong Answer" 
#         res = ""
#         run_time = 0

#         # extract data from form
#         form = CodeForm(request.POST)
#         user_code = ''
#         if form.is_valid():
#             user_code = form.cleaned_data.get('user_code')
#             user_code = user_code.replace('\r\n','\n').strip()
            
#         language = request.POST['language']
#         submission = Submission(user=request.user, problem=problem, submission_time=datetime.now(), 
#                                     language=language, user_code=user_code)
#         submission.save()

#         filename = str(submission.id)

#         # if user code is in C++
#         if language == "C++":
#             extension = ".cpp"
#             cont_name = "oj-cpp"
#             compile = f"g++ -o {filename} {filename}.cpp"
#             clean = f"{filename} {filename}.cpp"
#             docker_img = "gcc:11.2.0"
#             exe = f"./{filename}"
            
       

#         # elif language == "Python3":
#         #     extension = ".py"
#         #     cont_name = "oj-py3"
#         #     compile = "python3"
#         #     clean = f"{filename}.py"
#         #     docker_img = "python3"
#         #     exe = f"python {filename}.py"
        
#         # elif language == "Python2":
#         #     extension = ".py"
#         #     cont_name = "oj-py2"
#         #     compile = "python2"
#         #     clean = f"{filename}.py"
#         #     docker_img = "python2"
#         #     exe = f"python {filename}.py"


#         file = filename + extension
        
#         filepath = settings.FILES_DIR + "/" + file
#         code = open(filepath,"w")
#         code.write(user_code)
#         code.close()

#         # checking if the docker container is running or not
#         try:
#             container = docker_client.containers.get(cont_name)
#             container_state = container.attrs['State']
#             container_is_running = (container_state['Status'] == Running)
#             if not container_is_running:
#                 subprocess.run(f"docker start {cont_name}",shell=True)
#         except docker.errors.NotFound:
#             subprocess.run(f"docker run -dt --name {cont_name} {docker_img}",shell=True)


#         # copy/paste the .cpp file in docker container 
#         subprocess.run(f"docker cp {filepath} {cont_name}:/{file}",shell=True)

#         # compiling the code
#         cmp = subprocess.run(f"docker exec {cont_name} {compile}", capture_output=True, shell=True)
#         if cmp.returncode != 0:
#             verdict = "Compilation Error"
#             subprocess.run(f"docker exec {cont_name} rm {file}",shell=True)

#         else:
#             # running the code on given input and taking the output in a variable in bytes
#             start = time()
#             try:
#                 res = subprocess.run(f"docker exec {cont_name} sh -c 'echo \"{testcase.input}\" | {exe}'",
#                                                 capture_output=True, timeout=problem.time_limit, shell=True)
#                 run_time = time()-start
#                 subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)
#             except subprocess.TimeoutExpired:
#                 run_time = time()-start
#                 verdict = "Time Limit Exceeded"
#                 subprocess.run(f"docker container kill {cont_name}", shell=True)
#                 subprocess.run(f"docker start {cont_name}",shell=True)
#                 subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)


#             if verdict != "Time Limit Exceeded" and res.returncode != 0:
#                 verdict = "Runtime Error"
                

#         user_stderr = ""
#         user_stdout = ""
#         if verdict == "Compilation Error":
#             user_stderr = cmp.stderr.decode('utf-8')
        
#         elif verdict == "Wrong Answer":
#             user_stdout = res.stdout.decode('utf-8')
#             if str(user_stdout)==str(testcase.output):
#                 verdict = "Accepted"
#             testcase.output += '\n' # added extra line to compare user output having extra ling at the end of their output
#             if str(user_stdout)==str(testcase.output):
#                 verdict = "Accepted"


#         # creating Solution class objects and showing it on leaderboard
#         user = User.objects.get(username=request.user)
#         previous_verdict = Submission.objects.filter(user=user.id, problem=problem, verdict="Accepted")
#         if len(previous_verdict)==0 and verdict=="Accepted":
#             user.save()

#         submission.verdict = verdict
#         submission.user_stdout = user_stdout
#         submission.user_stderr = user_stderr
#         submission.run_time = run_time
#         submission.save()
#         os.remove(filepath)
#         context={'verdict':verdict}
#         return render(request,'OJ/verdict.html',context)


# # ###############################################################################################################################


# def compile_code(container_name, compile_command):
#     # Run the compilation command inside the Docker container
#     result = subprocess.run(f"docker exec {container_name} {compile_command}", capture_output=True, shell=True)
#     return result.returncode == 0, result.stderr.decode("utf-8")


# def run_code(container_name, execution_command, input_data, timeout):
#     # Run the user code with the provided input inside the Docker container
#     try:
#         result = subprocess.run(
#             f"docker exec {container_name} sh -c 'echo \"{input_data}\" | {execution_command}'",
#             capture_output=True,
#             timeout=timeout,
#             shell=True,
#             text=True
#         )
#         return True, result.stdout.strip(), None
#     except subprocess.TimeoutExpired:
#         return False, None, "Time Limit Exceeded"
#     except Exception as e:
#         traceback.print_exc()
#         return False, None, "Runtime Error"


# @login_required(login_url='login')
# def verdictPage(request, problem_id):
#     if request.method == 'POST':
#         # Setting docker-client
#         docker_client = docker.from_env()
#         Running = "running"

#         problem = get_object_or_404(Problem, id=problem_id)
#         testcase = get_object_or_404(TestCase, problem_id=problem_id)
#         testcase.output = testcase.output.replace('\r\n', '\n').strip()  # Replace line endings for comparison

#         # Score of a problem
#         # if problem.difficulty == "Easy":
#         #     score = 10
#         # elif problem.difficulty == "Medium":
#         #     score = 30
#         # else:
#         #     score = 50

#         # Default verdict is "Wrong Answer"
#         verdict = "Wrong Answer"
#         run_time = 0

#         # Extract data from the form
#         form = CodeForm(request.POST)
#         user_code = ''
#         if form.is_valid():
#             user_code = form.cleaned_data.get('user_code')
#             user_code = user_code.replace('\r\n', '\n').strip()

#         language = request.POST['language']
#         submission = Submission(
#             user=request.user,
#             problem=problem,
#             submission_time=datetime.now(),
#             language=language,
#             user_code=user_code
#         )
#         submission.save()

#         filename = str(submission.id)

#         # Language-specific configurations
#         if language == "C++":
#             extension = ".cpp"
#             container_name = "oj-cpp"
#             compile_command = f"g++ -o {filename} {filename}.cpp"
#             execution_command = f"./{filename}"
#             docker_img = "gcc:11.2.0"

#         elif language == "Python3":
#             extension = ".py"
#             container_name = "oj-py3"
#             compile_command = "echo ''"  # No need to compile Python code
#             execution_command = f"python {filename}.py"
#             docker_img = "python3"

#         # File and Docker container configurations
#         file = filename + extension
#         filepath = os.path.join(settings.FILES_DIR, file)

#         # Write the user code to the file
#         with open(filepath, "w") as code:
#             code.write(user_code)

#         # Check if the Docker container is running, start if not found
#         try:
#             container = docker_client.containers.get(container_name)
#             container_state = container.attrs['State']
#             container_is_running = container_state['Status'] == Running
#             if not container_is_running:
#                 subprocess.run(f"docker start {container_name}", shell=True)
#         except docker.errors.NotFound:
#             subprocess.run(f"docker run -dt --name {container_name} {docker_img}", shell=True)

#         # Copy the file to the Docker container
#         subprocess.run(f"docker cp {filepath} {container_name}:/{file}", shell=True)

#         # Compile the code
#         compiled_successfully, compile_error_msg = compile_code(container_name, compile_command)
#         if not compiled_successfully:
#             verdict = "Compilation Error"

#         else:
#             # Run the code on the given input and take the output
#             start_time = time()
#             execution_successful, user_stdout, run_error_msg = run_code(container_name, execution_command,
#                                                                         testcase.input, problem.time_limit)
#             run_time = time() - start_time

#             # Remove the compiled binary or Python script from the container
#             subprocess.run(f"docker exec {container_name} rm {file}", shell=True)

#             if not execution_successful:
#                 verdict = run_error_msg

#             elif user_stdout.strip() == testcase.output.strip():
#                 verdict = "Accepted"

#         # Clean up the file after running
#         os.remove(filepath)

#         # Handling leaderboard and other score-related operations (as before)

#         context = {'verdict': verdict}
#         return render(request, 'OJ/verdict.html', context)

def verdictPage(request, problem_id):
    if request.method == 'POST':
        # setting docker-client
        docker_client = docker.from_env()
        Running = "running"

        problem = Problem.objects.get(id=problem_id)
        testcase = TestCase.objects.get(problem_id=problem_id)
        #replacing \r\n by \n in original output to compare it with the usercode output
        testcase.output = testcase.output.replace('\r\n','\n').strip() 

        # score of a problem
        # if problem.difficulty=="Easy":
        #     score = 10
        # elif problem.difficulty=="Medium":
        #     score = 30
        # else:
        #     score = 50


        #setting verdict to wrong by default
        verdict = "Wrong Answer" 
        res = ""
        run_time = 0

        # extract data from form
        form = CodeForm(request.POST)
        user_code = ''
        if form.is_valid():
            user_code = form.cleaned_data.get('user_code')
            user_code = user_code.replace('\r\n','\n').strip()
            
        language = request.POST['language']
        submission = Submission(user=request.user, problem=problem, submission_time=datetime.now(), 
                                    language=language, user_code=user_code)
        submission.save()

        filename = str(submission.id)

        # if user code is in C++
        if language == "C++":
            extension = ".cpp"
            cont_name = "oj-cpp"
            compile = f"g++ -o {filename} {filename}.cpp"
            clean = f"{filename} {filename}.cpp"
            docker_img = "gcc:11.2.0"
            exe = f"./{filename}"
            
        elif language == "C":
            extension = ".c"
            cont_name = "oj-c"
            compile = f"gcc -o {filename} {filename}.c"
            clean = f"{filename} {filename}.c"
            docker_img = "gcc:11.2.0"
            exe = f"./{filename}"

        elif language == "Python3":
            extension = ".py"
            cont_name = "oj-py3"
            compile = "python3"
            clean = f"{filename}.py"
            docker_img = "python3"
            exe = f"python {filename}.py"
        
        elif language == "Python2":
            extension = ".py"
            cont_name = "oj-py2"
            compile = "python2"
            clean = f"{filename}.py"
            docker_img = "python2"
            exe = f"python {filename}.py"

        elif language == "Java":
            filename = "Main"
            extension = ".java"
            cont_name = "oj-java"
            compile = f"javac {filename}.java"
            clean = f"{filename}.java {filename}.class"
            docker_img = "openjdk"
            exe = f"java {filename}"


        file = filename + extension
        filepath = settings.FILES_DIR + "/" + file
        code = open(filepath,"w")
        code.write(user_code)
        code.close()

        # checking if the docker container is running or not
        try:
            container = docker_client.containers.get(cont_name)
            container_state = container.attrs['State']
            container_is_running = (container_state['Status'] == Running)
            if not container_is_running:
                subprocess.run(f"docker start {cont_name}",shell=True)
        except docker.errors.NotFound:
            subprocess.run(f"docker run -dt --name {cont_name} {docker_img}",shell=True)


        # copy/paste the .cpp file in docker container 
        subprocess.run(f"docker cp {filepath} {cont_name}:/{file}",shell=True)

        # compiling the code
        cmp = subprocess.run(f"docker exec {cont_name} {compile}", capture_output=True, shell=True)
        if cmp.returncode != 0:
            verdict = "Compilation Error"
            subprocess.run(f"docker exec {cont_name} rm {file}",shell=True)

        else:
            # running the code on given input and taking the output in a variable in bytes
            start = time()
            try:
                res = subprocess.run(f"docker exec {cont_name} sh -c 'echo \"{testcase.input}\"'",
                                                capture_output=True, timeout=problem.time_limit, shell=True)
                run_time = time()-start
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)
            except subprocess.TimeoutExpired:
                run_time = time()-start
                verdict = "Time Limit Exceeded"
                subprocess.run(f"docker container kill {cont_name}", shell=True)
                subprocess.run(f"docker start {cont_name}",shell=True)
                subprocess.run(f"docker exec {cont_name} rm {clean}",shell=True)

            
            if verdict != "Time Limit Exceeded" and res.returncode != 0:
                verdict = "Runtime Error"
                

        user_stderr = ""
        user_stdout = ""
        if verdict == "Compilation Error":
            user_stderr = cmp.stderr.decode('utf-8')
        
        elif verdict == "Wrong Answer":
            user_stdout = res.stdout.decode('utf-8')
            if str(user_stdout)==str(testcase.output):
                verdict = "Accepted"
            testcase.output += '\n' # added extra line to compare user output having extra ling at the end of their output
            if str(user_stdout)==str(testcase.output):
                verdict = "Accepted"


       

        submission.verdict = verdict
        submission.user_stdout = user_stdout
        submission.user_stderr = user_stderr
        submission.run_time = run_time
        submission.save()
        os.remove(filepath)
        context={'verdict':verdict}
        return render(request,'OJ/verdict.html',context)
