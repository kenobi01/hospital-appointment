from django.shortcuts import render,redirect,reverse
from django.conf import settings
from . import forms,models
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User,Group
from .forms import DoctorRegisterForm,DoctorUpdateForm, AdminRegisterForm,AdminUpdateForm, PatientRegisterForm,PatientUpdateForm,PatientAppointmentForm,AdminAppointmentForm,YourHealthEditForm,AppointmentEditForm,AdmitRegisterForm,AdminAdmitRegisterForm,AddMedForm,OpcostsForm,CovidVaccinationApplicationForm
from django.contrib.auth.forms import AuthenticationForm
from hospital.models import Doctor,Admin,Patient,Appointment,User,PatHealth,PatAdmit,Charges,DoctorProfessional,Medicines,OperationCosts,ChargesApt,CovidVaccination
from django.contrib import auth
from django.utils import timezone
from datetime import date,timedelta,time
from django.http import HttpResponseRedirect

## For Invoice Function
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

#Admin Related Views
@login_required(login_url='login_adm.html')     # if user is not logged in, redirect to login page
def opcost_adm_view(request):
    if check_admin(request.user):
        if request.method == "POST" and 'addmeds' in request.POST:    # form for adding medicines
            f = AddMedForm(request.POST)
            if f.is_valid():
                name = f.cleaned_data.get('name')   # get name from form
                price = f.cleaned_data.get('price') # get price from form
                med = Medicines(name=name, price=price)  # create new medicine
                med.save()
                return redirect('opcost.html')
            else:
                print(f.errors)
        else:
            f = AddMedForm()

        if request.method == "POST" and 'opcost' in request.POST:    # form for editing operational costs
            opf = OpcostsForm(request.POST)
            if opf.is_valid():
                main = opf.cleaned_data.get('maintenance')  # get maintenance charges from form
                hosp = opf.cleaned_data.get('hospfee')     # get hospital fees from form
                rf = opf.cleaned_data.get('roomfee')        # get room fee from form
                
                # edit, then save records
                mnc = OperationCosts.objects.all().filter(name="Maintenance").first()
                mnc.cost = main
                mnc.save()

                hp = OperationCosts.objects.all().filter(name="Hospital Fee").first()
                hp.cost = hosp
                hp.save()

                r = OperationCosts.objects.all().filter(name="Room").first()
                r.cost = rf
                r.save()

                return redirect('opcost.html')
            else:
                print(opf.errors)
        else:
            f = AddMedForm()
            opf = OpcostsForm()
            mnc = OperationCosts.objects.all().filter(name="Maintenance").first()
            hp = OperationCosts.objects.all().filter(name="Hospital Fee").first()
            r = OperationCosts.objects.all().filter(name="Room").first()

            # setting initial placeholders for operational costs form
            opf.fields['maintenance'].initial = mnc.cost  
            opf.fields['hospfee'].initial = hp.cost
            opf.fields['roomfee'].initial = r.cost

        meds = Medicines.objects.all()
        return render(request, 'hospital/Admin/opcost.html', {'medform': f, 'opf': opf, 'meds': meds, 'mnc': mnc, 'hp': hp, 'r': r})
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def admit_adm_view(request):
    if check_admin(request.user):
        if request.method == "POST":
            admitForm = AdminAdmitRegisterForm(request.POST)
            if admitForm.is_valid():
                docid = admitForm.cleaned_data.get('doctor')  # Get doctor id
                patid = admitForm.cleaned_data.get('patient')  # Get patient id
                doc = Doctor.objects.all().filter(id=docid).first()  # Get doctor
                pat = Patient.objects.all().filter(id=patid).first()  # Get patient
                adt = PatAdmit(patient=pat, doctor=doc,  # Create new admit record
                               description=admitForm.cleaned_data.get('description'),
                               admitDate=admitForm.cleaned_data.get('admitDate'))
                adt.save()
                return redirect('admit_adm.html')
            else:
                print(admitForm.errors)
        admitForm = AdminAdmitRegisterForm()
        return render(request, 'hospital/Admin/admit_adm.html', {'admitForm': admitForm})
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def admin_appointment_view(request):
    if check_admin(request.user):
        det = []
        for c in Appointment.objects.filter(status=True).all():  # Get approved appointments
            d = c.doctor  # Get doctor
            p = c.patient  # Get patient
            if d and p:
                det.append([d.firstname, p.firstname, c.description, c.calldate, c.calltime, c.pk])  # Add information to the list
        return render(request, 'hospital/Admin/appoint_view_adm.html', {'app': det})  # Render the appointment information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def admin_admit_view(request):
    if check_admin(request.user):
        det = []
        for c in PatAdmit.objects.all():  # Get all admit records
            d = c.doctor  # Get doctor
            p = c.patient  # Get patient
            if d and p:
                det.append([d.firstname, p.firstname, c.description, c.admitDate, c.pk])  # Add information to the list
        return render(request, 'hospital/Admin/admit_view_adm.html', {'app': det})  # Render the admit information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def dash_adm_view(request):
    if check_admin(request.user):
        doc = Doctor.objects.all().filter(status=False)  # Get all on-hold doctors
        pat = Patient.objects.all().filter(status=False)  # Get all on-hold patients
        pattotcount = Patient.objects.all().count()  # Get total patients
        doctotcount = Doctor.objects.all().count()  # Get total doctors
        appcount = Appointment.objects.all().count()  # Get total appointments
        patapp = Patient.objects.all().filter(status=False).count()  # Get total on-hold patients
        docapp = Doctor.objects.all().filter(status=False).count()  # Get total on-hold doctors
        approveapp = Appointment.objects.all().filter(status=False).count()  # Get total on-hold appointments
        dic = {'doc': doc, 'pat': pat, 'pattotcount': pattotcount, 'doctotcount': doctotcount,
               'patapp': patapp, 'docapp': docapp, 'appcount': appcount, 'approveapp': approveapp}  # Create a dictionary with information
        return render(request, 'hospital/Admin/dashboard_adm.html', context=dic)  # Render the dashboard with the information
    else:
        auth.logout(request)
        return redirect('login_adm.html')

def calladoc_adm_view(request):
    return render(request, 'hospital/Admin/calladoc_adm.html')

def medicalreport_adm_view(request):
    return render(request, 'hospital/Admin/medicalreport_adm.html')

def yourhealth_adm_view(request):
    return render(request, 'hospital/Admin/yourhealth_adm.html')


def login_adm_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')  # Get username
            password = form.cleaned_data.get('password')  # Get password
            user = auth.authenticate(username=username, password=password)  # Authenticate user
            if user is not None and check_admin(user):  # If user exists and is admin
                auth.login(request, user)  # Log in user
                accountapproval = Admin.objects.all().filter(status=True, user_id=request.user.id)  # Check if account is approved
                if accountapproval:
                    return redirect('profile_adm.html')
                else:  # If account is not yet approved
                    auth.logout(request)
                    return render(request, 'hospital/Home/wait_approval.html')
                return redirect('dashboard_adm.html')
        return render(request, 'hospital/Admin/login_adm.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'hospital/Admin/login_adm.html', {'form': form})

def register_adm_view(request):
    if request.method == "POST":
        form = AdminRegisterForm(request.POST, request.FILES)
        if form.is_valid():  # Get data from form (if it is valid)
            db = form.cleaned_data.get('dob')  # Get date of birth from form
            today = date.today()
            ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))  # Calculate age from dob
            if db < timezone.now().date():  # Check if date of birth is valid (happened the previous day or even back)
                nu = User.objects.create_user(username=form.cleaned_data.get('username'),
                                              email=form.cleaned_data.get('email'),
                                              password=form.cleaned_data.get('password1'))  # Create user
                adm = Admin(user=nu, firstname=form.cleaned_data.get('firstname'),
                            lastname=form.cleaned_data.get('lastname'),
                            age=ag,
                            dob=form.cleaned_data.get('dob'),
                            address=form.cleaned_data.get('address'),
                            city=form.cleaned_data.get('city'),
                            country=form.cleaned_data.get('country'),
                            postalcode=form.cleaned_data.get('postalcode'),
                            image=request.FILES['image']
                            )  # Create admin
                adm.save()
                mpg = Group.objects.get_or_create(name='ADMIN')  # Add user to admin group
                mpg[0].user_set.add(nu)
                return redirect('login_adm.html')
            else:
                form.add_error('dob', 'Invalid date of birth.')
        else:
            print(form.errors)
            return render(request, 'hospital/Admin/register_adm.html', {'form': form})
    else:
        form = AdminRegisterForm()

    return render(request, 'hospital/Admin/register_adm.html', {'form': form})


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def patient_adm_view(request):
    if check_admin(request.user):
        pat = Patient.objects.all().filter(status=False)  # Get all patients with status=False (on-hold patients)
        patapp = Patient.objects.all().filter(status=False).count()  # Get count of on-hold patients
        patcount = Patient.objects.all().count()  # Get total count of patients
        dic = {'pat': pat, 'patcount': patcount, 'patapp': patapp}  # Create a dictionary with information
        return render(request, 'hospital/Admin/patient_adm.html', context=dic)  # Render the patient view with the information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def patient_all_view(request):
    if check_admin(request.user):
        det = []
        for c in Patient.objects.filter(status=True).all():  # Get all patients with status=True (approved patients)
            # Append patient details to the det list
            det.append([c.firstname, c.lastname, c.dob, c.address, c.city, c.country, c.postalcode, c.image.url])
        return render(request, 'hospital/Admin/patient_all_adm.html', {'app': det})  # Render the patient view with the information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def doctor_adm_view(request):
    if check_admin(request.user):
        # Get information from the database and render it in the HTML webpage
        doc = Doctor.objects.all().filter(status=False)  # Get all doctors with status=False (on-hold doctors)
        doccount = Doctor.objects.all().count()  # Get the total count of doctors
        dic = {'doc': doc, 'doccount': doccount}  # Create a dictionary with the doctor information
        return render(request, 'hospital/Admin/doctor_adm.html', context=dic)  # Render the doctor view with the information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def doctor_all_view(request):
    # Get information from the database and render it in the HTML webpage
    if check_admin(request.user):
        det = []
        for c in Doctor.objects.filter(status=True).all():
            # Get additional information from the DoctorProfessional model related to the doctor
            k = DoctorProfessional.objects.filter(doctor=c).first()
            det.append([c.firstname, c.lastname, c.dob, c.address, c.city, c.country, c.postalcode, c.department,
                        k.appfees, k.admfees, k.totalpat])  # Append the doctor information to the list
        return render(request, 'hospital/Admin/doctor_all_adm.html', {'app': det})  # Render the doctor view with the information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def admin_adm_view(request):
    # Get information from the database and render it in the HTML webpage
    if check_admin(request.user):
        adm = Admin.objects.all().filter()  # Get all admin records
        admcount = Admin.objects.all().count()  # Count the number of admin records
        dic = {'adm': adm, 'admcount': admcount}  # Create a dictionary with admin information
        return render(request, 'hospital/Admin/admin_adm.html', context=dic)  # Render the admin view with the information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def admin_all_view(request):
    if check_admin(request.user):
        # Get information from the database and render it in the HTML webpage
        det = []
        for c in Admin.objects.all():
            det.append([c.firstname, c.lastname, c.dob, c.address, c.city, c.country, c.postalcode, c.image.url])
            # Append admin information to the 'det' list

        return render(request, 'hospital/Admin/admin_all_adm.html', {'app': det})
        # Render the admin_all_adm.html template with the admin information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def admit_particular_adm_view(request, pk):
    if check_admin(request.user):
        # Get information from the database and render it in the HTML webpage
        ad = PatAdmit.objects.filter(id=pk).first()
        # Get the PatAdmit object with the given primary key (pk)

        doc = ad.doctor
        # Get the doctor associated with the admission

        doci = doc.department
        # Get the department of the doctor

        pat = ad.patient
        # Get the patient associated with the admission

        det = [ad.pk, doc.firstname, pat.firstname, ad.admitDate, ad.dischargeDate, ad.description, pk]
        # Create a list with the admission details

        med = Medicines.objects.all()
        # Get all the medicines

        return render(request, 'hospital/Admin/admit_particular_adm.html', {'app': det, 'doci': doci, 'med': med})
        # Render the admit_particular_adm.html template with the admission details, department, and medicines
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_pat_view(request):
    # Get information from the database and render it in the HTML webpage
    if check_admin(request.user):
        pat = Patient.objects.all().filter(status=False)
        # Get all the patients with status=False (not approved)

        return render(request, 'hospital/Admin/approve_pat.html', {'pat': pat})
        # Render the approve_pat.html template with the patient information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_doc_view(request):
    if check_admin(request.user):
        # Get information from the database and render it in the HTML webpage
        doc = Doctor.objects.all().filter(status=False)
        # Get all the doctors with status=False (not approved)

        return render(request, 'hospital/Admin/approve_doc.html', {'doc': doc})
        # Render the approve_doc.html template with the doctor information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_adm_view(request):
    if check_admin(request.user):
        # Get information from the database and render it in the HTML webpage
        adm = Admin.objects.all().filter(status=False)
        # Get all the admin users with status=False (not approved)

        return render(request, 'hospital/Admin/approve_adm.html', {'adm': adm})
        # Render the approve_adm.html template with the admin user information
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_patient_view(request, pk):
    if check_admin(request.user):
        # Get information from the database
        patient = Patient.objects.get(id=pk)
        # Retrieve the patient with the specified ID

        patient.status = True
        # Approve the patient by setting the status to True
        patient.save()
        # Save the changes to the patient object

        return redirect(reverse('approve_pat.html'))
        # Redirect to the approve_pat.html page using the 'reverse' function
        # The 'approve_pat.html' is likely the template to display the approved patients
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_doctor_view(request, pk):
    if check_admin(request.user):
        # Get information from the database
        doctor = Doctor.objects.get(id=pk)
        # Retrieve the doctor with the specified ID

        doctor.status = True
        # Approve the doctor by setting the status to True
        doctor.save()
        # Save the changes to the doctor object

        return redirect(reverse('approve_doc.html'))
        # Redirect to the approve_doc.html page using the 'reverse' function
        # The 'approve_doc.html' is likely the template to display the approved doctors
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_admin_view(request, pk):
    if check_admin(request.user):
        # Get information from the database
        admin = Admin.objects.get(id=pk)
        # Retrieve the admin with the specified ID

        admin.status = True
        # Approve the admin by setting the status to True
        admin.save()
        # Save the changes to the admin object

        return redirect(reverse('approve_adm.html'))
        # Redirect to the approve_adm.html page using the 'reverse' function
        # The 'approve_adm.html' is likely the template to display the approved admins
    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_appoint_view(request):
    if check_admin(request.user):
        # Get the appointments that need approval
        det = []
        for c in Appointment.objects.filter(status=False).all():
            d = c.doctor
            p = c.patient
            if d and p:
                det.append([d.firstname, p.firstname, c.description, c.calldate, c.calltime, c.id])
                # Append the relevant information to the 'det' list
                # This information will be rendered on the webpage

        return render(request, 'hospital/Admin/approve_appoint.html', {'app': det})
        # Render the 'approve_appoint.html' template and pass the 'det' list as context

    else:
        auth.logout(request)
        return redirect('login_adm.html')


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def approve_app_view(request, pk):
    if check_admin(request.user):
        # Get the appointment information from the database
        appointment = Appointment.objects.get(id=pk)
        appointment.status = True  # Approve the appointment
        appointment.save()
        return redirect(reverse('approve_appoint.html'))
        # Redirect to the 'approve_appoint.html' page after approval

    else:
        auth.logout(request)
        return redirect('login_adm.html')
        # If the user is not an admin or not logged in, redirect to the login page


@login_required(login_url='login_adm.html')  # If user is not logged in, redirect to login page
def profile_adm_view(request):
    if check_admin(request.user):
        # Get the admin information from the database
        adm = Admin.objects.filter(user_id=request.user.id).first()
        db = adm.dob
        today = date.today()
        ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))
        
        if request.method == "POST":  # Profile is being updated
            p_form = AdminUpdateForm(request.POST, request.FILES, instance=adm)
            if p_form.is_valid():
                p_form.save()  # Save changes in the profile
                return redirect('profile_adm.html')
        else:
            p_form = AdminUpdateForm(instance=adm)
        
        context = {
            'p_form': p_form,
            'adm': adm,
            'ag': ag
        }
        return render(request, 'hospital/Admin/profile_adm.html', context)
    
    else:
        auth.logout(request)
        return redirect('login_adm.html')


def check_avail(doc, dt, tm):
    # Check if the doctor is available in a given time slot
    
    tm = tm[:-3]  # Separate AM/PM
    hr = tm[:-3]  # Get hour reading
    mn = tm[-2:]  # Get minute reading
    ftm = time(int(hr), int(mn), 0)  # Create a time object
    
    # Get all appointments for the given doctor and date
    k = Appointment.objects.all().filter(status=True, doctor=doc, calldate=dt)
    
    # If time is not between 9AM to 5PM, reject
    if ftm < time(9, 0, 0) or ftm > time(17, 0, 0):
        return False
    
    # If time is between 1PM to 2PM, reject
    if ftm > time(13, 0, 0) and ftm < time(14, 0, 0):
        return False
    
    for l in k:
        if ftm == l.calltime and dt == l.calldate:
            # If another appointment already exists for the same slot, reject
            return False
    
    return True


@login_required(login_url='login_pat.html')
def bookapp_view(request):
    if check_patient(request.user):
        pat = Patient.objects.get(user_id=request.user.id)  # Get the patient from the logged in user
        
        # Get information from the database and render it in the HTML webpage
        app_det = []
        for a in Appointment.objects.filter(patient=pat, status=False).all():
            k = a.doctor
            if k:
                app_det.append([k.firstname, a.description, k.department, a.calldate, a.calltime, a.status])
        
        if request.method == "POST":  # If patient books an appointment
            appointmentForm = PatientAppointmentForm(request.POST)
            
            if appointmentForm.is_valid():  # If the form is valid
                docid = int(appointmentForm.cleaned_data.get('doctor'))  # Get doctor id from the form
                doc = Doctor.objects.all().filter(id=docid).first()  # Get doctor from the form
                
                if check_avail(doc, appointmentForm.cleaned_data.get('calldate'), appointmentForm.cleaned_data.get('calltime')):  # Check if doctor is available during that slot
                    dt = appointmentForm.cleaned_data.get('calldate')  # Get the call date
                    
                    if timezone.now().date() < dt:  # Check if the call date is valid
                        app = Appointment(patient=pat, doctor=doc,
                                          description=appointmentForm.cleaned_data.get('description'),
                                          calldate=appointmentForm.cleaned_data.get('calldate'),
                                          calltime=appointmentForm.cleaned_data.get('calltime'),
                                          status=False)  # Create an appointment instance, which is unapproved
                        app.save()
                        return redirect('bookapp.html')
                    else:
                        appointmentForm.add_error('calldate', 'Invalid date.')
                else:  # If the doctor is busy
                    appointmentForm.add_error('calltime', 'Slot Unavailable.')
                
                return render(request, 'hospital/Patient/bookapp.html', {'appointmentForm': appointmentForm, 'p1': app_det})
            
            else:  # If the form is invalid
                print(appointmentForm.errors)
        
        else:
            appointmentForm = PatientAppointmentForm()
        
        return render(request, 'hospital/Patient/bookapp.html', {'appointmentForm': appointmentForm, 'p1': app_det})
    
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def covidvaccine_pat_view(request):
    if check_patient(request.user):
        pat = Patient.objects.get(user_id=request.user.id)  # Get the patient from the logged in user
        
        # Get information from the database and render it in the HTML webpage
        covaxin = Medicines.objects.all().filter(name="covaxin").first()
        covishield = Medicines.objects.all().filter(name="covishield").first()
        tot = CovidVaccination.objects.all().count()
        t1 = Charges.objects.filter(commodity__name="covaxin").all().count()
        t2 = ChargesApt.objects.filter(commodity__name="covaxin").all().count()
        t3 = Charges.objects.filter(commodity__name="covishield").all().count()
        t4 = ChargesApt.objects.filter(commodity__name="covishield").all().count()
        det = [covaxin.name, covaxin.price, covishield.name, covishield.price, tot, t1 + t2, t3 + t4]
        
        if request.method == "POST":  # If patient applies for COVID vaccination
            vacForm = CovidVaccinationApplicationForm(request.POST)
            
            if vacForm.is_valid():  # If the form is valid
                vacid = vacForm.cleaned_data.get('commodity')
                med = Medicines.objects.all().filter(id=vacid).first()
                cv = CovidVaccination(patient=pat, vaccine=med)
                cv.save()
            
            else:  # If the form is invalid
                print(vacForm.errors)
        
        else:
            vacForm = CovidVaccinationApplicationForm()
        
        return render(request, 'hospital/Patient/bookvaccine.html', {'form': vacForm, 'app': det})
    
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def appointment_details_particular_pat_view(request, pk):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        ad = Appointment.objects.filter(id=pk).first()
        pat = ad.patient
        doc = ad.doctor
        det = [doc.firstname, pat.firstname, ad.calldate, ad.link, ad.calltime, ad.description, ad.pk]
        med = Medicines.objects.all()
        
        return render(request, 'hospital/Patient/bookapp_details_particular_pat.html', {'app': det, 'med': med})
    
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def pat_appointment_view(request):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        pat = Patient.objects.get(user_id=request.user.id)
        det = []
        for c in Appointment.objects.filter(status=True, patient=pat).all():
            # Iterate through all approved appointments for the patient
            d = c.doctor
            p = c.patient
            if d and p:
                # Append appointment details to the 'det' list
                det.append([d.firstname, p.firstname, c.description, c.link, c.calldate, c.calltime, c.pk])
        
        return render(request, 'hospital/Patient/appoint_view_pat.html', {'app': det})
    
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def calladoc_view(request):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        pat = Patient.objects.get(user_id=request.user.id)
        det = []
        for c in Appointment.objects.filter(status=True, patient=pat).all():
            # Iterate through all approved appointments for the patient
            d = c.doctor
            if d:
                # Append appointment details to the 'det' list
                det.append([d.firstname, pat.firstname, c.calldate, c.calltime, c.link])
        
        l = []
        for c in DoctorProfessional.objects.all():
            # Iterate through all DoctorProfessional instances
            d = c.doctor
            db = d.dob
            today = date.today()
            ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))
            if d.status:
                # Append doctor details to the 'l' list
                l.append([d.firstname, d.lastname, d.department, d.city, ag, c.appfees, c.admfees, c.totalpat])
        
        return render(request, 'hospital/Patient/calladoc.html', {'app': det, 'docs': l})
    
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def feedback_view(request):
    if check_patient(request.user):
        sub = forms.ContactusForm()
        if request.method == 'POST':
            # If the request method is POST
            sub = forms.ContactusForm(request.POST)
            if sub.is_valid():
                # If the form is valid
                email = sub.cleaned_data['Email']
                # Get email from the form
                name = sub.cleaned_data['Name']
                # Get name from the form
                message = sub.cleaned_data['Message']
                # Get message from the form
                try:
                    # Try sending the mail
                    send_mail(str(name) + ' || ' + str(email), message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently=False)
                    return redirect('feedback.html')
                except:
                    # If sending mail fails
                    sub.add_error('Email', 'Please turn on access to less secured apps from your Gmail account.')
                    return render(request, 'hospital/Patient/feedback.html', {'form': sub})
        return render(request, 'hospital/Patient/feedback.html', {'form': sub})
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def medicalreport_view(request):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        pat = Patient.objects.get(user_id=request.user.id)
        padm = PatAdmit.objects.all().filter(patient=pat).order_by('admitDate')
        det = []
        for p in padm:
            det.append([p.admitDate, p.pk])
        papt = Appointment.objects.all().filter(patient=pat, status=True).order_by('calldate')
        d = []
        for p in papt:
            d.append([p.calldate, p.pk])
        return render(request, 'hospital/Patient/medicalreport.html', {'padm': det, 'papt': d})
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def admit_details_view(request):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        pat = Patient.objects.get(user_id=request.user.id)
        app_det = []
        for a in Appointment.objects.filter(patient=pat, status=False).all():
            k = a.doctor
            if k:
                app_det.append([k.firstname, a.description, k.department, a.calldate, a.calltime, a.status])
        det = []
        for c in PatAdmit.objects.filter(patient=pat).all():
            d = c.doctor
            if d:
                det.append([d.firstname, pat.firstname, c.admitDate, c.dischargeDate, c.pk])
        return render(request, 'hospital/Patient/admit_details.html', {'app': det})
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def admit_details_particular_view(request, pk):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        ad = PatAdmit.objects.filter(id=pk).first()
        pat = ad.patient
        doc = ad.doctor
        det = [doc.firstname, pat.firstname, ad.admitDate, ad.dischargeDate, ad.description, pk]
        return render(request, 'hospital/Patient/admit_details_particular.html', {'app': det})
    else:
        auth.logout(request)
        return redirect('login_pat.html')

def login_pat_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():  # If form is valid
            username = form.cleaned_data.get('username')  # Get username from form
            password = form.cleaned_data.get('password')  # Get password from form
            user = auth.authenticate(username=username, password=password)  # Get user
            if user is not None and check_patient(user):  # If user exists and is a patient
                auth.login(request, user)  # Login
                account_approval = Patient.objects.all().filter(status=True, user_id=request.user.id)
                if account_approval:  # If account is approved
                    return redirect('profile_pat.html')
                else:  # If not approved, redirect to wait_approval webpage
                    return render(request, 'hospital/Home/wait_approval.html')
        return render(request, 'hospital/Patient/login_pat.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'hospital/Patient/login_pat.html', {'form': form})

def register_pat_view(request):
    if request.method == "POST":
        form = PatientRegisterForm(request.POST, request.FILES)
        if form.is_valid():  # If form is valid
            db = form.cleaned_data.get('dob')  # Get date of birth from form
            if db < timezone.now().date():  # Check if date is valid
                nu = User.objects.create_user(username=form.cleaned_data.get('username'), email=form.cleaned_data.get('email'), password=form.cleaned_data.get('password1'))  # Create user
                p = Patient(user=nu, firstname=form.cleaned_data.get('firstname'),
                            lastname=form.cleaned_data.get('lastname'),
                            dob=form.cleaned_data.get('dob'),
                            address=form.cleaned_data.get('address'),
                            city=form.cleaned_data.get('city'),
                            country=form.cleaned_data.get('country'),
                            postalcode=form.cleaned_data.get('postalcode'),
                            image=request.FILES['image']
                            )  # Create patient
                p.save()
                path = PatHealth(patient=p, status=False)  # Create patient health instance for newly registered patient
                path.save()
                mpg = Group.objects.get_or_create(name='PATIENT')  # Add user to patient group
                mpg[0].user_set.add(nu)
                return redirect('login_pat.html')
            else:  # If date of birth is invalid
                form.add_error('dob', 'Invalid date of birth.')
                return render(request, 'hospital/Patient/register_pat.html', {'form': form})
        else:
            print(form.errors)
    else:
        form = PatientRegisterForm()
    return render(request, 'hospital/Patient/register_pat.html', {'form': form})


@login_required(login_url='login_pat.html')
def profile_pat_view(request):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        pat = Patient.objects.filter(user_id=request.user.id).first()
        db = pat.dob
        today = date.today()
        ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))  # Calculate age
        if request.method == "POST":
            p_form = PatientUpdateForm(request.POST, request.FILES, instance=pat)
            if p_form.is_valid():  # If form is valid
                db = p_form.cleaned_data.get('dob')  # Get date of birth from form
                today = date.today()
                ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))
                if db < timezone.now().date():  # If date of birth is valid
                    p_form.save()  # Save details
                    pat.age = ag  # Save age
                    pat.save()
                    return redirect('profile_pat.html')
                else:
                    p_form.add_error('dob', 'Invalid date of birth.')
                    context = {
                        'p_form': p_form,
                        'pat': pat,
                        'age': ag
                    }
                    return render(request, 'hospital/Patient/profile_pat.html', context)
            else:
                print(p_form.errors)
        p_form = PatientUpdateForm(instance=pat)
        context = {
            'p_form': p_form,
            'pat': pat,
            'age': ag
        }

        return render(request, 'hospital/Patient/profile_pat.html', context)
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def yourhealth_view(request):
    if check_patient(request.user):
        # Get information from the database and render it in the HTML webpage
        pat = Patient.objects.filter(user_id=request.user.id).first()
        info = PatHealth.objects.filter(patient=pat).first()
        # Calculate age
        db = pat.dob
        today = date.today()
        ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))
        if info.status:
            return render(request, 'hospital/Patient/yourhealth.html', {'info': info, 'pat': pat, 'age': ag})
        else:
            return redirect('edityourhealth.html')
    else:
        auth.logout(request)
        return redirect('login_pat.html')


@login_required(login_url='login_pat.html')
def edityourhealth_view(request):
    if check_patient(request.user):
        pat = Patient.objects.filter(user_id=request.user.id).first()
        info = PatHealth.objects.filter(patient=pat).first()
        if request.method == "POST":
            p_form = YourHealthEditForm(request.POST, instance=pat)
            if p_form.is_valid():   #if form is valid
                # Save PatHealth details from the form
                info.height = p_form.cleaned_data.get('height')
                info.weight = p_form.cleaned_data.get('weight')
                info.diseases = p_form.cleaned_data.get('diseases')
                info.medicines = p_form.cleaned_data.get('medicines')
                info.ts = p_form.cleaned_data.get('ts')
                info.status = True
                info.save()
                p_form.save()
                return render(request, 'hospital/Patient/yourhealth.html', {'info': info, 'pat': pat})
        else:
            # Get information from the database and set the placeholder for each form field
            info.refresh_from_db()
            p_form = YourHealthEditForm(instance=pat)
            p_form.fields['height'].initial = info.height
            p_form.fields['weight'].initial = info.weight
            p_form.fields['diseases'].initial = info.diseases
            p_form.fields['medicines'].initial = info.medicines
            p_form.fields['ts'].initial = info.ts
            context = {
                'p_form': p_form,
                'info': info,
                'pat': pat
            }
            return render(request, 'hospital/Patient/edityourhealth.html', context)
    else:
        auth.logout(request)
        return redirect('login_pat.html')


# Doctor Related Views

@login_required(login_url='login_doc.html')
def dash_doc_view(request):
    if check_doctor(request.user):
        # Get information from the database and render it in the HTML webpage
        doc = Doctor.objects.get(user_id=request.user.id)
        patcount = PatAdmit.objects.all().filter(doctor=doc, dischargeDate=None).count()
        patcountdis = PatAdmit.objects.all().filter(doctor=doc).count()
        patcountdis = patcountdis - patcount
        appcount = models.Appointment.objects.all().filter(status=True, doctor=doc).count()
        det = []
        for c in Appointment.objects.filter(status=False, doctor=doc).all():
            # Get all on-hold appointments of a given doctor
            p = c.patient
            if p:
                det.append([p.firstname, c.description, c.calldate, c.calltime, c.link, c.id])

        admt = []
        for c in PatAdmit.objects.filter(doctor=doc).all():
            # Get all admit details of a given doctor
            p = c.patient
            if p:
                admt.append([doc.firstname, p.firstname, c.admitDate, c.dischargeDate, c.pk])

        return render(request, 'hospital/Doctor/dashboard_doc.html', {'app': det, 'patcount': patcount, 'appcount': appcount, 'admt': admt, 'patcountdis': patcountdis})
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def dash_doc_approve_view(request, pk):
    if check_doctor(request.user):
        # Get information from the database
        appointment = Appointment.objects.get(id=pk)
        appointment.status = True  # Approve appointment
        appointment.save()
        doc = appointment.doctor
        dp = DoctorProfessional.objects.filter(doctor=doc).first()
        dp.totalpat += 1  # Add patient to doctor's patient count
        dp.save()
        return redirect(reverse('dashboard_doc.html'))  # Redirect to doctor's dashboard
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def bookapp_doc_view(request):
    if check_doctor(request.user):
        # Get information from the database and render in the HTML webpage
        doc = Doctor.objects.get(user_id=request.user.id)
        det = []
        for c in Appointment.objects.filter(status=True, doctor=doc.id, link__isnull=True, finished=False).all():
            # Get approved appointments which have links not set and are not yet finished for a given doctor
            p = Patient.objects.filter(id=c.patient.id).first()
            if p:
                det.append([p.firstname, c.description, c.calldate, c.pk, c.calltime])
        d = []
        for c in Appointment.objects.filter(status=True, doctor=doc.id, link__isnull=False, finished=False).all():
            # Get approved appointments which have links set and are not yet finished for a given doctor
            p = Patient.objects.filter(id=c.patient.id).first()
            if p:
                d.append([p.firstname, c.description, c.calldate, c.calltime, c.link, c.pk])
        k = []
        for c in Appointment.objects.filter(doctor=doc.id, finished=True).all():
            # Get finished appointments for a given doctor
            p = Patient.objects.filter(id=c.patient.id).first()
            if p:
                k.append([p.firstname, c.description, c.calldate, c.calltime, c.link, c.pk])
        return render(request, 'hospital/Doctor/bookapp_doc.html', {'app': det, 'sapp': d, 'hisapp': k})
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def appointment_details_particular_doc_view(request, pk):
    if check_doctor(request.user):
        ad = Appointment.objects.filter(id=pk).first()
        # Get the appointment
        pat = ad.patient
        doc = ad.doctor
        pathi = PatHealth.objects.filter(patient=pat).first()
        # Get the patient's health information
        db = pat.dob
        med = Medicines.objects.all()
        today = date.today()
        ag =  today.year - db.year - ((today.month, today.day) < (db.month, db.day))
        # Calculate the age
        det = [doc.firstname, pat.firstname, ad.calldate, ad.link, ad.calltime, ad.description, ad.pk, ad.finished]
        # Create a list with appointment details
        if request.method == "POST" and 'edit' in request.POST:
            p_form = AppointmentEditForm(request.POST, instance=ad)
            if p_form.is_valid():
                # If the form is valid, update the appointment description
                ad.description = p_form.cleaned_data.get('description')
                ad.save()
                p_form.save()
                p_form = AppointmentEditForm()
                q_form = AdmitRegisterForm()
                # Clear the forms for further use
                det = [doc.firstname, pat.firstname, ad.calldate, ad.link, ad.calltime, ad.description, ad.pk, ad.finished]
                return render(request, 'hospital/Doctor/appointment_details_particular_doc.html', {'app': det, 'p_form': p_form, 'q_form': q_form, 'pathi': pathi, 'ag': ag, 'med': med})
            else:
                print(p_form.errors)
        elif request.method == "POST" and 'admit' in request.POST:
            q_form = AdmitRegisterForm(request.POST, instance=doc)
            if q_form.is_valid():
                # If the form is valid, register the patient admission
                adt = PatAdmit(patient=pat, doctor=doc, admitDate=q_form.cleaned_data.get('admitDate'), description=q_form.cleaned_data.get('description'))
                adt.save()
                p_form = AppointmentEditForm()
                q_form = AdmitRegisterForm()
                # Clear the forms for further use
                det = [doc.firstname, pat.firstname, ad.calldate, ad.link, ad.calltime, ad.description, ad.pk, ad.finished]
                return render(request, 'hospital/Doctor/appointment_details_particular_doc.html', {'app': det, 'p_form': p_form, 'q_form': q_form, 'pathi': pathi, 'ag': ag, 'med': med})
            else:
                print(q_form.errors)
        p_form = AppointmentEditForm()
        q_form = AdmitRegisterForm()
        # Create instances of the appointment and admission forms
        return render(request, 'hospital/Doctor/appointment_details_particular_doc.html', {'app': det, 'p_form': p_form, 'q_form': q_form, 'pathi': pathi, 'ag': ag, 'med': med})
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def appointment_details_particular_doc_add_charge_view(request, pk, comm, quan):
    if check_doctor(request.user):
        ad = Appointment.objects.get(id=pk)
        # Get the appointment
        money = Medicines.objects.get(name=comm)
        # Get the medicine information
        ChargesApt.objects.create(Aptinfo=ad, commodity=money, quantity=quan)
        # Create a new ChargesApt object with appointment, medicine, and quantity
        adr = '/hospital/bookapp_doc/' + str(ad.pk)
        # Create the redirect URL
        return redirect(adr)
        # Redirect to the appointment details page
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def endappointment_doc_view(request, pk):
    if check_doctor(request.user):
        ap = Appointment.objects.get(id=pk)
        # Get the appointment
        ap.finished = True
        ap.save()
        # Mark the appointment as finished
        pat = ap.patient
        # Get the associated patient
        yh = PatHealth.objects.all().filter(patient=pat).first()
        # Get the patient's health information
        yh.diseases = yh.diseases + "\n" + ap.description
        # Add the appointment description to the patient's diseases
        for i in ChargesApt.objects.all().filter(Aptinfo=ap):
            yh.medicines = yh.medicines + "\n" + i.commodity + "-" + i.quantity
        # Add the medicines and quantities from ChargesApt to the patient's medicines
        yh.save()
        # Save the updated patient's health information
        return redirect('bookapp_doc.html')
        # Redirect to the book appointments page for the doctor
    else:
        print("4")
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def bookapp_doc_link_view(request, pk, link):
    if check_doctor(request.user):
        appointment = Appointment.objects.get(id=pk)
        # Get the appointment
        appointment.link = link
        # Set the appointment's link
        appointment.save()
        # Save the updated appointment
        return redirect(reverse('bookapp_doc.html'))
        # Redirect to the book appointments page for the doctor
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def feedback_doc_view(request):
    if check_doctor(request.user):
        sub = forms.ContactusForm()
        # Create a ContactusForm instance
        if request.method == 'POST':
            sub = forms.ContactusForm(request.POST)
            # Create a ContactusForm instance with POST data
            if sub.is_valid():
                email = sub.cleaned_data['Email']
                # Get email from the form
                name = sub.cleaned_data['Name']
                # Get name from the form
                message = sub.cleaned_data['Message']
                # Get message from the form
                try:
                    send_mail(str(name) + ' || ' + str(email), message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently=False)
                    # Send email
                    return redirect('feedback_doc.html')
                except:
                    sub.add_error('Email', 'please turn on access to less secured apps from your gmail account')
                    # Add error to the form
                    return render(request, 'hospital/Doctor/feedback_doc.html', {'form': sub})
        return render(request, 'hospital/Doctor/feedback_doc.html', {'form': sub})
    else:
        auth.logout(request)
        return redirect('login_doc.html')

def login_doc_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request=request, data=request.POST)
        # Create an AuthenticationForm instance with POST data
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = auth.authenticate(username=username, password=password)
            # Authenticate the user
            if user is not None and check_doctor(user):
                auth.login(request, user)
                # Log in the user
                accountapproval = Doctor.objects.all().filter(status=True, user_id=request.user.id)
                if accountapproval:
                    return redirect('profile_doc.html')
                else:
                    return render(request, 'hospital/Home/wait_approval.html')
        return render(request, 'hospital/Doctor/login_doc.html', {'form': form})
    else:
        form = AuthenticationForm()

    return render(request, 'hospital/Doctor/login_doc.html', {'form': form})

def register_doc_view(request):
    if request.method == "POST":
        form = DoctorRegisterForm(request.POST, request.FILES)
        # Create a DoctorRegisterForm instance with POST data
        if form.is_valid():
            db = form.cleaned_data.get('dob')
            # Get date of birth from the form
            if db < timezone.now().date():
                # If date of birth is valid
                nu = User.objects.create_user(username=form.cleaned_data.get('username'), email=form.cleaned_data.get('email'), password=form.cleaned_data.get('password1'))
                # Create a new user
                doc = Doctor(user=nu, firstname=form.cleaned_data.get('firstname'), lastname=form.cleaned_data.get('lastname'), department=form.cleaned_data.get('department'), dob=form.cleaned_data.get('dob'), address=form.cleaned_data.get('address'), city=form.cleaned_data.get('city'), country=form.cleaned_data.get('country'), postalcode=form.cleaned_data.get('postalcode'), image=request.FILES['image'])
                # Create a new doctor
                doc.save()
                dp = DoctorProfessional(doctor=doc, appfees=200, admfees=2000)
                # Create a DoctorProfessional instance with default prices
                dp.save()
                mpg = Group.objects.get_or_create(name='DOCTOR')
                mpg[0].user_set.add(nu)
                # Add user to doctor group
                return redirect('login_doc.html')
            else:
                # If date of birth is invalid
                form.add_error('dob', 'Invalid date of birth.')
                return render(request, 'hospital/Doctor/register_doc.html', {'form': form})
        else:
            print(form.errors)
    else:
        form = DoctorRegisterForm()

    return render(request, 'hospital/Doctor/register_doc.html', {'form': form})


@login_required(login_url='login_doc.html')
def profile_doc_view(request):
    if check_doctor(request.user):
        # Get information from the database and render it in the HTML webpage
        doc = Doctor.objects.filter(user_id=request.user.id).first()
        # Get the doctor's information
        db = doc.dob
        today = date.today()
        ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))
        # Calculate the age of the doctor
        if request.method == "POST":
            p_form = DoctorUpdateForm(request.POST, request.FILES, instance=doc)
            # Create a DoctorUpdateForm instance with POST data and doctor instance
            if p_form.is_valid():
                db = p_form.cleaned_data.get('dob')
                today = date.today()
                ag = today.year - db.year - ((today.month, today.day) < (db.month, db.day))
                # Recalculate the age based on the updated date of birth
                if db < timezone.now().date():
                    # If the date of birth is valid
                    p_form.save()
                    # Save the updated form data
                    dp = DoctorProfessional.objects.all().filter(doctor=doc).first()
                    # Get the doctor's professional details
                    dp.appfees = p_form.cleaned_data.get('appfees')
                    dp.admfees = p_form.cleaned_data.get('admfees')
                    dp.save()
                    # Update the doctor's professional data
                    return redirect('profile_doc.html')
                else:
                    p_form.add_error('dob', 'Invalid date of birth.')
                    # Add an error to the form
                    context = {
                        'p_form': p_form,
                        'doc': doc,
                        'age': ag
                    }
                    return render(request, 'hospital/Doctor/profile_doc.html', context)
        else:
            # Get data from the database and put initial values in the form
            doc.refresh_from_db()
            dp = DoctorProfessional.objects.all().filter(doctor=doc).first()
            # Get the doctor's professional details
            p_form = DoctorUpdateForm(instance=doc)
            p_form.fields['appfees'].initial = dp.appfees
            p_form.fields['admfees'].initial = dp.admfees
            # Set initial values for the appfees and admfees fields
            context = {
                'p_form': p_form,
                'doc': doc,
                'age': ag
            }
            return render(request, 'hospital/Doctor/profile_doc.html', context)
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def admit_details_doc_view(request):
    if check_doctor(request.user):
        doc = Doctor.objects.get(user_id=request.user.id)
        # Get the doctor's information
        det = []
        for c in PatAdmit.objects.filter(doctor=doc).all():
            # Iterate over all patients admitted under the given doctor
            p = c.patient
            if p and not (c.dischargeDate):
                # Check if the patient exists and hasn't been discharged yet
                det.append([doc.firstname, p.firstname, c.admitDate, c.dischargeDate, c.pk])
                # Append the admission details to the 'det' list
        d = []
        for c in PatAdmit.objects.filter(doctor=doc).all():
            # Iterate over all patients admitted under the given doctor
            p = c.patient
            if p and c.dischargeDate:
                # Check if the patient exists and has been discharged
                d.append([doc.firstname, p.firstname, c.admitDate, c.dischargeDate, c.pk])
                # Append the discharge details to the 'd' list
        return render(request, 'hospital/Doctor/admit_details_doc.html', {'app': det, 'appi': d})
        # Render the HTML webpage with the admission and discharge details
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def admit_details_particular_doc_view(request, pk):
    if check_doctor(request.user):
        ad = PatAdmit.objects.filter(id=pk).first()
        # Get the specific patient admission details based on the provided ID
        doci = Doctor.objects.get(user_id=request.user.id)
        doci = doci.department
        # Get the department of the doctor currently logged in
        pat = ad.patient
        doc = ad.doctor
        # Get the patient and doctor associated with the admission details
        det = [ad.pk, doc.firstname, pat.firstname, ad.admitDate, ad.dischargeDate, ad.description]
        # Create a list with the admission details to render in the HTML webpage
        med = Medicines.objects.all()
        # Get all available medicines
        return render(request, 'hospital/Doctor/admit_details_particular_doc.html', {'app': det, 'doci': doci, 'med': med})
        # Render the HTML webpage with the admission details, doctor department, and medicines
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def admit_details_particular_doc_add_charge_view(request, pk, comm, quan):
    if check_doctor(request.user):
        ad = PatAdmit.objects.get(id=pk)
        # Get the specific patient admission details based on the provided ID
        money = Medicines.objects.get(name=comm)
        # Get the medicine object based on the provided name
        Charges.objects.create(Admitinfo=ad, commodity=money, quantity=quan)
        # Create a new charge entry for the admission with the specified medicine and quantity
        adr = '/hospital/admit_details_doc/' + str(ad.pk)
        # Construct the URL for redirecting to the admission details page
        return redirect(adr)
        # Redirect to the admission details page
    else:
        auth.logout(request)
        return redirect('login_doc.html')


@login_required(login_url='login_doc.html')
def discharge_doc_view(request,pk):
    if check_doctor(request.user):
        #get information from database and render in html webpage
        ad = PatAdmit.objects.get(id=pk)
        ad.dischargeDate=date.today()
        ad.save()
        pat=ad.patient
        yh = PatHealth.objects.all().filter(patient=pat).first()
        yh.diseases = yh.diseases + "\n" + ad.description
        for i in Charges.objects.all().filter(Aptinfo=ap):
            yh.medicines = yh.medicines + "\n" + i.commodity + "-" + i.quantity
        yh.save()
        return redirect('admit_details_doc.html')
    else:
        auth.logout(request)
        return redirect('login_doc.html')

def home_view(request):
    return render(request,'hospital/Home/home.html')


def login_view(request):
    return render(request,'hospital/Home/login.html')


def bill_view(request,pk):
    #get information from database and render in html webpage
    padm=PatAdmit.objects.all().filter(id=pk).first()
    pat=padm.patient
    doc=padm.doctor
    d1=padm.admitDate
    if padm.dischargeDate:
        d2=padm.dischargeDate
    else:
        d2=date.today()
    days=(d2-d1).days
    room=OperationCosts.objects.all().filter(name='Room').first()
    roomcharges=room.cost
    total_room_charge=roomcharges*days
    docpro=DoctorProfessional.objects.all().filter(doctor=doc).first()
    docfee=docpro.admfees
    hosp=OperationCosts.objects.all().filter(name='Hospital Fee').first()
    hospfee=hosp.cost
    mainp=OperationCosts.objects.all().filter(name='Maintenance').first()
    mainfee=mainp.cost
    OtherCharge=mainfee+hospfee
    tot=OtherCharge+docfee+total_room_charge
    det=[]
    for i in Charges.objects.all().filter(Admitinfo=padm):
        for k in Medicines.objects.all():
            if k==i.commodity:
                tot+=i.quantity*k.price
                det.append([k.name,i.quantity,k.price,i.quantity*k.price])
    dict={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'admitDate':d1,
            'releaseDate':d2,
            'roomcharges':roomcharges,
            'desc':padm.description,
            'pat_add':pat.address,
            'days':days,
            'tot':tot,
            'tc':total_room_charge,
            'doctorFee': docfee,
            'OtherCharge': OtherCharge,
            'mainp': mainfee,
            'hospfee': hospfee,
            'med': det,
            'pk': pk
        }
    if check_patient(request.user):
        return render(request,'hospital/Patient/bill.html',dict)
    elif check_doctor(request.user):
        return render(request,'hospital/Doctor/bill.html',dict)
    elif check_admin(request.user):
        return render(request,'hospital/Admin/bill.html',dict)
    else:
        return render(request,'hospital/Home/login.html')


def bill_apt_view(request,pk):
    #get information from database and render in html webpage
    apt=Appointment.objects.all().filter(id=pk).first()
    pat=apt.patient
    doc=apt.doctor
    d=apt.calldate
    t=apt.calltime
    docpro=DoctorProfessional.objects.all().filter(doctor=doc).first()
    docfee=docpro.appfees
    hosp=OperationCosts.objects.all().filter(name='Hospital Fee').first()
    hospfee=hosp.cost
    mainp=OperationCosts.objects.all().filter(name='Maintenance').first()
    mainfee=mainp.cost
    OtherCharge=mainfee+hospfee
    tot=OtherCharge+docfee
    det=[]
    for i in ChargesApt.objects.all().filter(Aptinfo=apt):
        for k in Medicines.objects.all():
            if k==i.commodity:
                tot+=i.quantity*k.price
                det.append([k.name,i.quantity,k.price,i.quantity*k.price])
    dict={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'aptDate':d,
            'aptTime':t,
            'desc':apt.description,
            'pat_add':pat.address,
            'tot':tot,
            'doctorFee': docfee,
            'OtherCharge': OtherCharge,
            'mainp': mainfee,
            'hospfee': hospfee,
            'med': det,
            'pk': pk
        }
    if check_patient(request.user):
        return render(request,'hospital/Patient/bill_apt.html',dict)
    elif check_doctor(request.user):
        return render(request,'hospital/Doctor/bill_apt.html',dict)
    elif check_admin(request.user):
        return render(request,'hospital/Admin/bill_apt.html',dict)
    else:
        return render(request,'hospital/Home/login.html')


def report_view(request,pk):
    #get information from database and render in html webpage
    padm=PatAdmit.objects.all().filter(id=pk).first()
    pat=padm.patient
    doc=padm.doctor
    d1=padm.admitDate
    if padm.dischargeDate:
        d2=padm.dischargeDate
    else:
        d2=date.today()
    days=(d2-d1).days
    det=[]
    for i in Charges.objects.all().filter(Admitinfo=padm):
        for k in Medicines.objects.all():
            if k==i.commodity:
                det.append([k.name])
    dict={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'admitDate':d1,
            'releaseDate':d2,
            'desc':padm.description,
            'pat_add':pat.address,
            'days':days,
            'med': det,
            'pk': pk
        }
    if check_patient(request.user):
        return render(request,'hospital/Patient/report.html',dict)
    elif check_doctor(request.user):
        return render(request,'hospital/Doctor/report.html',dict)
    elif check_admin(request.user):
        return render(request,'hospital/Admin/report.html',dict)
    else:
        return render(request,'hospital/Home/login.html')


def report_apt_view(request,pk):
    #get information from database and render in html webpage
    apt=Appointment.objects.all().filter(id=pk).first()
    pat=apt.patient
    doc=apt.doctor
    d=apt.calldate
    t=apt.calltime
    det=[]
    for i in ChargesApt.objects.all().filter(Aptinfo=apt):
        for k in Medicines.objects.all():
            if k==i.commodity:
                det.append([k.name])
    dict={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'aptDate':d,
            'aptTime':t,
            'desc':apt.description,
            'pat_add':pat.address,
            'med': det,
            'pk': pk
        }
    if check_patient(request.user):
        return render(request,'hospital/Patient/report_apt.html',dict)
    elif check_doctor(request.user):
        return render(request,'hospital/Doctor/report_apt.html',dict)
    elif check_admin(request.user):
        return render(request,'hospital/Admin/report_apt.html',dict)
    else:
        return render(request,'hospital/Home/login.html')
    

def check_admin(user):  #check if user is admin
    return user.groups.filter(name='ADMIN').exists()
def check_doctor(user): #check if user is doctor
    return user.groups.filter(name='DOCTOR').exists()
def check_patient(user):#check if user is patient
    return user.groups.filter(name='PATIENT').exists()


def render_pdf_report_view(request,pk):
    #get information from database
    template_path = 'hospital/report_pdf.html'
    padm=PatAdmit.objects.all().filter(id=pk).first()
    pat=padm.patient
    doc=padm.doctor
    d1=padm.admitDate
    if padm.dischargeDate:
        d2=padm.dischargeDate
    else:
        d2=date.today()
    days=(d2-d1).days
    det=[]
    for i in Charges.objects.all().filter(Admitinfo=padm):
        for k in Medicines.objects.all():
            if k==i.commodity:
                det.append([k.name])
    context={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'admitDate':d1,
            'releaseDate':d2,
            'desc':padm.description,
            'pat_add':pat.address,
            'days':days,
            'med': det
        }
    #context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def render_pdf_bill_view(request,pk):
    #get information from database
    template_path = 'hospital/bill_pdf.html'
    padm=PatAdmit.objects.all().filter(id=pk).first()
    pat=padm.patient
    doc=padm.doctor
    d1=padm.admitDate
    if padm.dischargeDate:
        d2=padm.dischargeDate
    else:
        d2=date.today()
    days=(d2-d1).days
    room=OperationCosts.objects.all().filter(name='Room').first()
    roomcharges=room.cost
    total_room_charge=roomcharges*days
    docpro=DoctorProfessional.objects.all().filter(doctor=doc).first()
    docfee=docpro.admfees
    hosp=OperationCosts.objects.all().filter(name='Hospital Fee').first()
    hospfee=hosp.cost
    mainp=OperationCosts.objects.all().filter(name='Maintenance').first()
    mainfee=mainp.cost
    OtherCharge=mainfee+hospfee
    tot=OtherCharge+docfee+total_room_charge
    det=[]
    for i in Charges.objects.all().filter(Admitinfo=padm):
        for k in Medicines.objects.all():
            if k==i.commodity:
                tot+=i.quantity*k.price
                det.append([k.name,i.quantity,k.price,i.quantity*k.price])
    context={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'admitDate':d1,
            'releaseDate':d2,
            'roomCharge':roomcharges,
            'desc':padm.description,
            'pat_add':pat.address,
            'days':days,
            'tot':tot,
            'tc':total_room_charge,
            'doctorFee': docfee,
            'OtherCharge': OtherCharge,
            'mainp': mainfee,
            'hospfee': hospfee,
            'med': det
        }
    #context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response

######apt

def render_pdf_report_apt_view(request,pk):
    #get information from database
    template_path = 'hospital/report_apt_pdf.html'
    apt=Appointment.objects.all().filter(id=pk).first()
    pat=apt.patient
    doc=apt.doctor
    d=apt.calldate
    t=apt.calltime
    det=[]
    for i in ChargesApt.objects.all().filter(Aptinfo=apt):
        for k in Medicines.objects.all():
            if k==i.commodity:
                det.append([k.name])
    context={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'aptDate':d,
            'aptTime':t,
            'desc':apt.description,
            'pat_add':pat.address,
            'med': det
        }
    #context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


def render_pdf_bill_apt_view(request,pk):
    #get information from database
    template_path = 'hospital/bill_apt_pdf.html'
    apt=Appointment.objects.all().filter(id=pk).first()
    pat=apt.patient
    doc=apt.doctor
    d=apt.calldate
    t=apt.calltime
    docpro=DoctorProfessional.objects.all().filter(doctor=doc).first()
    docfee=docpro.appfees
    hosp=OperationCosts.objects.all().filter(name='Hospital Fee').first()
    hospfee=hosp.cost
    mainp=OperationCosts.objects.all().filter(name='Maintenance').first()
    mainfee=mainp.cost
    OtherCharge=mainfee+hospfee
    tot=OtherCharge+docfee
    det=[]
    for i in ChargesApt.objects.all().filter(Aptinfo=apt):
        for k in Medicines.objects.all():
            if k==i.commodity:
                tot+=i.quantity*k.price
                det.append([k.name,i.quantity,k.price,i.quantity*k.price])
    context={
            'patientName':pat.firstname,
            'doctorName':doc.firstname,
            'aptDate':d,
            'aptTime':t,
            'desc':apt.description,
            'pat_add':pat.address,
            'tot':tot,
            'doctorFee': docfee,
            'OtherCharge': OtherCharge,
            'mainp': mainfee,
            'hospfee': hospfee,
            'med': det
        }
    #context = {'myvar': 'this is your template context'}
    # Create a Django response object, and specify content_type as pdf
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    # find the template and render it.
    template = get_template(template_path)
    html = template.render(context)

    # create a pdf
    pisa_status = pisa.CreatePDF(
       html, dest=response)
    # if error then show some funy view
    if pisa_status.err:
       return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


@login_required(login_url='login_adm.html')
def track_med_view(request, name):
    if check_admin(request.user):
        # Check if the user is an admin, and if so, proceed with tracking the medication

        # Initialize an empty list to store medication details
        det = []

        # Retrieve charges related to the specified commodity from the database
        meds = Charges.objects.filter(commodity__name=name).all()
        for med in meds:
            # Retrieve relevant information for each charge and append it to the 'det' list
            det.append([
                med.Admitinfo.patient.firstname,  # Patient's first name associated with the charge
                med.Admitinfo.patient.lastname,   # Patient's last name associated with the charge
                med.quantity,                      # Quantity of the medication
                med.Admitinfo.doctor.firstname,    # Doctor's first name associated with the charge
                med.Admitinfo.doctor.lastname,     # Doctor's last name associated with the charge
                med.Admitinfo.admitDate            # Admission date associated with the charge
            ])

        # Retrieve charges from appointments related to the specified commodity from the database
        admeds = ChargesApt.objects.filter(commodity__name=name).all()
        for med in admeds:
            # Retrieve relevant information for each appointment charge and append it to the 'det' list
            det.append([
                med.Aptinfo.patient.firstname,     # Patient's first name associated with the appointment charge
                med.Aptinfo.patient.lastname,      # Patient's last name associated with the appointment charge
                med.quantity,                      # Quantity of the medication
                med.Aptinfo.doctor.firstname,      # Doctor's first name associated with the appointment charge
                med.Aptinfo.doctor.lastname,       # Doctor's last name associated with the appointment charge
                med.Aptinfo.calldate               # Call date associated with the appointment charge
            ])

        # Render the 'particular_medtrack.html' template with the medication details
        return render(request, 'hospital/Admin/particular_medtrack.html', {'app': det})
    else:
        # If the user is not an admin, log out the user and redirect to the login page
        auth.logout(request)
        return redirect('login_adm.html')

    
@login_required(login_url='login_adm.html')
def covid_vaccine_adm_view(request):
    if check_admin(request.user):
        # Check if the user is an admin, and if so, proceed with rendering COVID vaccine information

        # Initialize an empty list to store vaccine details
        det = []

        # Retrieve charges related to covaxin from the database
        meds = Charges.objects.filter(commodity__name="covaxin").all()
        for med in meds:
            # Retrieve relevant information for each charge and append it to the 'det' list
            det.append([
                med.Admitinfo.patient.firstname,  # Patient's first name associated with the charge
                med.Admitinfo.patient.lastname,   # Patient's last name associated with the charge
                med.quantity,                      # Quantity of the medication
                med.Admitinfo.doctor.firstname,    # Doctor's first name associated with the charge
                med.Admitinfo.doctor.lastname,     # Doctor's last name associated with the charge
                med.Admitinfo.admitDate,           # Admission date associated with the charge
                "covaxin"                          # Vaccine name (covaxin)
            ])

        # Retrieve charges from appointments related to covaxin from the database
        admeds = ChargesApt.objects.filter(commodity__name="covaxin").all()
        for med in admeds:
            # Retrieve relevant information for each appointment charge and append it to the 'det' list
            det.append([
                med.Aptinfo.patient.firstname,     # Patient's first name associated with the appointment charge
                med.Aptinfo.patient.lastname,      # Patient's last name associated with the appointment charge
                med.quantity,                      # Quantity of the medication
                med.Aptinfo.doctor.firstname,      # Doctor's first name associated with the appointment charge
                med.Aptinfo.doctor.lastname,       # Doctor's last name associated with the appointment charge
                med.Aptinfo.calldate,              # Call date associated with the appointment charge
                "covaxin"                          # Vaccine name (covaxin)
            ])

        # Retrieve charges related to covishield from the database
        meds = Charges.objects.filter(commodity__name="covishield").all()
        for med in meds:
            # Retrieve relevant information for each charge and append it to the 'det' list
            det.append([
                med.Admitinfo.patient.firstname,  # Patient's first name associated with the charge
                med.Admitinfo.patient.lastname,   # Patient's last name associated with the charge
                med.quantity,                      # Quantity of the medication
                med.Admitinfo.doctor.firstname,    # Doctor's first name associated with the charge
                med.Admitinfo.doctor.lastname,     # Doctor's last name associated with the charge
                med.Admitinfo.admitDate,           # Admission date associated with the charge
                "covishield"                       # Vaccine name (covishield)
            ])

        # Retrieve charges from appointments related to covishield from the database
        admeds = ChargesApt.objects.filter(commodity__name="covishield").all()
        for med in admeds:
            # Retrieve relevant information for each appointment charge and append it to the 'det' list
            det.append([
                med.Aptinfo.patient.firstname,     # Patient's first name associated with the appointment charge
                med.Aptinfo.patient.lastname,      # Patient's last name associated with the appointment charge
                med.quantity,                      # Quantity of the medication
                med.Aptinfo.doctor.firstname,      # Doctor's first name associated with the appointment charge
                med.Aptinfo.doctor.lastname,       # Doctor's last name associated with the appointment charge
                med.Aptinfo.calldate,              # Call date associated with the appointment charge
                "covishield"                       # Vaccine name (covishield)
            ])

        # Retrieve covaxin and covishield information from the Medicines table in the database
        covaxin = Medicines.objects.all().filter(name="covaxin").first()
        covishield = Medicines.objects.all().filter(name="covishield").first()

        # Count the total number of CovidVaccination records in the database
        tot = CovidVaccination.objects.all().count()

        # Count the total charges for covaxin from both admissions and appointments
        t1 = Charges.objects.filter(commodity__name="covaxin").all().count()
        t2 = ChargesApt.objects.filter(commodity__name="covaxin").all().count()

        # Count the total charges for covishield from both admissions and appointments
        t3 = Charges.objects.filter(commodity__name="covishield").all().count()
        t4 = ChargesApt.objects.filter(commodity__name="covishield").all().count()

        # Store the relevant information in a list
        d = [
            covaxin.name,         # Covaxin name
            covaxin.price,        # Covaxin price
            covishield.name,      # Covishield name
            covishield.price,     # Covishield price
            tot,                  # Total number of CovidVaccination records
            t1 + t2,              # Total charges for covaxin
            t3 + t4               # Total charges for covishield
        ]

        # Retrieve all CovidVaccination records from the database
        cv = CovidVaccination.objects.all()

        # Render the 'covid_vaccine_adm.html' template with the vaccine details and information
        return render(request, 'hospital/Admin/covid_vaccine_adm.html', {'app': det, 'info': d, 'cvv': cv})
    else:
        # If the user is not an admin, log out the user and redirect to the login page
        auth.logout(request)
        return redirect('login_adm.html')