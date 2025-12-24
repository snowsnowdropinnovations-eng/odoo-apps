import base64
import json

from odoo import http, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request


class TimeOffController(http.Controller):
    @http.route('/all/time/off', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def Retrieve_Time_Off_Data(self, **kwargs):
        all_types = []
        # Use sudo() for portal users or get employee_id from user
        employee_id = request.env.user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', request.env.uid)], limit=1)
        if not employee_id:
            raise ValidationError(_('No employee record found for the current user.'))
        allocated_recs = request.env['hr.leave.allocation'].sudo().search(
            [('employee_id', '=', employee_id.id), ('state', 'in', ['validate', 'validate1'])])
        for x in allocated_recs:
            all_types.append({
                'name': x.holiday_status_id.name,
                'id': x.holiday_status_id.id,
                'no_of_days': x.number_of_days_display,
                'leave_type': x.holiday_status_id.leave_type,

            })
        unpaid_leave_id = request.env['hr.leave.type'].sudo().search([('name', 'ilike', 'Unpaid')], limit=1)
        if any(x['id'] == unpaid_leave_id.id for x in all_types):
            print('Already unpaid leave')
        else:
            all_types.append(
                {'id': unpaid_leave_id.id, 'name': unpaid_leave_id.name, 'leave_type': unpaid_leave_id.leave_type, })
        print(f'Leave: {all_types} ')

        # Use Odoo's standard get_allocation_data method for accurate calculations
        leaves_info = []
        dashboard_leaves_info = []  # Separate list for dashboard cards
        if employee_id:
            # Get all leave types (both requiring and not requiring allocation)
            leave_types = request.env['hr.leave.type'].sudo().search([
                ('active', '=', True)
            ])
            
            for leave_type in leave_types:
                # Use Odoo's standard method to get allocation data
                # This works for both types that require allocation and those that don't
                try:
                    allocation_data = leave_type.sudo().get_allocation_data(employee_id, fields.Date.today())
                except:
                    # If get_allocation_data fails for this type, skip it
                    continue
                
                if employee_id in allocation_data and allocation_data[employee_id]:
                    for lt_info in allocation_data[employee_id]:
                        lt_name, lt_data, requires_allocation, lt_id = lt_info
                        # Get leave_type field value if it exists
                        leave_type_obj = request.env['hr.leave.type'].sudo().browse(lt_id)
                        leave_type_value = getattr(leave_type_obj, 'leave_type', None) or lt_name
                        
                        remaining = round(lt_data.get('virtual_remaining_leaves', 0), 2)
                        allocated = round(lt_data.get('max_leaves', 0), 2)
                        taken = round(lt_data.get('leaves_taken', 0), 2)
                        
                        leave_info_dict = {
                            'Leave_type': leave_type_value,
                            'leave_type_name': lt_name,
                            'leave_type_id': lt_id,
                            'allocated': allocated,
                            'taken': taken,
                            'remaining': remaining,
                            'remaining_class': 'text-danger' if remaining < 0 else 'text-success',
                        }
                        
                        # Add to leaves_info for table (only if has allocation or is relevant)
                        if allocated > 0 or remaining != 0:
                            leaves_info.append(leave_info_dict)
                        
                        # Add to dashboard if it has any data (allocation, taken, or remaining)
                        # Show all leave types that have any activity
                        if allocated > 0 or taken > 0 or abs(remaining) > 0.01:
                            dashboard_leaves_info.append(leave_info_dict)
        
        print('Allocation Information: ', leaves_info)

        env_user = request.env.uid
        time_offs = []
        grouped_data = {}
        today = datetime.now().date()

        # Get filter, sort, and group parameters with "None" as default
        filter_by = kwargs.get('filter_by', '')
        sort_by = kwargs.get('sort_by', '')  # Default to no sort
        group_by = kwargs.get('group_by', 'none')

        if env_user:
            # Base domain for time off records
            domain = [('employee_id.user_id', '=', env_user)]

            # Apply date filter based on filter_by
            if filter_by == 'last_week':
                last_week_start = today - timedelta(days=today.weekday() + 7)
                last_week_end = last_week_start + timedelta(days=6)
                domain.append(('request_date_from', '>=', last_week_start))
                domain.append(('request_date_from', '<=', last_week_end))
            elif filter_by == 'last_month':
                last_month = today.replace(day=1) - timedelta(days=1)
                last_month_start = last_month.replace(day=1)
                domain.append(('request_date_from', '>=', last_month_start))
                domain.append(('request_date_from', '<', today.replace(day=1)))
            elif filter_by == 'last_year':
                last_year_start = today.replace(year=today.year - 1, month=1, day=1)
                last_year_end = today.replace(year=today.year - 1, month=12, day=31)
                domain.append(('request_date_from', '>=', last_year_start))
                domain.append(('request_date_from', '<=', last_year_end))
            # Empty filter_by means no filtering (equivalent to "All")

            # Fetch time off records
            time_off_recs = request.env['hr.leave'].sudo().search(domain)

            # Inside Retrive_Time_Off_Data method, update the time_offs.append block
            if time_off_recs:
                for time in time_off_recs:
                    # Fetch existing attachments
                    attachments = time.medical_attachment_ids
                    attachment_data = []
                    for attachment in attachments:
                        attachment_data.append({
                            'id': attachment.id,
                            'name': attachment.name,
                            'url': f'/web/content/{attachment.id}?download=true',
                        })

                    time_offs.append({
                        'employee_name': time.employee_id.name,
                        'type': time.holiday_status_id.name,
                        'description': time.name,
                        'request_date_from': time.request_date_from.strftime(
                            '%m/%d/%Y ') if time.request_date_from else '',
                        'request_date_to': time.request_date_to.strftime('%m/%d/%Y ') if time.request_date_to else '',
                        'duration': time.duration_display,
                        'id': time.id,
                        'state': time.state,
                        'request_date_from_raw': time.request_date_from,
                        'request_date_to_raw': time.request_date_to,
                        'request_unit_half': time.request_unit_half,
                        'request_date_from_period': time.request_date_from_period,
                        'holiday_status_id': time.holiday_status_id.id,
                        'request_unit_hours': time.request_unit_hours,
                        'request_hour_from': time.request_hour_from,
                        'request_hour_to': time.request_hour_to,
                        'medical_attachments': attachment_data,  # Add attachment data
                    })

            # Sort the records only if sort_by is specified
            if sort_by == 'request_date_from':
                time_offs.sort(key=lambda x: x['request_date_from_raw'] or datetime.min.date(), reverse=True)
            elif sort_by == 'request_date_to':
                time_offs.sort(key=lambda x: x['request_date_to_raw'] or datetime.min.date(), reverse=True)
            elif sort_by == 'duration':
                def duration_to_days(dur):
                    if not dur:
                        return 0
                    if 'days' in dur:
                        return float(dur.split()[0])
                    elif 'hours' in dur:
                        parts = dur.split()[0].split(':')
                        if len(parts) == 2:
                            hours = float(parts[0])
                            minutes = float(parts[1]) / 60
                            total_hours = hours + minutes
                            return total_hours / 8  # Convert hours to days (8-hour workday)
                    return 0

                time_offs.sort(key=lambda x: duration_to_days(x['duration']), reverse=True)

            # Group the records
            if group_by != 'none':
                for time_off in time_offs:
                    key = time_off[group_by] if group_by in time_off else 'Unknown'
                    if key not in grouped_data:
                        grouped_data[key] = []
                    grouped_data[key].append(time_off)
            else:
                grouped_data = {'none': time_offs}

        elif not env_user:
            raise ValidationError(_('Please login to access this page'))

        # Get error from session or URL params
        error_message = kwargs.get('error') or request.session.pop('leave_update_error', None)
        
        return request.render('sd_leave_request_portal.time_off_controller_portal_view_id', {
            'grouped_data': grouped_data,
            'group_by': group_by,
            'filter_by': filter_by,
            'sort_by': sort_by,
            'data': time_offs,
            'all_types': all_types,
            'leaves_info': leaves_info,
            'dashboard_leaves_info': dashboard_leaves_info,  # For dashboard cards
            'error_message': error_message,
        })

    @http.route('/time/off/update/<int:leave_id>', type='http', auth='user', website=True, methods=['GET', 'POST'],
                csrf=True)
    def Update_Time_Off_Data(self, leave_id, **kwargs):
        leave = request.env['hr.leave'].sudo().browse(leave_id).exists()
        if not leave or leave.employee_id.user_id.id != request.env.uid:
            raise ValidationError(_('You do not have permission to update this leave request.'))

        if request.httprequest.method == 'POST':
            description = kwargs.get('description')
            time_off_type = kwargs.get('time_off_type')
            start_date_raw = kwargs.get('start_date')
            end_date_raw = kwargs.get('end_date')
            request_unit_half = kwargs.get('request_unit_half') == 'on'
            request_unit_hours = kwargs.get('request_unit_hours') == 'on'
            half_morning_or_evening = kwargs.get('half_morning_or_evening')
            from_time = kwargs.get('from_time')
            to_time = kwargs.get('to_time')

            # Ensure start_date is always provided for custom hours
            start_date = datetime.strptime(start_date_raw, '%Y-%m-%dT%H:%M') if start_date_raw else None
            if request_unit_hours and not start_date_raw:
                raise ValidationError(_('Start Date is required for custom hours.'))
            end_date = start_date if request_unit_half else (
                datetime.strptime(end_date_raw, '%Y-%m-%dT%H:%M') if end_date_raw else None)

            if leave.state not in ['validate', 'validate1']:
                # Validate inputs for custom hours
                if request_unit_hours and (not from_time or not to_time):
                    raise ValidationError(_('From Time and To Time are required for custom hours.'))

                # Handle Custom Hours
                duration_hours = 0
                if request_unit_hours:
                    try:
                        from_time_dt = datetime.strptime(from_time, '%H:%M')
                        to_time_dt = datetime.strptime(to_time, '%H:%M')
                        if to_time_dt.time() <= from_time_dt.time():
                            raise ValidationError(_('To Time must be after From Time.'))
                        end_date = start_date  # Custom hours use the same start date
                        duration_hours = ((to_time_dt - from_time_dt).total_seconds() / 3600) % 24
                    except ValueError:
                        raise ValidationError(_('Invalid time format. Please use HH:MM format (e.g., 17:04).'))

                # Combine date and time for custom hours
                request_date_from = start_date
                request_date_to = end_date
                if request_unit_hours and from_time and to_time:
                    if not start_date:
                        raise ValidationError(_('Start Date is required for custom hours.'))
                    request_date_from = start_date.replace(hour=from_time_dt.hour, minute=from_time_dt.minute, second=0,
                                                           microsecond=0)
                    request_date_to = start_date.replace(hour=to_time_dt.hour, minute=to_time_dt.minute, second=0,
                                                         microsecond=0)

                def create_attachments(field_name):
                    attachments = []
                    if field_name in request.httprequest.files:
                        files = request.httprequest.files.getlist(field_name)
                        print(f"Files uploaded: {[file.filename for file in files]}")  # Debug
                        for file in files:
                            if file and file.filename:
                                attachment = request.env['ir.attachment'].sudo().create({
                                    'name': file.filename,
                                    'datas': base64.b64encode(file.read()),
                                    'res_model': 'hr.leave',
                                    'res_field': field_name,
                                    'type': 'binary',
                                })
                                attachments.append(attachment.id)
                                print(f"Created attachment ID: {attachment.id}")  # Debug
                    else:
                        print(f"No files found for field: {field_name}")  # Debug
                    return [(6, 0, attachments)] if attachments else [
                        (6, 0, leave.medical_attachment_ids.ids)]  # Retain existing if no new file

                # Get the new leave type to check if it's "Sick"
                new_leave_type = request.env['hr.leave.type'].sudo().browse(int(time_off_type))
                clear_attachments = new_leave_type.leave_type != 'sick'  # Assuming leave_type is the field indicating "sick"

                leave_vals = {
                    'name': description,
                    'holiday_status_id': int(time_off_type),
                    'request_date_from': request_date_from,
                    'request_date_to': request_date_to,
                    'request_unit_half': request_unit_half,
                    'request_date_from_period': half_morning_or_evening if request_unit_half else False,
                    'request_unit_hours': request_unit_hours,
                }

                # Handle attachments based on leave type
                if clear_attachments:
                    leave_vals['medical_attachment_ids'] = [(5,)]  # Clear attachments if not "Sick"
                else:
                    leave_vals['medical_attachment_ids'] = create_attachments('attachment_file')

                if request_unit_hours and from_time and to_time:
                    leave_vals['request_hour_from'] = from_time_dt.hour + from_time_dt.minute / 60.0
                    leave_vals['request_hour_to'] = to_time_dt.hour + to_time_dt.minute / 60.0
                    if 'number_of_hours' in leave._fields:
                        leave_vals['number_of_hours'] = duration_hours

                # Check allocation before updating using Odoo's standard logic
                holiday_status = leave.holiday_status_id
                # If leave type is being changed, get the new one
                if 'holiday_status_id' in leave_vals:
                    holiday_status = request.env['hr.leave.type'].sudo().browse(leave_vals['holiday_status_id'])
                
                if holiday_status and holiday_status.requires_allocation != 'no':
                    # Save original values for rollback
                    original_vals = {}
                    for key in leave_vals.keys():
                        if hasattr(leave, key):
                            original_vals[key] = getattr(leave, key)
                    
                    # Write new values temporarily
                    leave.write(leave_vals)
                    
                    try:
                        # Validate allocation using Odoo's standard method
                        leave._check_validity()
                    except ValidationError as e:
                        # Rollback to original values
                        leave.write(original_vals)
                        error_msg = str(e)
                        # Check if it's an allocation error and show user-friendly message
                        if 'allocation' in error_msg.lower() or 'no valid allocation' in error_msg.lower():
                            error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                        # Store error in session to display on redirect
                        request.session['leave_update_error'] = error_msg
                        return request.redirect(f'/all/time/off?error={error_msg}')
                else:
                    # For leave types that don't require allocation, just update
                    leave.write(leave_vals)
                
                print(f"Leave {leave.id} updated with attachments: {leave.medical_attachment_ids.ids}")  # Debug

            return request.redirect('/all/time/off')

        return request.redirect('/all/time/off')

    @http.route('/time/off/cancel/<int:leave_id>', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def Cancel_Time_Off_Data(self, leave_id, **kwargs):
        leave = request.env['hr.leave'].sudo().browse(leave_id).exists()
        if not leave or leave.employee_id.user_id.id != request.env.uid:
            raise ValidationError(_('You do not have permission to cancel this leave request.'))

        if leave.state not in ['validate']:  # Allow cancellation if not approved
            leave.write({
                'state': 'refuse',
            })
        return request.redirect('/all/time/off')

    @http.route('/create/time/off', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def create_Time_Off_Data(self, **kwargs):
        all_types = []
        # Use sudo() for portal users or get employee_id from user
        employee_id = request.env.user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', request.env.uid)], limit=1)
        if not employee_id:
            return request.render('sd_leave_request_portal.time_off_create_form_template', {
                'all_types': [],
                'allocation_info': {},
                'error': _('No employee record found for the current user.')
            })
        allocated_recs = request.env['hr.leave.allocation'].sudo().search(
            [('employee_id', '=', employee_id.id), ('state', 'in', ['validate', 'validate1'])])
        for x in allocated_recs:
            all_types.append({
                'name': x.holiday_status_id.name,
                'id': x.holiday_status_id.id,
                'type': x.holiday_status_id.leave_type,
            })

        unpaid_leave_id = request.env['hr.leave.type'].sudo().search([('name', 'ilike', 'Unpaid')], limit=1)
        if not any(x['id'] == unpaid_leave_id.id for x in all_types):
            all_types.append(
                {'id': unpaid_leave_id.id, 'name': unpaid_leave_id.name, 'type': unpaid_leave_id.leave_type})
        print(f'Leave: {all_types}')
        
        # Get allocation data for client-side validation
        allocation_info = {}
        if employee_id:
            leave_types = request.env['hr.leave.type'].sudo().search([('active', '=', True)])
            for leave_type in leave_types:
                try:
                    allocation_data = leave_type.sudo().get_allocation_data(employee_id, fields.Date.today())
                    if employee_id in allocation_data and allocation_data[employee_id]:
                        for lt_info in allocation_data[employee_id]:
                            lt_name, lt_data, requires_allocation, lt_id = lt_info
                            if lt_id == leave_type.id:
                                allocation_info[str(lt_id)] = {
                                    'remaining': round(lt_data.get('virtual_remaining_leaves', 0), 2),
                                    'allocated': round(lt_data.get('max_leaves', 0), 2),
                                    'taken': round(lt_data.get('leaves_taken', 0), 2),
                                    'requires_allocation': requires_allocation != 'no',
                                    'allows_negative': leave_type.allows_negative,
                                    'max_allowed_negative': leave_type.max_allowed_negative or 0,
                                }
                                break
                except:
                    continue

        if request.httprequest.method == 'POST':
            # Use sudo() for portal users or get employee_id from user
            employee_id = request.env.user.employee_id or request.env['hr.employee'].sudo().search([('user_id', '=', request.env.uid)], limit=1)
            if not employee_id:
                raise ValidationError(_('No employee record found for the current user.'))

            # Handle date fields with validation
            from_date_str = kwargs.get('from_date')
            to_date_str = kwargs.get('to_date')
            if not from_date_str:
                raise ValidationError(_('From Date is required.'))
            from_date = datetime.strptime(from_date_str, '%Y-%m-%dT%H:%M')
            to_date = datetime.strptime(to_date_str, '%Y-%m-%dT%H:%M') if to_date_str else from_date

            if from_date < datetime.now().replace(hour=0, minute=0, second=0, microsecond=0):
                raise ValidationError(_('Start date cannot be in the past.'))
            if to_date < from_date:
                raise ValidationError(_('End date must be after start date.'))

            request_unit_half = kwargs.get('request_unit_half') == 'on'
            request_unit_hours = kwargs.get('request_unit_hours') == 'on'
            half_morning_or_evening = kwargs.get('half_morning_or_evening')
            from_time = kwargs.get('from_time')
            to_time = kwargs.get('to_time')

            # Handle Half Day
            if request_unit_half:
                to_date = from_date

            # Handle Custom Hours
            if request_unit_hours:
                if not from_time or not to_time:
                    raise ValidationError(_('From Time and To Time are required for custom hours.'))
                try:
                    from_time_dt = datetime.strptime(from_time, '%H:%M')
                    to_time_dt = datetime.strptime(to_time, '%H:%M')
                    if to_time_dt <= from_time_dt:
                        raise ValidationError(_('To Time must be after From Time.'))
                    to_date = from_date  # Same day for custom hours
                    duration_hours = (to_time_dt - from_time_dt).total_seconds() / 3600
                except ValueError:
                    raise ValidationError(_('Invalid time format. Please use HH:MM format.'))

            department = employee_id.department_id.id
            time_off_type = int(kwargs.get('time_off_type'))
            description = kwargs.get('description')

            def create_attachments(field_name):
                attachments = []
                if field_name in request.httprequest.files:
                    files = request.httprequest.files.getlist(field_name)
                    for file in files:
                        if file and file.filename:
                            attachment = request.env['ir.attachment'].sudo().create({
                                'name': file.filename,
                                'datas': base64.b64encode(file.read()),
                                'res_model': 'hr.leave',
                                'res_field': field_name,
                                'type': 'binary',
                            })
                            attachments.append(attachment.id)
                return [(6, 0, attachments)] if attachments else False

            # Combine date and time for custom hours
            request_date_from = from_date
            request_date_to = to_date
            if request_unit_hours and from_time and to_time:
                request_date_from = from_date.replace(hour=from_time_dt.hour, minute=from_time_dt.minute, second=0,
                                                      microsecond=0)
                request_date_to = from_date.replace(hour=to_time_dt.hour, minute=to_time_dt.minute, second=0,
                                                    microsecond=0)

            leave_vals = {
                'employee_id': employee_id.id,
                'department_id': department,
                'name': description,
                'holiday_status_id': time_off_type,
                'request_date_from': request_date_from,
                'request_date_to': request_date_to,
                'medical_attachment_ids': create_attachments('attachment_file'),
                'request_unit_half': request_unit_half,
                'request_date_from_period': half_morning_or_evening if request_unit_half else False,
                'request_unit_hours': request_unit_hours,
            }

            if request_unit_hours and from_time and to_time:
                leave_vals['request_hour_from'] = from_time_dt.hour + from_time_dt.minute / 60.0
                leave_vals['request_hour_to'] = to_time_dt.hour + to_time_dt.minute / 60.0

            # Check allocation before creating using Odoo's standard logic
            holiday_status = request.env['hr.leave.type'].sudo().browse(time_off_type)
            if holiday_status.requires_allocation != 'no':
                # First, check if employee has any allocation for this leave type
                try:
                    allocation_data = holiday_status.sudo().get_allocation_data(employee_id, request_date_from.date())
                except:
                    allocation_data = {}
                
                # Check if employee has allocation
                if employee_id not in allocation_data or not allocation_data[employee_id] or len(allocation_data[employee_id]) == 0:
                    # No allocation found - show warning
                    error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                    return request.render('sd_leave_request_portal.time_off_create_form_template', {
                        'all_types': all_types,
                        'error': error_msg
                    })
                
                # Additional check: verify allocation has valid data
                emp_allocation_data = allocation_data[employee_id]
                has_valid_allocation = False
                for lt_info in emp_allocation_data:
                    lt_name, lt_data, requires_allocation, lt_id = lt_info
                    if lt_id == holiday_status.id:  # Match the selected leave type
                        max_leaves = lt_data.get('max_leaves', 0)
                        if max_leaves > 0:  # Has some allocation
                            has_valid_allocation = True
                            break
                
                if not has_valid_allocation:
                    # No valid allocation found for this specific leave type
                    error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                    return request.render('sd_leave_request_portal.time_off_create_form_template', {
                        'all_types': all_types,
                        'error': error_msg
                    })
                
                # Check if there's remaining leave available
                emp_allocation_data = allocation_data[employee_id]
                if emp_allocation_data:
                    # Find the allocation info for this specific leave type
                    lt_info = None
                    for info in emp_allocation_data:
                        lt_name, lt_data, requires_allocation, lt_id = info
                        if lt_id == holiday_status.id:  # Match the selected leave type
                            lt_info = info
                            break
                    
                    if not lt_info:
                        # No matching leave type found in allocation data
                        error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                        return request.render('sd_leave_request_portal.time_off_create_form_template', {
                            'all_types': all_types,
                            'error': error_msg
                        })
                    
                    lt_name, lt_data, requires_allocation, lt_id = lt_info
                    virtual_remaining = lt_data.get('virtual_remaining_leaves', 0)
                    
                    # Calculate requested days
                    if request_unit_half:
                        requested_days = 0.5
                    elif request_unit_hours and from_time and to_time:
                        requested_days = duration_hours / 8.0  # Convert hours to days
                    else:
                        # Calculate days from date range
                        delta = request_date_to.date() - request_date_from.date()
                        requested_days = delta.days + 1
                    
                    # Check if remaining is sufficient (considering allows_negative)
                    if not holiday_status.allows_negative:
                        # If negative not allowed, check if remaining is enough
                        if virtual_remaining < requested_days:
                            error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                            return request.render('sd_leave_request_portal.time_off_create_form_template', {
                                'all_types': all_types,
                                'error': error_msg
                            })
                    else:
                        # If negative allowed, check max allowed negative
                        max_excess = holiday_status.max_allowed_negative or 0
                        if virtual_remaining < (requested_days - max_excess):
                            error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                            return request.render('sd_leave_request_portal.time_off_create_form_template', {
                                'all_types': all_types,
                                'error': error_msg
                            })
                
                # Create the record and validate using Odoo's standard method
                leave_record = request.env['hr.leave'].sudo().create(leave_vals)
                try:
                    # Double-check with Odoo's validation
                    leave_record.sudo()._check_validity()
                except ValidationError as e:
                    # If validation fails, delete the record and show error
                    leave_record.unlink()
                    error_msg = str(e)
                    # Check if it's an allocation error and show user-friendly message
                    if 'allocation' in error_msg.lower() or 'no valid allocation' in error_msg.lower() or 'not have' in error_msg.lower():
                        error_msg = _("You do not have enough leave allocation. Please check your leave allocation.")
                    return request.render('sd_leave_request_portal.time_off_create_form_template', {
                        'all_types': all_types,
                        'error': error_msg
                    })
            else:
                # For leave types that don't require allocation, just create
                leave_record = request.env['hr.leave'].sudo().create(leave_vals)

            return request.redirect('/all/time/off')

        return request.render('sd_leave_request_portal.time_off_create_form_template', {
            'all_types': all_types,
            'allocation_info': allocation_info,
        })
