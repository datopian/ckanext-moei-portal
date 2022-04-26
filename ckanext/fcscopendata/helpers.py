import ckan.logic as logic
import ckan.model as model
import logging

log = logging.getLogger(__name__)
def get_package_download_stats(package_id):
    context = {'model': model, 'session': model.Session}
    stats = logic.get_action('package_show')(context, {'id': package_id})
    return stats['total_downloads']