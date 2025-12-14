import base64
from odoo import http, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import request


class FetcherUserWise_Attendance_Records(http.Controller):
    @http.route(['/fetch/attendance', '/fetch/attendance/page/<int:page>'], type='http', auth='user', website=True,
                methods=['GET'], csrf=False)
    def fetch_attendance(self, page=1, **kwargs):
        user_id = request.env.user.employee_id.id
        attendance_data = []
        check_in = False
        check_out = False
        filter_by = False
        leave_count_list = 0
        worked_hours = 0
        today = datetime.now().date()

        # Base domain for all queries
        domain = [('employee_id', '=', user_id)]

        # Handle check_in and check_out parameters
        check_in_param = kwargs.get('check_in', '')
        check_out_param = kwargs.get('check_out', '')

        # Convert 'False' string to False, and ensure valid date string
        if check_in_param and check_in_param != 'False':
            check_in = check_in_param
        if check_out_param and check_out_param != 'False':
            check_out = check_out_param

        # Check if filter_by is provided
        if kwargs.get('filter_by', ''):
            filter_by = kwargs.get('filter_by', '')

        # If no filters are applied, return empty dataset
        if not (check_in and check_out) and not filter_by:
            return request.render('sd_attendance_portal.attendance_history_fetcher_id',
                                  {
                                      'attendance_data': [],
                                      'leave_count': 0,
                                      'search_done': False,
                                      'pager': {},
                                      'total_records': 0,
                                      'worked_hours': 0,
                                  })

        # Apply filters if provided
        if filter_by:
            if filter_by == 'last_week':
                last_week_start = today - timedelta(days=today.weekday() + 7)
                last_week_end = last_week_start + timedelta(days=6)
                domain.append(('check_in', '>=', last_week_start))
                domain.append(('check_out', '<=', last_week_end))
            elif filter_by == 'last_month':
                last_month = today.replace(day=1) - timedelta(days=1)
                last_month_start = last_month.replace(day=1)
                domain.append(('check_in', '>=', last_month_start))
                domain.append(('check_out', '<', today.replace(day=1)))
            elif filter_by == 'last_year':
                last_year_start = today.replace(year=today.year - 1, month=1, day=1)
                last_year_end = today.replace(year=today.year - 1, month=12, day=31)
                domain.append(('check_in', '>=', last_year_start))
                domain.append(('check_out', '<=', last_year_end))

        if check_in and check_out:
            if not check_in or not check_out:
                raise ValidationError('Both Check In and Check Out are required.')

            if check_in > check_out:
                raise ValidationError('Check Out Must Be Greater Than Check In')

            if datetime.strptime(check_in, '%Y-%m-%d').date() > today:
                raise ValidationError(_('Selected Date cannot be in future.'))

            if user_id:
                domain.append(('check_in', '>=', check_in))
                domain.append(('check_out', '<=', check_out))

                # Calculate leave count
                leave_ids = request.env['hr.leave'].search([
                    ('employee_id', '=', user_id),
                    ('request_date_from', '>=', check_in),
                    ('request_date_from', '<=', check_out),
                    ('state', '=', 'validate'),
                ]).mapped('duration_display')
                leave_count_list = []
                for x in leave_ids:
                    sp = x.split(' ')
                    leave_count_list.append(int(sp[0]))
                leave_count_list = sum(x for x in leave_count_list)

        # Get total count for pagination + Worked hours
        attendance_count = request.env['hr.attendance'].search_count(domain)
        attendance_recs = request.env['hr.attendance'].search(domain)
        attendance_worked_hours = [x.worked_hours for x in attendance_recs]
        worked_hours = sum(attendance_worked_hours)

        # Setup pager with proper handling of False values
        pager = request.website.pager(
            url="/fetch/attendance",
            url_args={
                'check_in': check_in if check_in else None,
                'check_out': check_out if check_out else None,
                'filter_by': filter_by if filter_by else None,
            },
            total=attendance_count,
            page=page,
            step=10  # Records per page
        )

        # Get paginated records
        attendance_recs = request.env['hr.attendance'].search(
            domain,
            limit=10,
            offset=pager['offset'],
            order='check_in desc'
        )

        for rec in attendance_recs:
            attendance_data.append({
                'check_in': rec.check_in,
                'check_out': rec.check_out,
                'worked_hours': rec.worked_hours,
                'validated_overtime_hours': rec.validated_overtime_hours,
            })

        return request.render('sd_attendance_portal.attendance_history_fetcher_id',
                              {
                                  'attendance_data': attendance_data,
                                  'leave_count': leave_count_list,
                                  'search_done': bool(check_in or check_out or filter_by),
                                  'pager': pager,
                                  'total_records': attendance_count,
                                  'worked_hours': worked_hours,
                              })
