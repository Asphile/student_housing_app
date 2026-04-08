import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, abort
from flask_login import login_required, current_user
from flask_mail import Message  # Added for email functionality
from app import db, mail        # Added 'mail' import
from app.models.housing import RoommatePreferences, HousingListing, RoomApplication, Allocation
from app.models.user import User
from app.forms import PreferenceForm, ResidenceForm, HousingForm

main = Blueprint('main', __name__)

# --- Helper: Save Images ---
def save_image(form_picture, folder):
    """Saves image to static/uploads/<folder> and returns the filename."""
    try:
        ext = os.path.splitext(form_picture.filename)[1]
        filename = f"{os.urandom(8).hex()}{ext}"
        
        upload_path = os.path.join(current_app.root_path, 'static', 'uploads', folder)
        
        # Ensure directory exists
        if not os.path.exists(upload_path):
            os.makedirs(upload_path, exist_ok=True)
            
        file_path = os.path.join(upload_path, filename)
        
        # Save the file
        form_picture.save(file_path)
        
        # Verify file was saved
        if os.path.exists(file_path):
            current_app.logger.info(f"Image saved successfully: {file_path}")
            return filename
        else:
            raise OSError("File was not saved successfully")
            
    except Exception as e:
        current_app.logger.error(f"Error saving image to {folder}: {e}")
        raise OSError(f"Failed to save image: {str(e)}")

# --- 1. Dashboards ---
@main.route('/')
def index():
    """System entry point. Handles authenticated redirection to maintain session flow."""
    try:
        if current_user.is_authenticated:
            if current_user.email == 'studenthousing@dut4life.ac.za':
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.dashboard'))
        return render_template('index.html')
    except Exception as e:
        current_app.logger.error(f"Error in index route: {e}")
        # Fallback to showing index page if there's any error
        return render_template('index.html')

@main.route('/debug')
def debug():
    """Debug endpoint to check app status"""
    try:
        from app.models.user import User
        user_count = User.query.count()
        return f"""
        <h1>Debug Info</h1>
        <p>App Status: Running</p>
        <p>Database: Connected</p>
        <p>User Count: {user_count}</p>
        <p>Time: {datetime.utcnow()}</p>
        """
    except Exception as e:
        return f"""
        <h1>Debug Info</h1>
        <p>App Status: Error</p>
        <p>Error: {str(e)}</p>
        <p>Time: {datetime.utcnow()}</p>
        """, 500

@main.route('/health')
def health():
    """Health check endpoint for Render"""
    try:
        # Test database connection
        from app.models.user import User
        User.query.count()
        return "Database connected", 200
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return f"Database error: {str(e)}", 500

@main.route('/dashboard')
@login_required
def dashboard():
    try:
        # Check if admin is logging in
        if current_user.email == 'studenthousing@dut4life.ac.za':
            return redirect(url_for('main.admin_dashboard'))

        has_prefs = RoommatePreferences.query.filter_by(user_id=current_user.id).first() is not None
        active_app = RoomApplication.query.filter_by(user_id=current_user.id).first()
        allocation = Allocation.query.filter_by(user_id=current_user.id).first()
        
        user_img = current_user.image_file if current_user.image_file else 'default.jpg'
        image_file = url_for('static', filename=f'uploads/profile_pics/{user_img}')
        
        return render_template('dashboard.html', 
                                has_preferences=has_prefs,
                                active_app=active_app,
                                allocation=allocation,
                                image_file=image_file)
    except Exception as e:
        current_app.logger.error(f"Error in dashboard route: {e}")
        # Fallback to basic dashboard
        return render_template('dashboard.html', 
                                has_preferences=False,
                                active_app=None,
                                allocation=None,
                                image_file=url_for('static', filename='uploads/profile_pics/default.jpg'))

@main.route("/admin/dashboard")
@login_required
def admin_dashboard():
    try:
        if current_user.email != 'studenthousing@dut4life.ac.za':
            abort(403) 
        
        total_res = HousingListing.query.count()
        pending = RoomApplication.query.filter_by(status='Pending').count()
        all_students = User.query.filter(User.email != 'studenthousing@dut4life.ac.za').all()
        
        return render_template('admin_dashboard.html', total_res=total_res, pending=pending, users=all_students)
    except Exception as e:
        current_app.logger.error(f"Error in admin dashboard route: {e}")
        # Fallback to basic admin dashboard
        return render_template('admin_dashboard.html', total_res=0, pending=0, users=[])

# --- 2. Admin Management ---

@main.route("/admin/add-residence", methods=['GET', 'POST'])
@login_required
def add_residence():
    if current_user.email != 'studenthousing@dut4life.ac.za':
        abort(403)

    form = HousingForm()
    residences = HousingListing.query.all()

    if form.validate_on_submit():
        image_file = 'default_res.jpg'
        if form.image.data:
            image_file = save_image(form.image.data, 'residence_pics')
            
        new_res = HousingListing(
            name=form.name.data,
            region=form.region.data,
            gender_type=form.gender.data,
            address=form.address.data,
            capacity=form.capacity.data,
            available_rooms=form.capacity.data,
            description=form.description.data,
            image_file=image_file
        )
        db.session.add(new_res)
        db.session.commit()
        flash(f'Residence "{form.name.data}" added successfully!', 'success')
        return redirect(url_for('main.add_residence'))

    return render_template('add_residence.html', form=form, residences=residences)

@main.route("/admin/delete-residence/<int:res_id>", methods=['POST'])
@login_required
def delete_residence(res_id):
    if current_user.email != 'studenthousing@dut4life.ac.za':
        abort(403)

    res = HousingListing.query.get_or_404(res_id)
    try:
        db.session.delete(res)
        db.session.commit()
        flash(f'Residence "{res.name}" has been removed.', 'success')
    except:
        db.session.rollback()
        flash('Could not delete residence. Active student allocations exist.', 'danger')

    return redirect(url_for('main.add_residence'))

@main.route("/admin/student_profile/<int:user_id>")
@login_required
def student_profile(user_id):
    if current_user.email != 'studenthousing@dut4life.ac.za':
        abort(403)
    
    student = User.query.get_or_404(user_id)
    prefs = RoommatePreferences.query.filter_by(user_id=user_id).first()
    
    allocation = Allocation.query.filter_by(user_id=user_id).first()
    
    img = student.image_file if student.image_file else 'default.jpg'
    image_file = url_for('static', filename=f'uploads/profile_pics/{img}')
    
    return render_template('student_profile.html', 
                           student=student, 
                           preferences=prefs, 
                           allocation=allocation, 
                           image_file=image_file)

@main.route("/admin/allocate", methods=['GET', 'POST'])
@login_required
def admin_allocate():
    if current_user.email != 'studenthousing@dut4life.ac.za':
        abort(403)

    if request.method == 'POST':
        res_id = request.form.get('residence_id')
        room_no = request.form.get('room_number')
        student_ids = request.form.getlist('student_ids')
        
        res = HousingListing.query.get(res_id)
        
        for s_id in student_ids:
            student = User.query.get(s_id) # Fetch student to get email
            if not Allocation.query.filter_by(user_id=s_id).first():
                if res and res.available_rooms > 0:
                    new_alloc = Allocation(user_id=s_id, listing_id=res_id, room_number=room_no, status='Pending')
                    db.session.add(new_alloc)
                    
                    app = RoomApplication.query.filter_by(user_id=s_id).first()
                    if app: 
                        app.status = 'Allocated'
                    
                    res.available_rooms -= 1

                    # --- ADDED: Email Notification for Allocation ---
                    try:
                        msg = Message('DUT Housing: Room Allocation Notification',
                                      recipients=[student.email])
                        msg.body = f"Hello {student.username},\n\nYou have been allocated a room at {res.name}, Room {room_no}. Please log in to the portal to accept your offer."
                        mail.send(msg)
                    except Exception as e:
                        print(f"Mail failed: {e}")
                    # -----------------------------------------------

                else:
                    flash(f'Capacity reached for {res.name}.', 'warning')
                    break
        db.session.commit()
        flash('Allocation process updated and students notified via email!', 'success')
        return redirect(url_for('main.admin_allocate'))

    allocated_ids = [a.user_id for a in Allocation.query.all()]
    unallocated = User.query.filter(User.email != 'studenthousing@dut4life.ac.za', 
                                    ~User.id.in_(allocated_ids) if allocated_ids else True).all()
    
    return render_template('admin_allocate.html', 
                            unallocated_students=unallocated, 
                            active_allocations=Allocation.query.all(), 
                            residences=HousingListing.query.all())

@main.route("/admin/cancel_allocation/<int:allocation_id>", methods=['POST'])
@login_required
def cancel_allocation(allocation_id):
    if current_user.email != 'studenthousing@dut4life.ac.za':
        abort(403)

    alloc = Allocation.query.get_or_404(allocation_id)
    res = HousingListing.query.get(alloc.listing_id)
    app = RoomApplication.query.filter_by(user_id=alloc.user_id).first()

    if res:
        res.available_rooms += 1
    if app:
        app.status = 'Pending'

    db.session.delete(alloc)
    db.session.commit()
    flash('Allocation cancelled and room capacity restored.', 'info')
    return redirect(url_for('main.admin_allocate'))

# --- 3. Student Registration & Profile ---

@main.route('/residence-registration', methods=['GET', 'POST'])
@login_required
def residence_registration():
    form = ResidenceForm()
    
    if form.validate_on_submit():
        # Update every single field from the form to the current_user
        current_user.student_number = form.student_number.data
        current_user.id_number = form.student_id.data
        current_user.cell_number = form.cell_number.data
        current_user.full_names = form.full_names.data
        current_user.surname = form.surname.data
        current_user.age = form.age.data
        current_user.gender = form.gender.data
        
        current_user.nok_name = form.nok_name.data
        current_user.nok_relationship = form.nok_relationship.data
        current_user.nok_cell = form.nok_cell.data
        
        current_user.home_address = form.home_address.data
        current_user.province = form.province.data
        current_user.campus = form.campus.data
        
        current_user.faculty = form.faculty.data
        current_user.level_of_study = form.level_of_study.data
        current_user.qualification = form.qualification.data

        if form.profile_picture.data:
            current_user.image_file = save_image(form.profile_picture.data, 'profile_pics')
            
        db.session.commit() # This saves everything to the database

        # Email logic stays the same...
        try:
            msg = Message('Residence Registration Successful', recipients=[current_user.email])
            msg.body = f"Hello {current_user.full_names}, your registration is successful."
            mail.send(msg)
        except Exception as e:
            print(f"Mail failed: {e}")

        flash('Registration submitted successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    img = current_user.image_file if current_user.image_file else 'default.jpg'
    image_file = url_for('static', filename=f'uploads/profile_pics/{img}')
    return render_template('residence_registration.html', form=form, image_file=image_file)


@main.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    prefs = RoommatePreferences.query.filter_by(user_id=current_user.id).first()
    form = PreferenceForm()
    
    if form.validate_on_submit():
        if not prefs:
            prefs = RoommatePreferences(user_id=current_user.id)
            db.session.add(prefs)
        prefs.cleanliness_level = form.cleanliness_level.data
        prefs.noise_tolerance = form.noise_tolerance.data
        prefs.sleep_schedule = form.sleep_schedule.data
        prefs.study_habits = form.study_habits.data
        db.session.commit()
        flash('Preferences Saved!', 'success')
        return redirect(url_for('main.dashboard'))
        
    return render_template('preferences.html', form=form, preferences=prefs)

# --- 4. Housing & Matching ---

@main.route('/housing')
@login_required
def browse_housing():
    listings = HousingListing.query.all()
    return render_template('housing.html', listings=listings)

@main.route('/roommates_matching')
@login_required
def roommates_matching():
    my_prefs = RoommatePreferences.query.filter_by(user_id=current_user.id).first()
    potential_matches = []
    if my_prefs:
        potential_matches = User.query.join(RoommatePreferences).filter(
            User.id != current_user.id,
            RoommatePreferences.cleanliness_level == my_prefs.cleanliness_level
        ).all()
    return render_template('roommates_matching.html', matches=potential_matches)

@main.route('/matches')
@login_required
def matches():
    allocation = Allocation.query.filter_by(user_id=current_user.id).first()
    roommate = None
    roommate_image = None
    
    if allocation:
        r_alloc = Allocation.query.filter(Allocation.listing_id == allocation.listing_id, 
                                          Allocation.room_number == allocation.room_number, 
                                          Allocation.user_id != current_user.id).first()
        if r_alloc: 
            roommate = User.query.get(r_alloc.user_id)
            r_img = roommate.image_file if roommate.image_file else 'default.jpg'
            roommate_image = url_for('static', filename=f'uploads/profile_pics/{r_img}')

    my_img = current_user.image_file if current_user.image_file else 'default.jpg'
    my_image_file = url_for('static', filename=f'uploads/profile_pics/{my_img}')
            
    return render_template('matches.html', 
                            allocation=allocation, 
                            roommate=roommate,
                            roommate_image=roommate_image,
                            my_image_file=my_image_file)

@main.route('/process-allocation/<string:action>', methods=['POST'])
@login_required
def process_allocation(action):
    alloc = Allocation.query.filter_by(user_id=current_user.id).first()
    
    if not alloc:
        flash('No allocation found to process.', 'danger')
        return redirect(url_for('main.dashboard'))

    if action == 'accept':
        alloc.status = 'Accepted'
        db.session.commit()
        flash('You have successfully accepted your room allocation!', 'success')
    
    elif action == 'decline':
        res = HousingListing.query.get(alloc.listing_id)
        if res:
            res.available_rooms += 1
        
        app = RoomApplication.query.filter_by(user_id=current_user.id).first()
        if app:
            app.status = 'Pending'
            
        db.session.delete(alloc)
        db.session.commit()
        flash('Allocation declined. You are back in the waiting list.', 'info')

    return redirect(url_for('main.matches'))

# --- 5. Proof of Residence ---

@main.route('/proof-of-residence')
@main.route('/admin/proof-of-residence/<int:user_id>')
@login_required
def proof_of_residence(user_id=None):
    if user_id and current_user.email == 'studenthousing@dut4life.ac.za':
        target_id = user_id
    else:
        target_id = current_user.id

    alloc = Allocation.query.filter_by(user_id=target_id).first()
    
    if not alloc:
        flash('No allocation found.', 'info')
        return redirect(url_for('main.dashboard'))
        
    return render_template('proof_of_residence.html', 
                           alloc=alloc, 
                           date=datetime.now().strftime('%d %B %Y'))