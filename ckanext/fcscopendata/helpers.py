import ckan.logic as logic
import ckan.model as model
import logging

log = logging.getLogger(__name__)
def get_package_download_stats(package_id):
    context = {'model': model, 'session': model.Session}
    stats = logic.get_action('package_show')(context, {'id': package_id})
    return stats['total_downloads']

def is_dataset_draft(package_id):
    context = {'model': model, 'session': model.Session}
    dataset = logic.get_action('package_show')(context, {'id': package_id})
    if dataset.get('publishing_status', '') == 'draft':
        return True
    else:
        return False