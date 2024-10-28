from ckan.plugins import toolkit as tk
from ckanext.googleanalytics.cli import bulk_import, get_ga4_data, get_ga_data, _resource_url_tag
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange
from google.analytics.data_v1beta.types import Dimension
from google.analytics.data_v1beta.types import Metric
from google.analytics.data_v1beta.types import RunReportRequest
import logging

PACKAGE_URL = "/dataset/"
log = logging.getLogger(__name__)

def get_analytics(credentials, start_date):
    """Parse data from Google Analytics API and store it
    in a local database
    """
    from .ga_auth import init_service, get_profile_id
    analytics_data = None
    try:
        if tk.config.get("googleanalytics.measurement_id"):
            service = BetaAnalyticsDataClient.from_service_account_file(credentials)
        else:
            service = init_service(credentials)
            profile_id = get_profile_id(service)     
    except TypeError as e:
        raise Exception("Unable to create a service: {0}".format(e))
    
    # if start_date:
    #     bulk_import(service, profile_id, start_date)
    else:
        if tk.config.get("googleanalytics.measurement_id"):
            analytics_data = get_ga4_data(service)
            log.info("Saved %s records from google" % len(analytics_data))
        else:
            query = "ga:pagePath=~%s,ga:pagePath=~%s" % (
                PACKAGE_URL,
                _resource_url_tag(),
            )
            analytics_data = get_ga_data(service, profile_id, query_filter=query)
            log.info("Saved %s records from google" % len(analytics_data))
    return analytics_data