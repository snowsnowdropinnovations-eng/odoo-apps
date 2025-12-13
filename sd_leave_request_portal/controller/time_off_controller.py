import base64

from odoo import http, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request


class TimeOffController(http.Controller):
    @http.route('/all/time/off', type='http', auth='user', website=True, methods=['GET', 'POST'], csrf=True)
    def Retrieve_Time_Off_Data(self, **kwargs):
        all_types = []
        employee_id = request.env['hr.employee'].search([('user_id', '=', request.env.uid)], limit=1)
        allocated_recs = request.env['hr.leave.allocation'].search(
            [('employee_id', '=', employee_id.id), ('state', 'in', ['validate', 'validate1'])])
        for x in allocated_recs:
            all_types.append({
                'name': x.holiday_status_id.name,
                'id': x.holiday_status_id.id,
                'no_of_days': x.number_of_days_display,
                'leave_type': x.holiday_status_id.leave_type,

            })
        unpaid_leave_id = request.env['hr.leave.type'].search([('name', 'ilike', 'Unpaid')], limit=1)
        if any(x['id'] == unpaid_leave_id.id for x in all_types):
            print('Already unpaid leave')
        else:
            all_types.append(
                {'id': unpaid_leave_id.id, 'name': unpaid_leave_id.name, 'leave_type': unpaid_leave_id.leave_type, })
        print(f'Leave: {all_types} ')

        # allocated and remaining and taken working here:------------------------------:---------------------------------------:
        leave_summary = {}

        for rec in allocated_recs:
            leave_type = rec.holiday_status_id.leave_type
            allocated_days = float(rec.number_of_days_display)
            if leave_type not in leave_summary:
                leave_summary[leave_type] = {'allocated': 0, 'taken': 0}
            leave_summary[leave_type]['allocated'] += allocated_days

        taken_leave_recs = request.env['hr.leave'].sudo().search(
            [('employee_id', '=', employee_id.id), ('state', 'in', ['validate', 'validate1'])]
        )
        for rec in taken_leave_recs:
            leave_type = rec.holiday_status_id.leave_type
            duration_str = rec.duration_display
            # Extract numeric value from duration_display (e.g., "8:00 hours" -> 8.0, "1 days" -> 1.0)
            if 'hours' in duration_str.lower():
                taken_value = float(duration_str.split(':')[0])
            else:
                taken_value = float(duration_str.split()[0])
            # Convert to days if request_unit is 'hour'
            taken_days = (
                taken_value / 8
                if rec.holiday_status_id.request_unit == 'hour'
                else taken_value
            )
            if leave_type not in leave_summary:
                leave_summary[leave_type] = {'allocated': 0, 'taken': 0}
            leave_summary[leave_type]['taken'] += taken_days

        leaves_info = [
            {'Leave_type': leave_type, 'allocated': data['allocated'], 'taken': data['taken']}
            for leave_type, data in leave_summary.items()
        ]
        print('Information: ', leaves_info)

        # Ended Here ------------------------------------------------------------------- : ------------------------------------:

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
            time_off_recs = request.env['hr.leave'].search(domain)

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

        return request.render('sd_leave_request_portal.time_off_controller_portal_view_id', {
            'grouped_data': grouped_data,
            'group_by': group_by,
            'filter_by': filter_by,
            'sort_by': sort_by,
            'data': time_offs,
            'all_types': all_types,
            'leaves_info': leaves_info,
        })

    @http.route('/time/off/update/<int:leave_id>', type='http', auth='user', website=True, methods=['GET', 'POST'],
                csrf=True)
    def Update_Time_Off_Data(self, leave_id, **kwargs):
        leave = request.env['hr.leave'].browse(leave_id).exists()
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
                new_leave_type = request.env['hr.leave.type'].browse(int(time_off_type))
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

                leave.write(leave_vals)
                print(f"Leave {leave.id} updated with attachments: {leave.medical_attachment_ids.ids}")  # Debug

            return request.redirect('/all/time/off')

        return request.redirect('/all/time/off')

    @http.route('/time/off/cancel/<int:leave_id>', type='http', auth='user', website=True, methods=['POST'], csrf=True)
    def Cancel_Time_Off_Data(self, leave_id, **kwargs):
        leave = request.env['hr.leave'].browse(leave_id).exists()
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
        employee_id = request.env['hr.employee'].search([('user_id', '=', request.env.uid)], limit=1)
        allocated_recs = request.env['hr.leave.allocation'].search(
            [('employee_id', '=', employee_id.id), ('state', 'in', ['validate', 'validate1'])])
        for x in allocated_recs:
            all_types.append({
                'name': x.holiday_status_id.name,
                'id': x.holiday_status_id.id,
                'type': x.holiday_status_id.leave_type,
            })

        unpaid_leave_id = request.env['hr.leave.type'].search([('name', 'ilike', 'Unpaid')], limit=1)
        if not any(x['id'] == unpaid_leave_id.id for x in all_types):
            all_types.append(
                {'id': unpaid_leave_id.id, 'name': unpaid_leave_id.name, 'type': unpaid_leave_id.leave_type})
        print(f'Leave: {all_types}')

        if request.httprequest.method == 'POST':
            employee_id = request.env['hr.employee'].search([('user_id', '=', request.env.uid)], limit=1)
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

            request.env['hr.leave'].create(leave_vals)

            return request.redirect('/all/time/off')

        return request.render('sd_leave_request_portal.time_off_create_form_template', {'all_types': all_types})
