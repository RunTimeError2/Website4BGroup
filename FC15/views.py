#coding=utf-8
from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect, StreamingHttpResponse
from django.template import RequestContext
from django.contrib import messages

from FC15.models import UserInfo, TeamInfo, FileInfo, BlogPost, EmailActivate, PasswordReset, TeamRequest, GameRecord
from FC15.forms import BlogPostForm, UserLoginForm, UserRegistForm, FileUploadForm, CreateTeamForm, ResetPasswordForm, ChangeForm, TeamRequestForm
from FC15.sendmail import mail_activate, password_reset, random_string
from FC15.forms import flash
from FC15.oj import run, copy_all_exe, play_game, delete_exe, FILE_SUFFIX, run_game_queue, run_allgame
import time, os, random


AUTO_COMPILE = True
EMAIL_ACTIVATE = True
TSINGHUA_ONLY = True
MAX_TEAM_MEMBER_NUMBER = 3


# All of the views

# Home page
def home(request):
    username = request.COOKIES.get('username', '')
    posts1 = BlogPost.objects.all()[: 2]
    posts2 = BlogPost.objects.all()[2: 4]
    return render(request, 'home.html', {'posts1': posts1, 'posts2': posts2, 'username': username})


# Login
def login(request):
    current_username = request.COOKIES.get('username', '')
    if current_username != '':
        flash(request, 'Error', 'You have already login! Please logout first.')
        return HttpResponseRedirect('/index/')
    if request.method == 'POST':
        userform = UserLoginForm(request.POST)
        if userform.is_valid():
            username = userform.cleaned_data['username']
            password = userform.cleaned_data['password']

            user = UserInfo.objects.filter(username__exact = username, password__exact = password)

            if user:
                user_exact = UserInfo.objects.get(username = username, password = password)
                if user_exact.activated:
                    response = HttpResponseRedirect('/index/')
                    # User will automatically login within 1 hour
                    response.set_cookie('username', username, 3600)
                    response.set_cookie('tmp_username', '', 7200)
                    return response
                else:
                    response = HttpResponseRedirect('/login/')
                    response.set_cookie('tmp_username', username, 600)
                    flash(request, 'Error', 'This user account has not been activated!', 'error')
                    return response
                #    return HttpResponse('This user account has not been activated!')
            else:
                flash(request, 'Error', 'Incorrect username or password, please retry.', 'error')
                #return HttpResponseRedirect('/login/')
                #return HttpResponse('Incorrect username or password, please retry.')
    else:
        userform = UserLoginForm()
    return render(request, 'login.html', {'form': userform})


# Logout
def logout(request):
    response = HttpResponseRedirect('/home/')
    flash(request, 'Success', 'Logout successfully', 'success')
    response.delete_cookie('username')
    return response


# Register
def regist(request):
    if request.method == 'POST':
        userform = UserRegistForm(request.POST)
        un = request.POST['username']
        print(un)
        if userform.is_valid():
            username = userform.cleaned_data['username']
            realname = userform.cleaned_data['realname']
            password = userform.cleaned_data['password']
            email = userform.cleaned_data['email']
            stu_number = userform.cleaned_data['stu_number']
            password_confirm = userform.cleaned_data['password_confirm']

            if password == password_confirm:
                existing_user = UserInfo.objects.filter(username__exact = username)
                username_invalid = False
                if existing_user:
                    for user in existing_user:
                        if user.activated:
                            username_invalid = True
                if username_invalid:
                    flash(request, 'Error', 'The username already exists!', 'error')
                    return render(request, 'regist.html', {'form': userform})
                    #return HttpResponse('Error! The username already exists')

                existing_realname = UserInfo.objects.filter(realname__exact = realname, activated = True)
                if existing_realname:
                    flash(request, 'Error', 'The realname already exists!', 'error')
                    return render(request, 'regist.html', {'form': userform})

                existing_email = UserInfo.objects.filter(email__exact = email)
                email_invalid = False
                if existing_email:
                    for email in existing_email:
                        if email.activated:
                            email_invalid = True
                if email_invalid:
                    flash(request, 'Error', 'The email address has already been used!', 'error')
                    return render(request, 'regist.html', {'form': userform})
                    #return HttpResponse('Error! The email address has already been used!')

                # Judge if the student number is valids
                if stu_number.isdigit() and len(stu_number) == 10:
                    pass
                else:
                    flash(request, 'Error', 'Incorrect format of student number!')
                    return render(request, 'regist.html', {'form': userform})

                existing_stunumber = UserInfo.objects.filter(stu_number__exact = stu_number)
                stunumber_invalid = False
                if existing_stunumber:
                    for stunumber in existing_stunumber:
                        if stunumber.activated:
                            stunumber_invalid = True
                if stunumber_invalid:
                    flash(request, 'Error', 'One student number can only be used once!', 'error')
                    return render(request, 'regist.html', {'form': userform})

                # Judge if the email address belongs to Tsinghua mailbox
                if TSINGHUA_ONLY:
                    low_email = email.lower()
                    if len(low_email) < 15 or low_email[-15:] != 'tsinghua.edu.cn':
                        flash(request, 'Error', 'Only addresses of Tsinghua mailbox will be accepted.')
                        return render(request, 'regist.html', {'form': userform})

                print('Regist: username={0}, realname={1}'.format(username, realname))

                # Delete user that are not activated and has the same information
                existing_username = UserInfo.objects.filter(username__exact = username, activated = False)
                for item in existing_username:
                    item.delete()
                existing_email = UserInfo.objects.filter(email__exact = email, activated = False)
                for item in existing_email:
                    item.delete()
                existing_stunumber = UserInfo.objects.filter(stu_number__exact = stu_number, activated = False)
                for item in existing_stunumber:
                    item.delete()
                existing_realname = UserInfo.objects.filter(realname__exact = realname, activated = False)
                for item in existing_realname:
                    item.delete()

                # Switch whether the account should be activated with email
                if EMAIL_ACTIVATE:
                    new_user = UserInfo()
                    new_user.username = username
                    new_user.password = password
                    new_user.email = email
                    new_user.stu_number = stu_number
                    new_user.realname = realname
                    new_user.activated = False
                    new_user.save()
                    #UserInfo.objects.create(username = username, realname = realname, password = password, email = email, stu_number = stu_number, activated = False)
                    mail_activate(email, username)
                    flash(request, 'Success', 'The confirmation email has been successfully sent. Please check you email!')
                else:
                    new_user = UserInfo()
                    new_user.username = username
                    new_user.password = password
                    new_user.email = email
                    new_user.stu_number = stu_number
                    new_user.realname = realname
                    new_user.activated = True
                    new_user.save()
                    #UserInfo.objects.create(username = username, realname = realname, password = password, email = email, stu_number = stu_number, activated = True)
                    flash(request, 'Success', 'Your account has been successfully created.')

                return HttpResponseRedirect('/login/')
                #return HttpResponse('Regist success! Please check your email.')
            else:
                flash(request, 'Error', 'You should enter the same password!')
                return HttpResponseRedirect('/regist/')
        else:
            flash(request, 'Error', 'Please complete the form and then submit.')
            print('userform is invalid')
    else:
        userform = UserRegistForm()
    return render(request, 'regist.html', {'form': userform})


# About page
#def about(request):
#    return render(request, 'about.html')


# Introduction of game rule
def about_rule(request):
    return render(request, 'about_rule.html')


# Introduction for DAASTA
def about_story(request):
    return render(request, 'about_story.html')


# Introduction for the sponsor
def about_sponsor(request):
    return render(request, 'about_sponsor.html')


# Documents of the game
def document(request):
    return render(request, 'document.html')


# Activate account with email
def activate(request, activate_code):
    #activate_record = EmailActivate.objects.get(activate_string = activate_code)
    activate_record = get_object_or_404(EmailActivate, activate_string = activate_code)
    if activate_record:
        username = activate_record.username
        #user = UserInfo.objects.get(username = username)
        user = get_object_or_404(UserInfo, username = username)
        if user:
            user.activated = True
            user.save()
            activate_record.delete()
            flash(request, 'Success', 'You have successfully activated the account!')
            return HttpResponseRedirect('/login/')
            #return HttpResponse('You have successfully activated the account!')
        else:
            flash(request, 'Error', 'Invalid activating code!')
            return HttpResponseRedirect('/home/')
            #return HttpResponse('Invalid activating code!')
    else:
        return HttpResponse('Invalid activating url!')


# Fill in the request to reset password
def resetrequest(request):
    username = request.COOKIES.get('username', '')
    if request.method == 'POST':
        userform = ResetPasswordForm(request.POST)
        if userform.is_valid():
            username = userform.cleaned_data['username']
            email = userform.cleaned_data['email']
            user = UserInfo.objects.filter(username__exact = username, email__exact = email)
            if user:
                password_reset(email, username)
                flash(request, 'Success', 'The email has been send, please check you email!')
                return HttpResponseRedirect('/home/')
                #return HttpResponse('Success! Please check your email.')
            else:
                flash(request, 'Error', 'Incorrect user information!')
                return HttpResponseRedirect('/resetrequest/')
                #return HttpResponse('Error! Incorrect user information!')
    else:
        userform = ResetPasswordForm()
    return render(request, 'resetrequest.html', {'username': username, 'form': userform})


# Reset the password
def resetpassword(request, reset_code):
    reset_record = PasswordReset.objects.get(reset_string = reset_code)
    if reset_record:
        user = UserInfo.objects.get(username = reset_record.username)
        user.password = reset_record.new_password
        user.save()
        reset_record.delete()
        flash(request, 'Success', 'Your password has been successfully reset!\nPlease change your password after you login.', 'success')
        return HttpResponseRedirect('/login/')
        #return HttpResponse('Your password has been successfully reset!\nPlease change your password after you login.')
    else:
        flash(request, 'Error', 'Invalid reset code!', 'error')
        return HttpResponseRedirect('/home/')
        #return HttpResponse('Error! Invalid reset code!')


# Change the password or email
def change(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    user = UserInfo.objects.get(username = username)
    if request.method == 'POST':
        userform = ChangeForm(request.POST)
        if userform.is_valid():
            old_password = userform.cleaned_data['old_password']
            new_password = userform.cleaned_data['new_password']
            confirm_password = userform.cleaned_data['confirm_password']
            if old_password != user.password:
                flash(request, 'Error', 'Incorrect old password!', 'error')
                return render(request, 'change.html', {'username': username, 'form': userform})
                #return HttpResponse('Error! Incorrect old password')
            if new_password != confirm_password:
                flash(request, 'Error', 'Please enter the same password!', 'error')
                return render(request, 'change.html', {'username': username, 'form': userform})
                #return HttpResponse('Error! Please enter the same password')
            user.password = new_password
            user.email = userform.cleaned_data['email']
            user.save()
            flash(request, 'Success', 'You have successfully changed your account. Please login.', 'success')
            response = HttpResponseRedirect('/login/')
            response.delete_cookie('username')
            return response
        else:
            flash(request, 'Error', 'Please complete the form!', 'error')
            return render(request, 'change.html', {'username': username, 'form': userform})
    else:
        userform = ChangeForm(data = {'email': user.email})
    return render(request, 'change.html', {'username': username, 'form': userform})


# To index page
def index(request):
    #return render(request, 'index2.html') #================================================
    #return render(request, 'index.html')
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    posts = BlogPost.objects.filter(username__exact = username)
    files = FileInfo.objects.filter(username__exact = username)
    me = get_object_or_404(UserInfo, username = username)
    if me.team == '':
        warning = 'You have not joined a team yet'
        return render(request, 'userindex.html', {'username': username, 'posts': posts, 'files': files, 'warning': warning})
    else:
        warning = ''
        codes = FileInfo.objects.filter(teamname__exact = me.team).exclude(username = username)
        return render(request, 'userindex.html', {'username': username, 'posts': posts, 'files': files, 'warning': '', 'codes': codes})


# Uplaod file
def upload(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    if request.method == 'POST':
        userform = FileUploadForm(request.POST, request.FILES)
        if userform.is_valid():
            #limit the size and type of file to be uploaded
            myfile = request.FILES.get('file', None)
            if myfile:
                if myfile.size >= 1048576:
                    flash(request, 'Error', 'File should not be larger than 1 MiB.', 'error')
                    return render(request, 'upload.html', {'username': username, 'form': userform})
                    #return HttpResponse('Error! File should not be larger than 1 MiB')
                if myfile.name.endswith('.cpp') == False:
                    flash(request, 'Error', 'Only .cpp file will be accepted.', 'error')
                    return render(request, 'upload.html', {'username': username, 'form': userform})
                    #return HttpResponse('Error! Only .cpp file will be accepted.')
            else:
                flash(request, 'Error', 'File does not exist.', 'error')
                return render(request, 'upload.html', {'username': username, 'form': userform})
                #return HttpResponse('Error! File does not exist.')

            user = get_object_or_404(UserInfo, username = username)
            fileupload = FileInfo()
            fileupload.filename = userform.cleaned_data['filename']
            fileupload.username = username
            fileupload.teamname = user.team
            fileupload.description = userform.cleaned_data['description']
            fileupload.file = userform.cleaned_data['file']
            fileupload.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            fileupload.is_compiled = 'Not compiled'
            fileupload.is_compile_success = ''
            fileupload.compile_result = ''
            fileupload.save()
            flash(request, 'Success', 'You have successfully uploaded the code.', 'success')
            global AUTO_COMPILE
            if AUTO_COMPILE:
                run()
            return HttpResponseRedirect('/index/')
            #return HttpResponse('Upload success!')
        else:
            pass
    else:
        userform = FileUploadForm()
        username = request.COOKIES.get('username', '')
        if username == '':
            return HttpResponseRedirect('/login/')
    return render(request, 'upload.html', {'username': username, 'form': userform, 'filename': '', 'description': ''})


# Edit a file
def fileedit(request, pk):
    file = get_object_or_404(FileInfo, pk = pk)
    username = request.COOKIES.get('username', '')
    filename = file.filename
    description = file.description
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    if username != file.username:
        flash(request, 'Error', 'You can only edit your own file.', 'error')
        return HttpResponseRedirect('/index/')
        #return HttpResponse('Error! You can only edit your own file.')
    if request.method == 'POST':
        userform = FileUploadForm(request.POST, request.FILES)

        #limit the size and type of file to be uploaded
        myfile = request.FILES.get('file', None)
        if myfile:
            if myfile.size >= 1048576:
                flash(request, 'Error', 'File should not be larger than 1 MiB', 'error')
                return render(request, 'upload.html', {'username': username, 'form': userform, 'filename': filename, 'description': description})
                #return HttpResponse('Error! File should not be larger than 1 MiB')
            if myfile.name.endswith('.cpp') == False:
                flash(request, 'Error', 'Only .cpp file is accepted.', 'error')
                return render(request, 'upload.html', {'username': username, 'form': userform, 'filename': filename, 'description': description})
                #return HttpResponse('Error! Only .cpp file is accepted.')
        else:
            flash(request, 'Error', 'File does not exist.', 'error')
            return render(request, 'upload.html', {'username': username, 'form': userform, 'filename': filename, 'description': description})
            #return HttpResponse('Error! File does not exist.')

        if userform.is_valid():
            # delete old file
            os.remove(file.path)
            if os.path.exists(file.path[:-4] + '.exe'):
                os.remove(file.path[:-4] + '.exe')
            delete_exe(file) # delete copied executable file in /playgame directory

            file.filename = userform.cleaned_data['filename']
            file.description = userform.cleaned_data['description']
            file.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            file.file = userform.cleaned_data['file']
            file.is_compiled = 'Not compiled'
            file.is_compile_success = ''
            file.compile_result = ''
            file.save()
            flash(request, 'Success', 'You have successfully edited the file', 'success')
            global AUTO_COMPILE
            if AUTO_COMPILE:
                run()
            return HttpResponseRedirect('/index/')
            #return HttpResponse('File edited successfully')
    else:
        userform = FileUploadForm(data = {'filename': file.filename, 'description': file.description, 'file': file.file})
    return render(request, 'upload.html', {'username': username, 'form': userform, 'filename': filename, 'description': description})


# Delete a file
def filedelete(request, pk):
    file = get_object_or_404(FileInfo, pk = pk)
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    if username != file.username:
        flash(request, 'Error', 'You can only delete your own file.', 'error')
        return HttpResponseRedirect('/index/')
        #return HttpResponse('Error! You can only delete your own file.')

    # Delete source file
    if os.path.exists(file.path):
        os.remove(file.path)
    # Delete executable file in user folder
    global FILE_SUFFIX
    if os.path.exists(file.path[:-4] + '.' + FILE_SUFFIX):
        os.remove(file.path[:-4] + '.' + FILE_SUFFIX)
    # Delete executable file in 'playgame' folder
    if os.path.exists('playgame/{0}.{1}'.format(pk, FILE_SUFFIX)):
        os.remove('playgame/{0}.{1}'.format(pk, FILE_SUFFIX))
    file.delete()
    flash(request, 'Success', 'You have successfully deleted the file.', 'success')
    return HttpResponseRedirect('/index/')


# Download a file
def filedownload(request ,pk):
    def file_iterator(file_name, chunk_size = 2048):  
        with open(file_name) as f:  
            while True:  
                c = f.read(chunk_size)  
                if c:
                    yield c
                else:
                    break  

    file = get_object_or_404(FileInfo, pk = pk)
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = get_object_or_404(UserInfo, username = username)
    authors = UserInfo.objects.filter(username__exact = file.username)
    if authors:
        author = UserInfo.objects.get(username = username)
    else:
        author = None
        flash(request, 'Error', 'Invalid code! The author of the code does not exist.')
        return HttpResponseRedirect('/index/')
    #author = get_object_or_404(UserInfo, username = file.username)
    if username != file.username:
        if author.team == '' or me.team == '' or author.team != me.team:
            flash(request, 'Error', 'You can only download your own file or code of your teammates!')
            return HttpResponseRedirect('/index/')
            #return HttpResponse('Error! You can only download your own file.')
    response = StreamingHttpResponse(file_iterator(file.path))  
    response['Content-Type'] = 'application/octet-stream'  
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file.origin_name)
    return response


# View all blogs
def viewblogs(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    blogs = BlogPost.objects.all()
    #return render(request, 'viewblogs.html', {'username': username, 'blogs': blogs})
    return render(request, 'viewblogs.html', {'username': username, 'blogs': blogs})


# Post a blog
def postblog(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    if request.method == 'POST':
        userform = BlogPostForm(request.POST)
        if userform.is_valid():
            blogpost = BlogPost()
            blogpost.title = userform.cleaned_data['title']
            blogpost.content = userform.cleaned_data['content']
            blogpost.username = username
            blogpost.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            blogpost.save()
            flash(request, 'Success', 'The blog has been successfully posted.')
            return HttpResponseRedirect('/index/')
            #return HttpResponse('Blog posted successfully')\
        else:
            print('Invalid userform')
    else:
        userform = BlogPostForm()
    return render(request, 'blogpost.html', {'username': username, 'form': userform, 'title': '', 'content': ''})


# Return an 'unfinished' message
def unfinished(request):
    return HttpResponse('Oh, this function has not been finished yet!')


# Show the detail of a blog
def blogdetail(request, pk):
    username = request.COOKIES.get('username', '')
    post = get_object_or_404(BlogPost, pk = pk)
    background_image_count = 2
    bg_index = random.randint(1, background_image_count)
    bg_filename = 'blog-bg-' + str(bg_index) + '.jpg'
    return render(request, 'blogdetail.html', {'post': post, 'username': username, 'bgname': bg_filename})


# Edit a blog
def blogedit(request, pk):
    post = get_object_or_404(BlogPost, pk = pk)
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    if username != post.username:
        flash(request, 'Error', 'You can only edit you own blog!')
        return HttpResponseRedirect('/index/')
        #return HttpResponse('Error! You can only edit your own blog.')
    if request.method == 'POST':
        userform = BlogPostForm(request.POST)
        if userform.is_valid():
            post.title = userform.cleaned_data['title']
            post.content = userform.cleaned_data['content']
            post.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            post.save()
            return render(request ,'blogdetail.html', {'post': post})
    else:
        userform = BlogPostForm(data = {'title': post.title, 'content': post.content})
    return render(request, 'blogpost.html', {'username': username, 'form': userform, 'title': post.title, 'content': post.content})


# Delete a blog
def blogdelete(request, pk):
    post = get_object_or_404(BlogPost, pk = pk)
    post.delete()
    return HttpResponseRedirect('/index/')


# View the list of all teams
def team(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = UserInfo.objects.get(username = username)
    myteams = TeamInfo.objects.filter(captain__exact = username)
    if myteams:
        myteam = TeamInfo.objects.get(captain = username)
    else:
        myteam = None
    if TeamInfo.objects.filter(teamname__exact = me.team):
        joinedteam = TeamInfo.objects.get(teamname = me.team)
    else:
        joinedteam = None
    teams = TeamInfo.objects.all()
    return render(request, 'team.html', {'username': username, 'myteam': myteam,'joinedteam': joinedteam, 'teams': teams})


# Create a team
def createteam(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    myteam = TeamInfo.objects.filter(captain__exact = username)

    # Creating or joining more than one team is not allowed
    if myteam:
        flash(request, 'Error', 'You have already created a team', 'error')
        return HttpResponseRedirect('/team/')
        #return HttpResponse('You have already created a team!')
    me = get_object_or_404(UserInfo, username = username)
    if me.team != '':
        my_current_team = TeamInfo.objects.filter(teamname__exact = me.team)
        if my_current_team:
            flash(request, 'Error', 'You have already joined a team', 'error')
            return HttpResponseRedirect('/team/')
        else:
            flash(request, 'Error', 'Your current team does not exist, now you do not belong to any team lol.')
            me.team = ''
            me.save()
        #return HttpResponse('You have already joined a team!')

    if request.method == 'POST':
        userform = CreateTeamForm(request.POST)
        if userform.is_valid():
            newteam = TeamInfo()
            newteam.teamname = userform.cleaned_data['teamname']
            newteam.introduction = userform.cleaned_data['introduction']
            newteam.captain = username
            newteam.members = 1
            newteam.save()
            me = UserInfo.objects.get(username = username)
            me.team = newteam.teamname
            me.save()
            updatecodeteaminfo() #================================================
            flash(request, 'Success', 'Team created successfully', 'success')
            return HttpResponseRedirect('/team/')
            #return HttpResponse('Team created successfully')
    else:
        userform = CreateTeamForm()
    return render(request, 'createteam.html', {'form': userform})


# Join a team
def jointeam(request, pk):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = get_object_or_404(UserInfo, username = username)
    if me.team:
        pass
    else:
        my_current_team = TeamInfo.objects.filter(teamname__exact = me.team)
        if my_current_team:
            flash(request, 'Error', 'You have already joined a team', 'error')
            return HttpResponseRedirect('/team/')
        else:
            flash(request, 'Error', 'Your current team does not exist, now you do not belong to any team lol.')
            me.team = ''
            me.save()
        #return HttpResponse('You have already joined a team!')
    team = get_object_or_404(TeamInfo, pk = pk)
    # userform = TeamRequestForm(data = {'destin_team': team.teamname})
    userform = TeamRequestForm()
    print('teamname = {0}'.format(team.teamname))
    return render(request, 'teamrequest.html', {'username': username, 'form': userform, 'destin_team': team.teamname})


# Send a request to join the team
def jointeamrequest(request, pk):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    destin_team = ''
    me = get_object_or_404(UserInfo, username = username)
    if me.team:
        my_current_team = TeamInfo.objects.filter(teamname__exact = me.team)
        if my_current_team:
            flash(request, 'Error', 'You have already joined a team!', 'error')
            return HttpResponseRedirect('/team/')
        else:
            flash(request, 'Error', 'Your current team does not exist, now you do not belong to any team lol.')
            me.team = ''
            me.save()
        #return HttpResponse('You have already joined a team!')
    team = get_object_or_404(TeamInfo, pk = pk)
    destin_team = team.teamname
    if request.method == 'POST':
        userform = TeamRequestForm(request.POST)
        if userform.is_valid():
            if team.members >= MAX_TEAM_MEMBER_NUMBER: 
                flash(request, 'Error', 'A team at most has {0} members'.format(MAX_TEAM_MEMBER_NUMBER))
                return HttpResponseRedirect('/team/')
            team_request = TeamRequest()
            team_request.username = username
            team_request.destin_team = userform.cleaned_data['destin_team']
            team_request.message = userform.cleaned_data['message']
            team_request.status = False
            existing_request = TeamRequest.objects.filter(username__exact = username, destin_team__exact = team_request.destin_team)
            if existing_request:
                flash(request, 'Error', 'Error! You have already sent a request to join this team!', 'error')
                return HttpResponseRedirect('/team/')
            team_request.save()
            flash(request, 'Success', 'Request has been sent! Please wait for the captain to reply.', 'success')
            return HttpResponseRedirect('/team/')
        else:
            flash(request, 'Error', 'Please complete the form!')
            return render(request, 'teamrequest.html', {'username': username, 'form': userform})
    else:
        msg = 'I am ' + username + ', ' + me.realname
        userform = TeamRequestForm(data = {'destin_team': team.teamname, 'message': msg})
    return render(request, 'teamrequest.html', {'username': username, 'form': userform, 'destin_team': team.teamname})


# Accept a request to join a team
def acceptrequest(request, pk):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = get_object_or_404(UserInfo, username = username) # Me, namely the captain
    team_request = get_object_or_404(TeamRequest, pk = pk)
    destin_team = team_request.destin_team
    team = get_object_or_404(TeamInfo, teamname = destin_team)
    apply_user = get_object_or_404(UserInfo, username = team_request.username) # The one who sent the request
    if team.captain == me.username:
        if team.members >= MAX_TEAM_MEMBER_NUMBER:
            flash(request, 'Error', 'A team at most has {0} members'.format(MAX_TEAM_MEMBER_NUMBER))
            return HttpResponseRedirect('/team/')
            #return HttpResponse('A team at most has 4 members')
        apply_user.team = destin_team
        apply_user.save()
        user_codes = FileInfo.objects.filter(username__exact = apply_user.username)
        if user_codes:
            for code in user_codes:
                code.teamname = destin_team
                code.save()
        team.members = team.members + 1
        team.save()
        team_request.delete()
        updatecodeteaminfo() #================================================
        flash(request, 'Success', 'You have successfully accepted the request')
        return HttpResponseRedirect('/team/')
        #return HttpResponse('You have successfully accepted the requet.')
    else:
        flash(request, 'Error', 'You can only accept requests to join your own team.')
        return HttpResponseRedirect('/team/')
        #return HttpResponse('You can only accept requests to join your own team.')


# Reject a request to join a team
def rejectrequest(request, pk):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = get_object_or_404(UserInfo, username = username) # Me, namely the captain
    team_request = get_object_or_404(TeamRequest, pk = pk)
    destin_team = team_request.destin_team
    team = get_object_or_404(TeamInfo, teamname = destin_team)
    if team.captain == me.username:
        team_request.delete()
        updatecodeteaminfo() #================================================
        flash(request, 'Success', 'You have successfully rejected the request', 'succes')
        return HttpResponseRedirect('/team/')
        #return HttpResponse('You have successfully rejected the request')
    else:
        flash(request, 'Error', 'You can only reject requests to join your own team.')
        return HttpResponseRedirect('/team')
        #return HttpResponse('You can only reject requests to join your own team.')


# Show the detail of a team to the captain
def teamdetail(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    #my_team = get_object_or_404(TeamInfo, captain = username)
    me = get_object_or_404(UserInfo, username = username)
    #my_team_exists = TeamInfo.objects.filter(username__exact = username)
    my_team = me.team
    if my_team:
        my_team = get_object_or_404(TeamInfo, teamname = me.team)
        if my_team.captain == username:
            is_captain = True
        else:
            is_captain = False
        members = UserInfo.objects.filter(team__exact = my_team.teamname)
        requests = TeamRequest.objects.filter(destin_team = my_team.teamname)
        return render(request, 'teamdetail.html', {'username': username, 'team': my_team, 'members': members, 'requests': requests, 'is_captain': is_captain})
    else:
        flash(request, 'Error', 'Please join a team first!', 'error')
        return HttpResponseRedirect('/team/')


# Quit the team
def quitteam(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = get_object_or_404(UserInfo, username = username)
    if me:
        my_team = me.team
        if my_team == '':
            flash(request, 'Error', 'You have not joined a team yet!', 'error')
            return HttpResponseRedirect('/team/')
        team = get_object_or_404(TeamInfo, teamname = my_team)
        if team:
            captain = team.captain
            if captain == username:
                flash(request, 'Error', 'You are the captain so you cannot simply quit the team!')
                return HttpResponseRedirect('/teamdetail/')
            else:
                me.team = ''
                me.save()
                team.members = team.members - 1
                team.save()
                updatecodeteaminfo() #================================================
                flash(request, 'Success', 'You have successfully quitted the team.')
                return HttpResponseRedirect('/team/')
        else:
            flash(request, 'Error', 'Team does not exist', 'error')
            return HttpResponseRedirect('/team/')
    else:
        flash(request, 'Error', 'User does not exist!', 'error')
        return HttpResponseRedirect('/login/')


# Dismiss the team
def dismissteam(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    me = get_object_or_404(UserInfo, username = username)
    if me:
        my_team = me.team
        if my_team == '':
            flash(request, 'Error', 'You have not joined a team yet!', 'error')
            return HttpResponseRedirect('/team/')
        team = get_object_or_404(TeamInfo, teamname = my_team)
        if team:
            captain = team.captain
            if captain != username:
                flash(request, 'Error', 'You are not the captain so you cannot dismiss the team!', 'error')
                return HttpResponseRedirect('/teamdetail/')
            else:
                members = UserInfo.objects.filter(team__exact = my_team)
                if members:
                    for member in members:
                        member.team = ''
                        member.save()
                team.delete()
                updatecodeteaminfo() #================================================
                flash(request, 'Success', 'You have successfully dismissed the team', 'success')
                return HttpResponseRedirect('/team/')
        else:
            flash(request, 'Error', 'Team does not exist!', 'error')
            return HttpResponse('/team/')
    else:
        flash(request, 'Error', 'User does not exist', 'error')
        return HttpResponseRedirect('/login/')


# Play game online
def playgame(request):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first!', 'error')
        return HttpResponseRedirect('/login/')
    file_available = FileInfo.objects.filter(is_compile_success__exact = 'Successfully compiled')
    my_record = GameRecord.objects.filter(username__exact = username)
    me = get_object_or_404(UserInfo, username = username)
    if request.method == 'POST':
        check_box_list = request.POST.getlist('check_box_list')
        if check_box_list:
            if len(check_box_list) != 4:
                flash(request, 'Error', 'Please select 4 AIs.', 'error')
                #return HttpResponseRedirect('/playgame/')
                return render(request, 'playgame.html', {'ailist': file_available, 'records': my_record, 'username': username})
            
            print('Playgame! username = {0}'.format(username)) #=======================
            print('MyTeam = {0}'.format(me.team))
            involve_mine = False
            for item in check_box_list:
                pk = item.strip()
                #AIs = FileInfo.objects.filter(pk__exact = pk)
                AI = get_object_or_404(FileInfo, pk = pk)
                print('Author of AI = {0}'.format(AI.username)) #========================
                #if AI.username == username or (AI.teamname == me.team and AI.teamname != ''):
                #if AIs:
                #    for ai in AIs:
                #        if ai.username == username or (ai.teamname == me.teamname and ai.teamname != ''):
                #            involve_mine = True
                #    involve_mine = True
                #else:
                #    pass
                # flash(request, 'Error', 'Invalid AI selected!', 'error')
                #return HttpResponseRedirect('/playgame/')
                #return render(request, 'playgame.html', {'ailist': file_available, 'records': my_record, 'username': username})
                if me.team:
                    if AI.username == username or AI.teamname == me.team:
                        involve_mine = True
                else:
                    if AI.username == username:
                        involve_mine = True

            if involve_mine == False:
                flash(request, 'Error', 'AI(s) of your team must be included.', 'error')
                #return HttpResponseRedirect('/playgame/')
                return render(request, 'playgame.html', {'ailist': file_available, 'records': my_record, 'username': username})

            # Code to process game_result is required
            record = GameRecord()
            record.username = username
            record.timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            record.state = 'Unstarted'
            now = time.strftime('%Y%m%d%H%M%S') 
            #record.filename = 'record{0}_{1}.json'.format(now, random.randint(0, 1000))
            #while os.path.exists(record.filename):
            #    now = time.strftime('%Y%m%d%H%M%S')
            #    record.filename = 'record{0}_{1}.json'.format(now, random.randint(0, 1000))
            record.filename = 'record_{0}.json'.format(random_string(25))
            while os.path.exists(record.filename):
                record.filename = 'record_{0}.json'.format(random_string(25))
            record.AI1 = check_box_list[0].strip()
            record.AI2 = check_box_list[1].strip()
            record.AI3 = check_box_list[2].strip()
            record.AI4 = check_box_list[3].strip()
            record.AI1_name = get_object_or_404(FileInfo, pk = record.AI1).filename
            record.AI2_name = get_object_or_404(FileInfo, pk = record.AI2).filename
            record.AI3_name = get_object_or_404(FileInfo, pk = record.AI3).filename
            record.AI4_name = get_object_or_404(FileInfo, pk = record.AI4).filename
            record.save()

            # Add record to queue
            run_game_queue()

            flash(request, 'Success', 'The request for a game has been submitted. Please wait. The result will be put on this page later.')
            #return HttpResponseRedirect('/playgame/')
            return render(request, 'playgame.html', {'ailist': file_available, 'records': my_record, 'username': username})
        else:
            print('fail')
            flash(request, 'Error', 'Please select 4 AIs.', 'error')
            #return HttpResponseRedirect('/playgame/')
            return render(request, 'playgame.html', {'ailist': file_available, 'records': my_record, 'username': username})
    else:
        #all_file = FileInfo.objects.all()
        #file_available = FileInfo.objects.filter(is_compile_success__exact = 'Successfully compiled')
        #my_record = GameRecord.objects.filter(username__exact = username)
        return render(request, 'playgame.html', {'ailist': file_available, 'records': my_record, 'username': username})


# Handles 404 error
def page_not_found(request):
    #return HttpResponse('Page not found lol.')
    return render(request, 'page404.html')


# Handles 500 error
def page_error(request):
    #return HttpResponse('Page error lol.')
    return render(request, 'page500.html')


# Execute specific command
# should be deleted if the website is to be deployed
def exe_code(request):
   # UserInfo.objects.create(username = username, realname = realname, password = password, email = email, stu_number = stu_number, activated = False)
    #for i in range(0, 50):
    #    UserInfo.objects.create(username = i, realname = '123', password = '123456', email = 'justatest@tsinghua.edu.cn', stu_number = '2020000000', activated = True)
    return HttpResponse('Successfully executed.')


# Download game record
def recorddownload(request, pk):
    def file_iterator(file_name, chunk_size = 2048):
        with open(file_name) as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    now = time.strftime('%Y%m%d%H%M%S') 
    download_name = 'record_{0}.json'.format(now)
    record_info = get_object_or_404(GameRecord, pk = pk)
    response = StreamingHttpResponse(file_iterator('gamerecord/' + record_info.filename))
    response['Content-Type'] = 'application/octet-stream'  
    #response['Content-Disposition'] = 'attachment;filename="{0}"'.format(record_info.filename)
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format(download_name)
    return response


# Delete a game record
def recorddelete(request, pk):
    username = request.COOKIES.get('username', '')
    if username == '':
        flash(request, 'Error', 'Please login first', 'error')
        return HttpResponseRedirect('/login/')
    record_file = get_object_or_404(GameRecord, pk = pk)
    if record_file.username != username:
        flash(request, 'Error', 'You can only delete your own record file.', 'error')
        return HttpResponseRedirect('/playgame/')
    path = 'gamerecord/{0}'.format(record_file.filename)
    if os.path.exists(path):
        os.remove(path)
    record_file.delete()
    flash(request, 'Success', 'You have successfully deleted the record.', 'success')
    return HttpResponseRedirect('/playgame/')


# Launch UI
def ui(request):
    username = request.COOKIES.get('username', '')
    return render(request, 'ui.html', {'path': '', 'username': username})


# Replay a specific game
def replay(request, pk):
    record = get_object_or_404(GameRecord, pk = pk)
    filename = record.filename
    #path = '/static/gamerecord/{0}'.format(filename)
    username = request.COOKIES.get('username', '')
    return HttpResponseRedirect('/ui/?json=/static/gamerecord/{0}'.format(filename))
    #return render(request, 'ui.html', {'path': path, 'username': username})


# Download SDK
def sdkdownload(request):
    def file_iterator(file_name, chunk_size = 2048):  
        with open(file_name, 'rb') as f:  
            while True:  
                c = f.read(chunk_size)  
                if c:
                    yield c
                else:
                    break  

    response = StreamingHttpResponse(file_iterator('static/SDK_release.zip'))  
    #response = StreamingHttpResponse(file_iterator('static/a.ppt'))  
    response['Content-Type'] = 'application/octet-stream'  
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format('User_Package_v1.0.zip')
    return response


# Download file of a specific path, and it can replace function 'sdkdownload'
def downloadfile(path, _name, request):
    def file_iterator(file_name, chunk_size = 2048):  
        with open(file_name, 'rb') as f:  
            while True:  
                c = f.read(chunk_size)  
                if c:
                    yield c
                else:
                    break  

    if os.path.exists(path):
        response = StreamingHttpResponse(file_iterator(path))  
        response['Content-Type'] = 'application/octet-stream'  
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(_name)
        return response
    else:
        flash(request, 'Error', 'File does not exist.', 'error')
        return HttpResponseRedirect('/document/')


def download_manual(request):
    return downloadfile('static/FC15参赛手册.pdf', 'FC15参赛手册.pdf', request)


def download_0318ppt(request):
    return downloadfile('static/0318说明会.pdf', '0318说明会.pdf', request)


def sendmailtest(request):
    send_mail_to_mine
    return HttpResponseRedirect('/home/')


# Update info on team of all code
def updatecodeteaminfo():
    all_user = UserInfo.objects.all()
    for user in all_user:
        team = user.team
        if team:
            codes = FileInfo.objects.filter(username__exact = user.username)
            for code in codes:
                code.teamname = team
                code.save()


# Send activation email again
def activateagain(request):
    username = request.COOKIES.get('username', '')
    if username:
        flash(request, 'Error', 'You have already signed in.', 'error')
        return HttpResponseRedirect('/index/')
    tmp_username = request.COOKIES.get('tmp_username', '')
    if tmp_username:
        # Delete old activating infomation
        old_activate = EmailActivate.objects.filter(username__exact = tmp_username)
        for info in old_activate:
            info.delete()
        # Create new information
        userinfo = get_object_or_404(UserInfo, username = tmp_username)
        if userinfo.activated:
            flash(request, 'Error', 'The account has already been activated.', 'error')
            return HttpResponseRedirect('/login/')
        print('activate again, username = {0}'.format(userinfo.username))
        mail_activate(userinfo.email, userinfo.username)
        flash(request, 'Success', 'The email has been sent and the old one has become invalid. Please use the latest link to activate your account')
        return HttpResponseRedirect('/login/')
    else:
        print('tmp_username == None')
        return HttpResponseRedirect('/login/')


# View for new page
def newpage(request):
    return render(request, 'newpage.html')