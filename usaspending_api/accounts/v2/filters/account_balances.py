import logging

from django.db.models import Case, CharField, OuterRef, Subquery, Sum, When, Value
from django.db.models.functions import Concat

from usaspending_api.accounts.helpers import start_and_end_dates_from_fyq
from usaspending_api.accounts.models import AppropriationAccountBalances
from usaspending_api.common.exceptions import InvalidParameterException
from usaspending_api.download.v2.download_column_historical_lookups import query_paths
from usaspending_api.references.models import ToptierAgency

logger = logging.getLogger(__name__)


def account_balances_filter(filters, account_level='treasury_account'):
    query_filters = {}

    # Filter by agency if necessary
    if filters.get('agency', False) and filters['agency'] != 'all':
        agency = ToptierAgency.objects.filter(toptier_agency_id=filters['agency']).first()
        if agency:
            query_filters['treasury_account_identifier__agency_id'] = agency.cgac_code
        else:
            raise InvalidParameterException('agency with that ID does not exist')

    # TODO: Filter by federal account
    # federal_account = filters.get('federal_account', False)
    # if federal_account:
    #     query_filters['treasury_account_identifier__federal_account__federal_account_code'] = federal_account

    # Filter by Fiscal Year and Quarter
    if filters.get('fy', False) and filters.get('quarter', False):
        start_date, end_date = start_and_end_dates_from_fyq(filters['fy'], filters['quarter'])
        query_filters['reporting_period_start'] = start_date
        query_filters['reporting_period_end'] = end_date
    else:
        raise InvalidParameterException('fy and quarter are required parameters')

    queryset = AppropriationAccountBalances.objects
    if account_level == 'treasury_account':
        # Derive treasury_account_symbol, allocation_transfer_agency_name, and agency_name
        ata_subquery = ToptierAgency.objects.filter(
            cgac_code=OuterRef('treasury_account_identifier__allocation_transfer_agency_id'))
        agency_name_subquery = ToptierAgency.objects.filter(
            cgac_code=OuterRef('treasury_account_identifier__agency_id'))
        queryset = queryset.annotate(
            treasury_account_symbol=Concat(
                'treasury_account_identifier__agency_id',
                Value('-'),
                Case(When(treasury_account_identifier__availability_type_code='X', then=Value('X')),
                     default=Concat('treasury_account_identifier__beginning_period_of_availability', Value('/'),
                                    'treasury_account_identifier__ending_period_of_availability'),
                     output_field=CharField()),
                Value('-'),
                'treasury_account_identifier__main_account_code',
                Value('-'),
                'treasury_account_identifier__sub_account_code',
                output_field=CharField()),
            allocation_transfer_agency_name=Subquery(ata_subquery.values('name')[:1]),
            agency_name=Subquery(agency_name_subquery.values('name')[:1]),
            federal_account_symbol=Concat('treasury_account_identifier__federal_account__agency_identifier', Value('-'),
                                          'treasury_account_identifier__federal_account__main_account_code')
        )

    elif account_level == 'federal_account':
        # Group by budget_function and budget_subfunction
        group_vals = ['treasury_account_identifier__budget_function_title',
                      'treasury_account_identifier__budget_subfunction_title']
        queryset = queryset.values(*group_vals)

        # Sum all the columns, excluding the ones we're grouping by
        q_path = query_paths['account_balances']
        summed_cols = {i: Sum(q_path['treasury_account'][i]) for i in q_path['federal_account'] if i not in group_vals}
        queryset = queryset.annotate(**summed_cols)

    else:
        raise InvalidParameterException('Invalid Parameter: account_level must be either "federal_account" or '
                                        '"treasury_account"')

    return queryset.filter(**query_filters)
