from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission #
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
from . import models
import random
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Get user and course object, then get the associated enrollment object created when the user enrolled the course
         # Create a submission object referring to the enrollment
         # Collect the selected choices from exam form
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id
def submit(request, course_id):
        user = request.user
        course = get_object_or_404(Course, pk=course_id)
        #print("Course:",type(course))
        enrollment = Enrollment.objects.get(user=user, course=course)
        submission = Submission.objects.create(enrollment=enrollment)
        selected_choice = extract_answers(request)
        submission.choices.add(*selected_choice)
        submission.save()
        #print(submission.choices)
        #print("Submission:",type(submission))
        #selected = request.POST['selected'] ###### no POST["selected"]  你自己加架啦  原本deg submit係空既
        #submission = Submission.objects.create_user(username=username, first_name=first_name, last_name=last_name,
        #                                   password=password) ## I added this myself 我都唔知係邊copy返黎
        ## submission = Submission.objects.create(submitted_answers)1234
        #return redirect('onlinecourse:show_exam_result', course.id,xx=context)
        return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id,submission.id,)))  ## 11 AUG added
        

# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    #print(submitted_anwsers)
    return submitted_anwsers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
def show_exam_result(request, course_id, submission_id):
    #print(submission_id)
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    answer=submission.choices.all()  ## This line returns "<QuerySet [<Choice: Choice object (1)>, <Choice: Choice object (2)>]>"
    full_score,score=0,0
    for q in course.question_set.all():
        #print("outside Model Ans",q.choice_set.filter(is_correct=True))
        #print("outside Your Choice",q.choice_set.filter(id__in=answer))
        if q.is_get_score(answer):
            score+=q.grade
        full_score+=q.grade
        #print(score,"/",full_score)
    grade=score/full_score*100
    #print(answer[:])
    #course.question.choice_set.filter(is_correct=True)
    
    context = {}
    context['total_score']=int(grade)
    context['course']=course
    context['submission']=submission


    #use zup function and double for loop in html template to mark the text colour
    #example as follow for zip function
    #https://www.w3schools.com/python/ref_func_zip.asp
    item1 = []
    item2=[]
    length=0
    n=1
    for i in course.question_set.all():
        #text="Q"+str(n)
        item1.append(i.question_text)
        n+=1
        length=max(length,(len(i.choice_set.all())))
        n2=1
        b=[""]*length
        c=[""]*length
        for j in i.choice_set.all():
            #text2="C"+str(n2)+"_"+str(n-1)##Choice_text here
            b[n2-1]=j.choice_text
            c[n2-1]=random.randint(1, 9)##Colour Text here
            n2+=1
        d=list(zip(b,c))
        item2.append(d)
    #print(item1)
    #print(item2)
    item_master=list(zip(item1,item2))
    #print(len(list(item_master)))
    for i1 in list(item_master):
        pass
        #print(i1[0])
        for i2 in i1[1]:
        #    print("Choice inside",i2)
            pass
    b = ["C1","C2","C3"]
    c = [1,2,3]
    x = list(zip(b, c)) #or even zip 3 or more
    y = zip(item1,x)
    print(x)
    print("\n",item_master[0])
    context['liste']=x
    context['item_master']=item_master
    context['colourful']="green"
    #print(list(y))
    #use the tuple() or list() function to display a readable version of the result:
    #print(list(x))
    #use function to determine colour and match question text to it.
    #this list should contain For example:
    #1:["green","green","black"]
    #2:[course.question_set.choice_text[0],course.question_set.choice_text[1],course.question_set.choice_text[2]]
    #Merge into [("green",choice_text0),("green",choice_text1),("black",choice_text2)]


    #double for loop function
    #https://github.com/gabrielgrant/django-multiforloop
    #https://stackoverflow.com/questions/14079815/using-for-in-template-with-two-variables-django
    #return render_to_response('template.html', {'liste': mylist, ...   below
    #{% for item1, item2 in liste %}   in the tempalte




    # In redirect, you can only pass through args that exists in the url.
    #'<int:course_id>/submit/' --> only pass through one argument which is course_id
    #'course/<int:course_id>/submission/<int:submission_id>/result/' pass through two args, course_id and submission_id
    # in render, the pass through argument is a Dictionary (e.g. context)
    # It is a dictionary, you can pass through anything, from int, string to array,list, even object.
    # In this case, passed through object is query_set from CRUD action.
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)



