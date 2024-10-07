import ckan.model as model
from ckan.common import _, g, request
import ckan.plugins.toolkit as tk
from ckan.views.api import _finish_ok
from ckan.views.dataset import GroupView
from ckanext.fcscopendata.models.data_request import DataRequest
import csv
from io import StringIO
from flask import Response

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

# TODO: implement index page or redirect to first report
def reports_index():
    pass
    # TODO: return base.redirect_to somewhere

# TODO: implement report read page
def reports_read(name):
    # TODO: conditionally return a different template render based on the name parameter
    # TODO: analytics
    if name == "data-request":
        # TODO
        # /reports/data-request?page=1&limit=20
        page = tk.request.args.get("page", 1)
        limit = tk.request.args.get("limit", 20)

        data_requests = DataRequest.find_all({"page": page, "limit": limit })
        return tk.render("reports/data-request.html", extra_vars={"data_requests": data_requests, "page": page})
    elif name == "analytics":
        # TODO
        pass

    pass
def reports_delete(id):
    try:
        DataRequest.delete(id)  # Call the delete method by ID
        tk.h.redirect_to(u'/reports/data-requests', view_func=reports_read)
    except Exception as e:
        tk.h.redirect_to(u'/reports/data-requests', view_func=reports_read)
    return tk.h.redirect_to(u'/reports/data-requests', view_func=reports_read)
    

def generate_csv(data_requests):
    """Helper function to generate CSV from data requests."""
    output = StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow(["Email", "Topic", "Date Created", "Phone Number", "Message Content", "Name"])

    # Write each data request to the CSV
    for data_request in data_requests:
        writer.writerow([
            data_request.email,
            data_request.topic,
            data_request.date_created,
            data_request.phone_number,
            data_request.message_content,
            data_request.name,
        ])

    # Move the cursor to the start of the file for reading
    output.seek(0)
    
    # Generate a Flask response with the correct headers for downloading
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=data_requests.csv"}
    )

def reports_download(name):
    if name == "data-request":
        page = tk.request.args.get("page", 1)
        limit = tk.request.args.get("limit", 1000)  # Optionally, allow more data for CSV

        # Fetch the data requests (you can reuse the find_all method)
        data_requests = DataRequest.find_all({"page": page, "limit": limit})

        # Generate and return the CSV response
        return generate_csv(data_requests)
