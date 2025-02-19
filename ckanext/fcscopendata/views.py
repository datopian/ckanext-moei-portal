import ckan.model as model
from ckan.common import _, g, request
import ckan.plugins.toolkit as tk
from ckan.views.api import _finish_ok
from ckan.views.dataset import GroupView
from ckanext.fcscopendata.models.data_request import DataRequest
from ckanext.fcscopendata.models.analytics import Analytics
import csv
from io import StringIO, BytesIO
from flask import Response
from ckan.lib.helpers import helper_functions as h, Page
import logging
from openpyxl import Workbook
from datetime import datetime
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def vocab_tag_autocomplete():
    q = request.args.get(u'incomplete', u'')
    context = {u'model': model, u'session': model.Session,
                   u'user': g.user, u'auth_user_obj': g.userobj}

    limit = request.args.get(u'limit', 10)
    vocab_list = tk.get_action(u'vocabulary_list')(context, {})

    tag_list = []
    if q:
        data_dict = {u'q': q, u'limit': limit}

        for vocab in vocab_list:
            tags = tk.get_action(u'tag_autocomplete')(context, 
                {**data_dict,'vocabulary_id': vocab['id'] })
            for tag_item in tags:
                tag_list.append(tag_item) 
            
    resultSet = {
        u'ResultSet': {
            u'Result': [{u'Name': tag} for tag in tag_list]
        }
    }

    return _finish_ok(resultSet)

class GroupManage(GroupView):
    def post(self, package_type, id):
        context, pkg_dict = self._prepare(id)
        new_group = request.form.get(u'group_added')

        try:
            tk.check_access('package_update', context, pkg_dict)
        except tk.NotFound:
            tk.abort(404, _('Dataset not found'))
        except tk.NotAuthorized:
            tk.abort(403, _('User %r not authorized to manage themes'))

        if new_group:
            data_dict = {
                u"id": new_group,
                u"object": id,
                u"object_type": u'package',
                u"capacity": u'public'
            }
            try:
                tk.get_action(u'member_create')(dict(context, ignore_auth=True), data_dict)
            except tk.NotFound:
                return tk.abort(404, _(u'Group not found'))

        removed_group = None
        for param in request.form:
            if param.startswith(u'group_remove'):
                removed_group = param.split(u'.')[-1]
                break
        if removed_group:
            data_dict = {
                u"id": removed_group,
                u"object": id,
                u"object_type": u'package'
            }
            try:
                tk.get_action(u'member_delete')(dict(context, ignore_auth=True), data_dict)
            except tk.NotFound:
                return tk.abort(404, _(u'Group not found'))
        return tk.h.redirect_to(u'{}.groups'.format(package_type), id=id)

def reports_index():
    return h.redirect_to("fcscopendata.reports_read" )

def reports_read():
    page_number = h.get_page_number(request.args)
    limit = tk.request.args.get("limit", 8)
    q = tk.request.args.get('q', '')
    q_segments = q.split(' - ')
    if len(q_segments) == 2:
        start_date=q_segments[0]
        end_date=q_segments[1]
    else:
        start_date = tk.request.args.get('start_date', '')
        end_date = tk.request.args.get('end_date', '')
    q = '{} - {}'.format(start_date,end_date)
    data_requests = DataRequest.find_all({"page": page_number, "limit": limit},start_date=start_date, end_date=end_date, solved=False)
    count = DataRequest.find_all({}, is_count=True, start_date=start_date, end_date=end_date, solved=False)
    page = Page(
        collection=data_requests,
        page=page_number,
        presliced_list=True,
        url=h.pager_url,
        item_count=count,
        items_per_page=limit)
    return tk.render("reports/data-request.html", extra_vars={"data_requests": data_requests, "page": page, "q": q })

def analytics_read():
    page_number = h.get_page_number(request.args)
    limit = tk.request.args.get("limit", 8)
    q = tk.request.args.get('q', '')
    q_segments = q.split(' - ')
    if len(q_segments) == 2:
        start_date=q_segments[0]
        end_date=q_segments[1]
    else:
        start_date = tk.request.args.get('start_date', '')
        end_date = tk.request.args.get('end_date', '')
    q = '{} - {}'.format(start_date,end_date)
    analytics = Analytics.find_all({"page": page_number, "limit": limit},start_date=start_date, end_date=end_date)
    count = Analytics.find_all({}, is_count=True, start_date=start_date, end_date=end_date)
    page = Page(
        collection=analytics,
        page=page_number,
        presliced_list=True,
        url=h.pager_url,
        item_count=count,
        items_per_page=limit)
    return tk.render("reports/analytics.html", extra_vars={"analytics": analytics, "page": page, "q": q })

def reports_delete_confirm():
    id = tk.request.args.get("id", None)
    return tk.render("reports/confirm.html", extra_vars={"id":id})

def reports_delete(id = None):
    if not id:
        id = tk.request.args.get("id", None)
    try:
        DataRequest.delete(id) 
    except tk.NotFound:
        return tk.abort(404, _(u'Report not found'))
    return h.redirect_to("fcscopendata.reports_read", name="data-request" )

def reports_solve(id = None):
    if not id:
        id = tk.request.args.get("id", None)
    try:
        DataRequest.solve(id) 
    except tk.NotFound:
        return tk.abort(404, _(u'Report not found'))
    return h.redirect_to("fcscopendata.reports_read", name="data-request" )  
    
def generate_xlsx(data_requests):
    wb = Workbook()
    ws = wb.active
    ws.title = "Data Requests"

    headers = ["Email", "Topic", "Date Created", "Name", "Phone Number", "Message Content", "Resolution"]
    ws.append(headers)

    for data_request in data_requests:
        formatted_date = data_request.date_created.strftime("%Y-%m-%d") if isinstance(data_request.date_created, datetime) else data_request.date_created
        phone_number = str(data_request.phone_number) if data_request.phone_number else ""
        ws.append([
            data_request.email,
            data_request.topic,
            formatted_date,
            data_request.name,
            phone_number,
            data_request.message_content,
            "Resolved" if data_request.solved else "Not Resolved"
        ])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=data_requests.xlsx"}
    )
    
def generate_ga_xlsx(analytics):
    wb = Workbook()
    ws = wb.active
    ws.title = "Analytics Entries"

    headers = ["Resource ID", "Dataset ID", "Download Count", "Language", "Dataset Title", "Date Created"]
    ws.append(headers)

    for analytics_entry in analytics:
        formatted_date = analytics_entry.date_created.strftime("%Y-%m-%d") if isinstance(analytics_entry.date_created, datetime) else analytics_entry.date_created
        ws.append([
            analytics_entry.resource_id,
            analytics_entry.dataset_id,
            analytics_entry.count,
            analytics_entry.language,
            analytics_entry.dataset_title,
            formatted_date,
        ])

    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max_length + 2

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=analytics_entries.xlsx"}
    )

def requests_download():
    q = tk.request.args.get('q', '')
    q_segments = q.split(' - ')
    if len(q_segments) == 2:
        start_date=q_segments[0]
        end_date=q_segments[1]
    else:
        start_date = tk.request.args.get('start_date', '')
        end_date = tk.request.args.get('end_date', '')
    data_requests = DataRequest.find_all({"pagination": 0} , start_date=start_date, end_date=end_date)

    return generate_xlsx(data_requests)

def analytics_download():
    q = tk.request.args.get('q', '')
    q_segments = q.split(' - ')
    if len(q_segments) == 2:
        start_date=q_segments[0]
        end_date=q_segments[1]
    else:
        start_date = tk.request.args.get('start_date', '')
        end_date = tk.request.args.get('end_date', '')
    analytics = Analytics.find_all({"pagination": 0} , start_date=start_date, end_date=end_date)

    return generate_ga_xlsx(analytics)