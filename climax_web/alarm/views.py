from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from random import randrange
from django.http import JsonResponse
from django.views.generic.edit import UpdateView
from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.template import RequestContext

from django.contrib.auth.models import User
from .models import gateways, users, sensors, events
#from .forms import gatewaysForm, userForm, sensorModifyForm, sensorModifyForm_1, sensorModifyForm2
from .forms import *

from .Dj_GW_cmd import cmdTo_climax, Glob
from .event_translate import translate 

class SensorIcon:
    icon_list= ["icon_keyfob.png",
                "icon_doorsensor.png",
                "Pendant___",
                "icon_movementsensor.png",
                "icon_smoke.png",
                "Gas",
                "Tx",
                "icon_keypad.png",
                "glass",
                "wrist",
                "wrist",
                "icon_watersensor.png",
                "12",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "20",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "icon_smartplug.png",
                "",
                "",]
    
    
# Create your views here.
@login_required(login_url="/login/")
def index( request):

#   usr = User.objects.get(username="marc")
    
    if request.user.is_authenticated():
        usr = request.user
    
    try:
        gw=gateways.objects.get(userWEB=usr.id)
        Glob.current_GW=gw
        
    except: 
        return redirect('gateway_new')     
    
    else: 
        # refresh DB content if required
        #should be 10 users, otherwise --> refresh
        
        cmd=cmdTo_climax()
        if users.objects.filter(gwID=gw.id).count() != 10 :
            cmd.getUsers()
            
        cmd.getSensors()
        
        
        # return the value for GW and adapt it to the buttons
        if gw.mode == "3":
            sts="0"
        elif gw.mode == "2":
            sts="1"
        else :
            sts="2"      
    
        evts = events.objects.filter(gwID = Glob.current_GW.id ).order_by('id').reverse()[:5]  
        
        for evt in evts :
            evt.translation=translate( evt.event )
        
        return render( request, 'home.html',{'status': sts,'events':evts })


@login_required(login_url="/")
def users_list( request):
    usr = users.objects.filter(gwID = Glob.current_GW.id )
    return render( request, 'alarm/userslist.html', {'users':usr})

@login_required(login_url="/")
def user_edit( request, pk ):
    post = get_object_or_404(users, pk=pk)
    if request.method == 'POST':
        usr_form = userForm(request.POST, instance=post)
        if usr_form.is_valid():
            post = usr_form.save(commit=False)
       
            cmd=cmdTo_climax()
            cmd.setUsers( post.index_usr, post.code, post.name, post.latch )
            post.save()
            return redirect('users_list')
    else:
        usr_form = userForm( instance = post )
    return render( request, 'alarm/useredit.html', {'form': usr_form})

@login_required(login_url="/")
def gateways_list( request ):       
    
    gws_list = gateways.objects.filter(userWEB = request.user.id )
    if gws_list == []:
        gateway_new( request)
    else:
        return render( request, 'alarm/gatewayslist.html', {'gateways':gws_list})

@login_required(login_url="/")
def gateways_delete( request, pk):
    gw = gateways.objects.get(pk=pk)

    # delete gateway in DB
    gw.delete()
    return redirect('gateways_list')

@login_required(login_url="/")
def gateway_new( request):
    if request.method == 'POST':
        gw_form = gatewaysForm(request.POST)
        if gw_form.is_valid():
            gateways = gw_form.save(commit=False)
            
            if request.user.is_authenticated():
                usr = request.user
                gateways.userWEB = usr
                gateways.userID = usr.id
                
#            usr = User.objects.get(username="marc")
#            gateways.userWEB = usr
#            gateways.userID = "Marc"

            gateways.ver = "123"
            gateways.sensor_mod = "A"
            gateways.rptipid = ""
            gateways.acct2 = ""
            gateways.cmd_pending = ""
            gateways.last_cmd_id = 0
            gateways.mode = ""
            gateways.sensorsNbr = ""
            gateways.registrationDatec = timezone.now()
            gateways.lastSeenTimestamp = timezone.now()
            
            gateways.save()
            return redirect('index')
#            return redirect('index', pk=gateways.pk)
    else:
        gw_form = gatewaysForm()
        
    return render(request, 'alarm/gatewayedit.html', {'form': gw_form})

@login_required(login_url="/")
def gateway_status( request):
#    return HttpResponse("Gw Status")
#    return render( request, 'alarm/test3.html')
#    cmd = cmdTo_climax(db, "00:1D:94:03:0F:16", "usr1", "1","0730")   

    cmd=cmdTo_climax()
    btn = request.GET.get('btnActive', None)  

    print("Btn= {}".format(btn))
       
    # adapt the button value to the DB values 
    if btn == "2":
        mode="1"
    elif btn == "1":
        mode="2"
    else :
        mode="3"
    
    cmd.setMode(mode)
    
    data = {
        'attribute' : 'gw_mode= ' + mode
    }
    return JsonResponse(data)

@login_required(login_url="/")
def sensors_list( request):
    snrs_list = sensors.objects.filter(gwID = Glob.current_GW.id )
   
    # add icon to sensor list
    for sensor in snrs_list:        
        sensor.ico = SensorIcon.icon_list[int(sensor.type)]
#        print("sensor type={}".format (int(sensor.type)) )
    
    return render( request, 'alarm/sensorslist.html', {'sensors':snrs_list})

@login_required(login_url="/")
def sensor_delete( request, pk):

    snrs = sensors.objects.get(pk=pk)
    
    # delete sensor on GW
    cmd=cmdTo_climax()
    cmd.delSensors( snrs.no )
    
    # delete sensor in DB
    snrs.delete()
 
    return redirect('sensors_list')
    
@login_required(login_url="/")    
def sensor_modify( request, pk ):
    post = get_object_or_404(sensors, pk=pk)
    if request.method == 'POST':
        
        if post.type == '0':
            usr_form = sensorModifyForm_0( request.POST, instance = post )
        elif post.type == '1':
            usr_form = sensorModifyForm_1( request.POST, instance = post )
        elif post.type == '3':
            usr_form = sensorModifyForm_3( request.POST, instance = post )           
        else:
            usr_form = sensorModifyForm_other( request.POST, instance = post )
        
        if usr_form.is_valid():
            post = usr_form.save(commit=False)
            #gateways.userID = "Marc"          
            cmd=cmdTo_climax()
            
            cmd.editSensors(post.no, post.name[0:10], post.attr, post.latch )
            post.save()
            return redirect('sensors_list')
    else:
        if post.type == '0':
            usr_form = sensorModifyForm_0( instance = post )
        elif post.type == '1':
            usr_form = sensorModifyForm_1( instance = post )
        elif post.type == '3':
            usr_form = sensorModifyForm_3( instance = post )           
        else:
            usr_form = sensorModifyForm_other( instance = post )
            
    return render( request, 'alarm/sensormodify.html', {'form': usr_form})
    

@login_required(login_url="/")
def smartplug_list( request):
    
    smartplug_list = sensors.objects.filter(gwID = Glob.current_GW.id).filter(type="29")
   
    # add icon to sensor list
    # for splug in smartplug_list:        
    #   print("sensor type={}, power={}".format (int(splug.type),splug.status_switch) )
    
    return render( request, 'alarm/smartpluglist.html', {'status': 1 , 'smartplug_list':smartplug_list})


@login_required(login_url="/")
def smartplug_cmd( request):
    
    btn = request.GET.get('btnActive', None) 
    btn = btn[0:5]      # for security
    print("Btn= {}".format(btn))
    btn = btn[0:4]
   
    cmd=cmdTo_climax()
    
    zone = btn.split('_')[0]
    switch= btn[-2:]
    if switch == 'ON':
        switch="1"
    else:
        switch="0"  

    cmd.setSmartPlug( zone, switch )

    # update the switch value in DB (Gateway answer can take up to 20 sec)
    smartplug = sensors.objects.filter(gwID = Glob.current_GW.id, no=zone).update(status_switch = switch)
    
    
    data = {
        'attribute' : 'smrt_plug = ' + btn
    }
    return JsonResponse(data)
 
