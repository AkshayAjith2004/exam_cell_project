import re
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from departments.models import Branch
from .models import Student
from accounts.views import role_required

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER', 'TEACHER'])
def student_list(request):
    query = request.GET.get('q', '').strip()
    selected_branch = request.GET.get('branch', '').strip()
    selected_sem = request.GET.get('sem', '').strip()
    selected_batch = request.GET.get('batch', '').strip().upper()

    students_query = Student.objects.select_related('user', 'branch', 'branch__department').all()
    
    if query:
        # Support search patterns like 's3', 's4', 'sem 3', 'sem4', 'semester 4', etc.
        sem_match = re.match(r'^(?:s|sem|semester)[-_\s]*(\d+)$', query, re.IGNORECASE)
        if sem_match:
            searched_sem = int(sem_match.group(1))
            q_filter = (
                Q(semester=searched_sem) |
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(admission_number__icontains=query) |
                Q(registration_number__icontains=query) |
                Q(branch__code__icontains=query)
            )
        else:
            q_filter = (
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(admission_number__icontains=query) |
                Q(registration_number__icontains=query) |
                Q(branch__code__icontains=query) |
                Q(branch__name__icontains=query)
            )
        students_query = students_query.filter(q_filter)

    if selected_branch:
        students_query = students_query.filter(branch__id=selected_branch)
    if selected_sem:
        students_query = students_query.filter(semester=selected_sem)

    # Sort Batch A students and Batch B students separately so Batch B roll numbers start from 1
    batch_a_students = list(students_query.filter(batch='A').order_by('registration_number', 'admission_number'))
    for idx, s in enumerate(batch_a_students, start=1):
        s.batch_roll_no = idx

    batch_b_students = list(students_query.filter(batch='B').order_by('registration_number', 'admission_number'))
    for idx, s in enumerate(batch_b_students, start=1):
        s.batch_roll_no = idx

    no_batch_students = list(students_query.filter(batch__isnull=True).order_by('registration_number', 'admission_number'))
    for idx, s in enumerate(no_batch_students, start=1):
        s.batch_roll_no = idx

    if selected_batch == 'A':
        all_students_list = batch_a_students
    elif selected_batch == 'B':
        all_students_list = batch_b_students
    elif selected_batch == 'NONE':
        all_students_list = no_batch_students
    else:
        all_students_list = batch_a_students + batch_b_students + no_batch_students

    per_page = request.GET.get('per_page', '50')
    try:
        per_page_int = int(per_page)
    except ValueError:
        per_page_int = 50
        
    paginator = Paginator(all_students_list, per_page_int)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    branches = Branch.objects.select_related('department').all()
    
    return render(request, 'students/student_list.html', {
        'page_obj': page_obj,
        'branches': branches,
        'query': query,
        'selected_branch': selected_branch,
        'selected_sem': selected_sem,
        'selected_batch': selected_batch,
        'semester_choices': range(1, 9)
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def student_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        admission_number = request.POST.get('admission_number')
        registration_number = request.POST.get('registration_number', '').strip()
        branch_id = request.POST.get('branch')
        semester = request.POST.get('semester')
        batch_input = request.POST.get('batch', '').strip().upper()
        batch = batch_input if batch_input in ['A', 'B'] else None
        phone = request.POST.get('phone')
        photo = request.FILES.get('photo')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
        elif Student.objects.filter(admission_number=admission_number).exists():
            messages.error(request, f"Admission number '{admission_number}' already exists.")
        else:
            try:
                # 1. Create Django User
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # 2. Set profile role
                profile = user.profile
                profile.role = 'STUDENT'
                profile.save()
                
                # 3. Create Student profile
                branch = Branch.objects.get(id=branch_id)
                Student.objects.create(
                    user=user,
                    admission_number=admission_number,
                    registration_number=registration_number or None,
                    branch=branch,
                    semester=int(semester),
                    batch=batch,
                    phone=phone,
                    photo=photo
                )
                messages.success(request, f"Student '{first_name} {last_name}' registered successfully.")
            except Exception as e:
                messages.error(request, f"Error registering student: {str(e)}")
                
    return redirect('student_list')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    if request.method == 'POST':
        new_admission_no = request.POST.get('admission_number', '').strip()
        if new_admission_no and new_admission_no != student.admission_number:
            if Student.objects.filter(admission_number=new_admission_no).exclude(pk=student.pk).exists():
                messages.error(request, f"Admission number '{new_admission_no}' is already used by another student.")
                branches = Branch.objects.all()
                return render(request, 'students/student_edit.html', {
                    'student': student,
                    'branches': branches,
                    'semester_choices': range(1, 9)
                })
            student.admission_number = new_admission_no

        student.user.first_name = request.POST.get('first_name')
        student.user.last_name = request.POST.get('last_name')
        student.user.email = request.POST.get('email')
        student.user.save()
        
        branch_id = request.POST.get('branch')
        student.branch = Branch.objects.get(id=branch_id)
        student.semester = int(request.POST.get('semester'))
        batch_input = request.POST.get('batch', '').strip().upper()
        student.batch = batch_input if batch_input in ['A', 'B'] else None
        student.phone = request.POST.get('phone')
        student.registration_number = request.POST.get('registration_number', '').strip() or None
        
        if request.FILES.get('photo'):
            student.photo = request.FILES.get('photo')
            
        student.save()
        messages.success(request, "Student details updated successfully.")
        return redirect('student_list')
        
    branches = Branch.objects.all()
    return render(request, 'students/student_edit.html', {
        'student': student,
        'branches': branches,
        'semester_choices': range(1, 9)
    })

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    user = student.user
    user.delete() # cascades to student profile
    messages.success(request, "Student record deleted successfully.")
    return redirect('student_list')

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def student_sample_template(request):
    import csv
    from django.http import HttpResponse
    template_fmt = request.GET.get('format', 'simple')
    
    response = HttpResponse(content_type='text/csv')
    if template_fmt == 'full':
        response['Content-Disposition'] = 'attachment; filename="student_upload_template_full.csv"'
        writer = csv.writer(response)
        writer.writerow(['Roll No', 'Register Number', 'Name', 'Batch'])
        writer.writerow(['1', 'PJR25CS002', 'ABHINAV P', 'A'])
        writer.writerow(['2', 'PJR25CS004', 'ABHISHEK K ANEESH', 'A'])
        writer.writerow(['3', 'PJR25CS005', 'ADHI KRISHNA P M', 'B'])
        writer.writerow(['4', 'PJR25CS006', 'ADHILA KABEER', 'B'])
    else:
        response['Content-Disposition'] = 'attachment; filename="student_upload_template_roll_name.csv"'
        writer = csv.writer(response)
        writer.writerow(['Roll No', 'Name'])
        writer.writerow(['1', 'ABHISHEK KRISHNAN S S'])
        writer.writerow(['2', 'ABIN VARGHESE'])
        writer.writerow(['3', 'ADITHYAN T PRAVEEN'])
        writer.writerow(['4', 'ADITHYAN K P'])
    
    return response

@login_required
@role_required(['ADMIN', 'EXAM_CONTROLLER'])
def student_bulk_upload(request):
    import csv
    import io
    import re
    import openpyxl
    
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        filename = file.name.lower()

        default_branch_id = request.POST.get('default_branch')
        default_semester_val = request.POST.get('default_semester')
        default_batch_input = request.POST.get('batch', '').strip().upper()

        default_branch = None
        if default_branch_id:
            try:
                default_branch = Branch.objects.get(id=default_branch_id)
            except Branch.DoesNotExist:
                default_branch = None

        default_semester = int(default_semester_val) if (default_semester_val and default_semester_val.isdigit()) else 1

        all_branches = list(Branch.objects.select_related('department').all())
        if not all_branches and not default_branch:
            from departments.models import Department
            dept, _ = Department.objects.get_or_create(code='CS', defaults={'name': 'Computer Science & Engineering'})
            default_branch, _ = Branch.objects.get_or_create(code='CS', defaults={'name': 'Computer Science', 'department': dept})
            all_branches = [default_branch]
        elif not default_branch and all_branches:
            default_branch = all_branches[0]

        rows_data = []
        try:
            if filename.endswith('.csv'):
                decoded_file = file.read().decode('utf-8-sig', errors='ignore')
                io_string = io.StringIO(decoded_file)
                reader = csv.reader(io_string)
                
                header = None
                current_section_batch = None
                for r in reader:
                    if not r or not any(r):
                        continue
                    
                    r_raw_str = ' '.join([str(c).upper() for c in r if c is not None])
                    if 'BATCH B' in r_raw_str or 'SECTION B' in r_raw_str or 'SEC B' in r_raw_str:
                        current_section_batch = 'B'
                        header = None
                        continue
                    elif 'BATCH A' in r_raw_str or 'SECTION A' in r_raw_str or 'SEC A' in r_raw_str:
                        current_section_batch = 'A'
                        header = None
                        continue

                    r_norm = [re.sub(r'[^a-z0-9]', '', str(c).strip().lower()) for c in r]
                    if not header:
                        if any(k in r_norm for k in ['registernumber', 'registerno', 'regno', 'rollno', 'roll', 'name', 'studentname']):
                            header = r_norm
                            continue
                    if header:
                        row_cells = [str(c).strip() for c in r]
                        row_dict = dict(zip(header, row_cells))
                        if current_section_batch:
                            row_dict['_section_batch'] = current_section_batch
                        rows_data.append(row_dict)
                    
            elif filename.endswith('.xls'):
                import xlrd
                file_bytes = file.read()
                wb = xlrd.open_workbook(file_contents=file_bytes)
                for sheet in wb.sheets():
                    s_title = sheet.name.upper()
                    sheet_batch_hint = None
                    if 'BATCH B' in s_title or s_title.endswith(' B') or s_title == 'B' or 'SEC B' in s_title:
                        sheet_batch_hint = 'B'
                    elif 'BATCH A' in s_title or s_title.endswith(' A') or s_title == 'A' or 'SEC A' in s_title:
                        sheet_batch_hint = 'A'

                    header = None
                    current_section_batch = sheet_batch_hint
                    for row_idx in range(sheet.nrows):
                        r = sheet.row_values(row_idx)
                        if not r or not any(r):
                            continue
                        
                        r_raw_str = ' '.join([str(c).upper() for c in r if c is not None])
                        if 'BATCH B' in r_raw_str or 'SECTION B' in r_raw_str or 'SEC B' in r_raw_str:
                            current_section_batch = 'B'
                            header = None
                            continue
                        elif 'BATCH A' in r_raw_str or 'SECTION A' in r_raw_str or 'SEC A' in r_raw_str:
                            current_section_batch = 'A'
                            header = None
                            continue

                        r_norm = [re.sub(r'[^a-z0-9]', '', str(c).strip().lower()) if c is not None else '' for c in r]
                        if not header:
                            if any(k in r_norm for k in ['registernumber', 'registerno', 'regno', 'rollno', 'roll', 'name', 'studentname']):
                                header = r_norm
                                continue
                        if header:
                            row_cells = [str(c).strip() if c is not None else '' for c in r]
                            row_dict = dict(zip(header, row_cells))
                            if sheet_batch_hint:
                                row_dict['_sheet_batch'] = sheet_batch_hint
                            if current_section_batch:
                                row_dict['_section_batch'] = current_section_batch
                            rows_data.append(row_dict)

            elif any(filename.endswith(ext) for ext in ['.xlsx', '.xlsm', '.xltx', '.xltm']):
                wb = openpyxl.load_workbook(file, data_only=True)
                for sheet in wb.worksheets:
                    s_title = sheet.title.upper()
                    sheet_batch_hint = None
                    if 'BATCH B' in s_title or s_title.endswith(' B') or s_title == 'B' or 'SEC B' in s_title:
                        sheet_batch_hint = 'B'
                    elif 'BATCH A' in s_title or s_title.endswith(' A') or s_title == 'A' or 'SEC A' in s_title:
                        sheet_batch_hint = 'A'

                    header = None
                    current_section_batch = sheet_batch_hint
                    for r in sheet.iter_rows(values_only=True):
                        if not r or not any(r):
                            continue
                        
                        r_raw_str = ' '.join([str(c).upper() for c in r if c is not None])
                        if 'BATCH B' in r_raw_str or 'SECTION B' in r_raw_str or 'SEC B' in r_raw_str:
                            current_section_batch = 'B'
                            header = None
                            continue
                        elif 'BATCH A' in r_raw_str or 'SECTION A' in r_raw_str or 'SEC A' in r_raw_str:
                            current_section_batch = 'A'
                            header = None
                            continue

                        r_norm = [re.sub(r'[^a-z0-9]', '', str(c).strip().lower()) if c is not None else '' for c in r]
                        if not header:
                            if any(k in r_norm for k in ['registernumber', 'registerno', 'regno', 'rollno', 'roll', 'name', 'studentname']):
                                header = r_norm
                                continue
                        if header:
                            row_cells = [str(c).strip() if c is not None else '' for c in r]
                            row_dict = dict(zip(header, row_cells))
                            if sheet_batch_hint:
                                row_dict['_sheet_batch'] = sheet_batch_hint
                            if current_section_batch:
                                row_dict['_section_batch'] = current_section_batch
                            rows_data.append(row_dict)
            else:
                messages.error(request, "Unsupported file format. Please upload an Excel workbook (.xlsx, .xls, .xlsm) or .csv file.")
                return redirect('student_list')
        except Exception as e:
            messages.error(request, f"Failed to read file: {str(e)}")
            return redirect('student_list')

        created_count = 0
        updated_count = 0
        skipped_count = 0
        error_logs = []

        def find_value(row, keys):
            for k in keys:
                for rk, rv in row.items():
                    if rv and (rk == k or k in rk):
                        return rv
            return ''

        def resolve_branch(branch_str, reg_no=''):
            if default_branch and not branch_str:
                return default_branch

            if reg_no and not branch_str:
                reg_upper = reg_no.upper()
                if 'CS' in reg_upper:
                    cs_b = next((b for b in all_branches if b.code == 'CS'), None)
                    if cs_b: return cs_b
                elif 'EC' in reg_upper:
                    ec_b = next((b for b in all_branches if b.code == 'EC'), None)
                    if ec_b: return ec_b
                elif 'BCA' in reg_upper:
                    bca_b = next((b for b in all_branches if b.code == 'BCA'), None)
                    if bca_b: return bca_b
                elif 'MCA' in reg_upper:
                    mca_b = next((b for b in all_branches if b.code == 'MCA'), None)
                    if mca_b: return mca_b

            if not branch_str:
                return default_branch or all_branches[0]

            b_clean = re.sub(r'[^a-z0-9]', '', branch_str.lower())
            
            for br in all_branches:
                code_norm = re.sub(r'[^a-z0-9]', '', br.code.lower())
                name_norm = re.sub(r'[^a-z0-9]', '', br.name.lower())
                dept_code_norm = re.sub(r'[^a-z0-9]', '', br.department.code.lower()) if br.department else ''
                
                if b_clean == code_norm or b_clean == name_norm or b_clean == dept_code_norm:
                    return br
                    
            aliases = {
                'bca': 'BCA',
                'mca': 'MCA',
                'cs': 'CS', 'cse': 'CS', 'computerscience': 'CS', 'comp': 'CS',
                'ec': 'EC', 'ece': 'EC', 'electronics': 'EC',
                'eee': 'EEE', 'ee': 'EEE',
                'me': 'ME', 'mechanical': 'ME',
                'ce': 'CE', 'civil': 'CE'
            }
            mapped_code = aliases.get(b_clean)
            if mapped_code:
                for br in all_branches:
                    if br.code.upper() == mapped_code:
                        return br
                        
            for br in all_branches:
                code_norm = re.sub(r'[^a-z0-9]', '', br.code.lower())
                if code_norm in b_clean or b_clean in code_norm:
                    return br
                    
            code_upper = branch_str.strip().upper()[:10]
            dept = all_branches[0].department if all_branches else None
            new_b, _ = Branch.objects.get_or_create(code=code_upper, defaults={'name': branch_str, 'department': dept})
            all_branches.append(new_b)
            return new_b

        current_auto_batch = 'A'
        prev_roll_num = None

        for idx, row in enumerate(rows_data, start=1):
            roll_no = find_value(row, ['rollno', 'roll', 'slno', 'sno', 'number', 'no'])
            reg_no = find_value(row, ['registernumber', 'registerno', 'regno', 'regnumber', 'registrationnumber', 'registrationno', 'univregno'])
            name = find_value(row, ['name', 'studentname', 'fullname', 'candidatename', 'firstname'])
            branch_str = find_value(row, ['branchcode', 'branch', 'department', 'dept', 'course', 'stream'])
            sem_str = find_value(row, ['semester', 'sem', 'year', 'term'])
            batch_row_str = find_value(row, ['batch', 'section', 'sec', 'group', 'grp']).upper()
            row_sheet_batch = row.get('_sheet_batch')
            row_section_batch = row.get('_section_batch')

            if not reg_no and not name:
                continue

            roll_num_int = None
            if roll_no and str(roll_no).isdigit():
                roll_num_int = int(roll_no)
            elif reg_no:
                digits = re.findall(r'\d+', reg_no)
                if digits:
                    roll_num_int = int(digits[-1])

            # Detect roll number restart (e.g. Roll 1-40 Batch A, then Roll 1-35 Batch B)
            if roll_num_int is not None:
                if prev_roll_num is not None and prev_roll_num >= 10 and roll_num_int <= 5:
                    current_auto_batch = 'B'
                prev_roll_num = roll_num_int

            if default_batch_input in ['A', 'B']:
                row_batch = default_batch_input
            elif 'A' in batch_row_str or batch_row_str == 'A':
                row_batch = 'A'
            elif 'B' in batch_row_str or batch_row_str == 'B':
                row_batch = 'B'
            elif row_section_batch:
                row_batch = row_section_batch
            elif row_sheet_batch:
                row_batch = row_sheet_batch
            elif default_batch_input == 'SPLIT_40':
                num_to_check = roll_num_int if roll_num_int is not None else idx
                row_batch = 'A' if num_to_check <= 40 else 'B'
            elif default_batch_input == 'AUTO':
                # Auto-Detect mode
                if roll_num_int is not None and roll_num_int > 40 and current_auto_batch == 'A':
                    row_batch = 'B'
                else:
                    row_batch = current_auto_batch
            else:
                # Optional / No Batch mode
                row_batch = None

            branch = resolve_branch(branch_str, reg_no)

            sem_match = re.search(r'\d+', sem_str)
            if sem_match:
                semester = int(sem_match.group())
            else:
                semester = default_semester

            if reg_no:
                admission_no = reg_no
            else:
                r_num_str = f"R{roll_no}" if roll_no else f"ADM{idx:03d}"
                if row_batch:
                    admission_no = f"{branch.code}_S{semester}_{row_batch}_{r_num_str}"
                else:
                    admission_no = f"{branch.code}_S{semester}_{r_num_str}"

            full_name = name.strip().upper() if name else f"STUDENT {admission_no}"

            email = f"{admission_no.lower()}@student.college.edu"
            username_clean = re.sub(r'[^a-zA-Z0-9_]', '_', admission_no.lower())

            existing_student = Student.objects.filter(admission_number=admission_no).first()
            if not existing_student and reg_no:
                existing_student = Student.objects.filter(registration_number=reg_no).first()
            if not existing_student and not reg_no:
                existing_student = Student.objects.filter(
                    branch=branch,
                    semester=semester,
                    batch=row_batch,
                    user__first_name__iexact=full_name
                ).first()

            if existing_student:
                existing_student.registration_number = reg_no or existing_student.registration_number
                existing_student.branch = branch
                existing_student.semester = semester
                existing_student.batch = row_batch
                existing_student.save()

                existing_student.user.first_name = full_name
                existing_student.user.last_name = ''
                existing_student.user.save()
                updated_count += 1
                continue

            try:
                user = User.objects.filter(username=username_clean).first()
                if not user:
                    user = User.objects.create_user(
                        username=username_clean,
                        email=email,
                        password=admission_no,
                        first_name=full_name,
                        last_name=''
                    )
                    user.profile.role = 'STUDENT'
                    user.profile.save()

                Student.objects.create(
                    user=user,
                    admission_number=admission_no,
                    registration_number=reg_no or None,
                    branch=branch,
                    semester=semester,
                    batch=row_batch,
                    phone='N/A'
                )
                created_count += 1
            except Exception as e:
                skipped_count += 1
                error_logs.append(f"Row {idx} ({admission_no}): {str(e)}")

        msg_parts = []
        if created_count > 0:
            msg_parts.append(f"Imported {created_count} new student(s).")
        if updated_count > 0:
            msg_parts.append(f"Updated {updated_count} existing student(s).")
        if msg_parts:
            messages.success(request, " ".join(msg_parts))
            
        if skipped_count > 0:
            err_summary = f"Skipped {skipped_count} row(s). " + " ".join(error_logs[:3])
            messages.warning(request, err_summary)

    return redirect('student_list')




