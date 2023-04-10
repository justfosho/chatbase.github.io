from django.shortcuts import render, redirect
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse


# Create your views here.


#rooms=[
    #{'id': 1, 'name': 'Gamers'},
    #{'id': 2, 'name': 'Gymrats'},
    #{'id': 3, 'name': 'Football Debates'},    
    #{'id': 4, 'name': 'Meme connoissseurs'},
#]


def loginPage(request):#We call it login page coz there's a function in django called login
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist') #Checks if user exists
                                                        #if user doesn't exist display error message
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')#If user exists redirect them to home

        else:
            messages.error(request, 'Username or password does not exist')
            
    context = {'page':page}
    return render(request, 'base/login_register.html',context)


def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)#User can be accesed immediately after creating a valid form
                                            #More data can be saved within the form
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'base/login_register.html',{'form': form}) 

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else '' #In-line if statement

    rooms = Room.objects.filter(
        Q(topic__name__contains = q) |
        Q(name__contains=q) |
        Q(description__contains=q) 
    ) #Filters any letter,name or description in the search bar to bring a result

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q)) 

    context = {'rooms':rooms, 'topics':topics, 'room_count':room_count, 'room_messages':room_messages}
    return render(request, 'base/home.html', context)

def room(request, pk):
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()
     #Gives set of messages related to a room 
    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,  
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id) 
        #After inputting a message, the site reloads and redirects the user back to the room

    context = {'room':room, 'room_messages':room_messages,'participants':participants}
    return render(request, 'base/room.html', context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    rooms = user.room_set.all()
    context = {'user':user,'rooms':rooms, 'topics':topics, 'room_messages':room_messages}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login')#Prompts a person to create an account before creating a room
def createRoom(request):
    form = RoomForm()
    topics = Topic.objects.all()
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name =topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('home')

    context = {'form':form, 'topics':topics}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')#Prompts a person to create an account before updating a room
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    if request.user != room.host:
        return HttpResponse("You can't update someone else's room")
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name =topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home') 
    
    context = {'form':form, 'topics':topics, 'room':room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')#Prompts a person to create an account before deleting a room
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)
    if request.method == 'POST':
        room.delete()
        return redirect('home')

    if request.user != room.host:
        return HttpResponse("You can't delete someone else's room")

    return render(request, 'base/delete.html', {'obj':room})

@login_required(login_url='login') 
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)
    if request.method == 'POST':
        message.delete()
        return redirect('home')

    if request.user != message.user:
        return HttpResponse("You can't delete someone else's message")

    return render(request, 'base/delete.html', {'obj':message})

@login_required(login_url='login')
def updateUser(request):
     user = request.user
     form = UserForm(instance = user)

     if request.method == 'POST':
         form  = UserForm(request.POST, request.FILES, instance=user)
         if form.is_valid:
             form.save()
             return redirect('user-profile', pk=user.id)

     return render(request, 'base/update-user.html', {'form':form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)
    return render(request, 'base/topics.html', {'topics':topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render(request, 'base/activity.html', {'room_messages':room_messages})
