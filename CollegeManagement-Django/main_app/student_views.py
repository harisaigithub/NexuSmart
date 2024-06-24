import json
import math
from datetime import datetime

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *

from .forms import NoteForm
from .models import Note
from .models import MCQQuestion
from .models import MCQQuestion, UploadedFile
from .forms import ContentForm
from .forms import UploadFileForm
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
import os
import random
import spacy
#from openai import OpenAI,OpenAIError
from PyPDF2 import PdfReader
import langdetect
from langdetect import detect, DetectorFactory, LangDetectException
from django.utils import translation
import nltk
from nltk.tokenize import sent_tokenize
import fitz
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob 



nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')


DetectorFactory.seed = 0

nlp_en = spacy.load('en_core_web_sm')
nlp_es = spacy.load('es_core_news_sm')


def student_home(request):
    student = get_object_or_404(Student, admin=request.user)
    total_subject = Subject.objects.filter(course=student.course).count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(student=student, status=True).count()
    if total_attendance == 0:
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    subject_name = []
    data_present = []
    data_absent = []
    subjects = Subject.objects.filter(course=student.course)
    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=True, student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status=False, student=student).count()
        subject_name.append(subject.name)
        data_present.append(present_count)
        data_absent.append(absent_count)
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'subjects': subjects,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Student Homepage'
    }
    return render(request, 'student_template/home_content.html', context)



@ csrf_exempt
def student_view_attendance(request):
    student = get_object_or_404(Student, admin=request.user)
    if request.method != 'POST':
        course = get_object_or_404(Course, id=student.course.id)
        context = {
            'subjects': Subject.objects.filter(course=course),
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        subject_id = request.POST.get('subject')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        try:
            subject = get_object_or_404(Subject, id=subject_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), subject=subject)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date":  str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            return None


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, admin=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(request, "Error Occured While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, admin=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, admin=request.user)
    results = StudentResult.objects.filter(student=student)
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)



def student_mcq_ask(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = form.save()  # Save the uploaded file instance
            questions = handle_uploaded_file(uploaded_file)  # Pass the UploadedFile instance
            return render(request, 'student_template/student_generate_mcq.html', {'questions': questions})
    else:
        form = UploadFileForm()
    return render(request, 'student_template/student_mcq_ask.html', {'form': form})

def handle_uploaded_file(uploaded_file):
    questions = []
    file_path = uploaded_file.file.path  # Get the full path to the uploaded file

    # Open the PDF file
    try:
        with fitz.open(file_path) as pdf_document:
            content = ""
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                content += page.get_text()

    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return questions

    sentences = sent_tokenize(content)
    key_terms = extract_key_terms(sentences)

    question_count = 0
    used_sentences = set()

    while question_count < 20:
        for key_term in key_terms:
            if question_count >= 20:
                break
            question, options, correct_option = generate_question(key_term, sentences, used_sentences)
            if question and options:
                mcq_question = MCQQuestion(
                    question=question,
                    option1=options[0],
                    option2=options[1],
                    option3=options[2],
                    option4=options[3],
                    correct_option=correct_option,
                    difficulty='easy',  # Set difficulty statically
                    uploaded_file=uploaded_file  # Set the uploaded file
                )
                mcq_question.save()
                questions.append(mcq_question)
                question_count += 1
                used_sentences.add(question)

    return questions

def extract_key_terms(sentences):
    key_terms = []
    for sentence in sentences:
        blob = TextBlob(sentence)
        nouns = [word for word, tag in blob.tags if tag.startswith('NN')]
        key_terms.extend(nouns)
    return list(set(key_terms))

def generate_question(key_term, sentences, used_sentences):
    for sentence in sentences:
        if key_term in sentence and sentence not in used_sentences:
            question = sentence.replace(key_term, "__________")
            correct_option = key_term
            options = generate_options(correct_option, sentences)
            if options and correct_option not in options:
                options.append(correct_option)
            random.shuffle(options)
            return question, options, correct_option
    return None, None, None

def generate_options(correct_option, sentences):
    options = []
    blob = TextBlob(" ".join(sentences))
    words = [word for word, tag in blob.tags if tag.startswith('NN') or tag.startswith('VB')]
    words = [word for word in words if word.lower() not in stopwords.words('english') and word != correct_option]
    options = random.sample(words, min(3, len(words)))
    return options

def student_generate_mcq(request):
    questions = MCQQuestion.objects.all()  # Retrieve all MCQ questions from database
    return render(request, 'student_template/student_generate_mcq.html', {'questions': questions})

def student_quiz_result(request):
    if request.method == 'POST':
        score = 0
        total_questions = 0
        for key, value in request.POST.items():
            if key.startswith('question_'):
                question_id = key.split('_')[1]
                selected_option = value
                question = MCQQuestion.objects.get(id=question_id)
                total_questions += 1
                if selected_option == question.correct_option:
                    score += 1
        return render(request, 'student_template/student_quiz_result.html', {'score': score, 'total': total_questions})
    return redirect('student_mcq_ask')